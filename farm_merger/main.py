from item_finder import ImageFinder
from screen_area_selector import ScreenAreaSelector
from merging_points_selector import MergingPointsSelector
import os
import time
import pyautogui
from pynput import keyboard
import numpy as np
import argparse
import math

# Set up argument parser
parser = argparse.ArgumentParser(description='Farm Merge Clicker')
parser.add_argument('--merge_count', type=int, default=5, help='Number of items to merge')
parser.add_argument('--resize_factor', type=float, help='Resize factor for image recognition (optional)')

args = parser.parse_args()

MERGE_COUNT = args.merge_count
resize_factor = args.resize_factor

print(f"Merge count threshold set to: {MERGE_COUNT}")
print(f"Resize factor set to: {resize_factor}")


def get_screen_area():
    print("-> Setup 1/4: Select the screen area.")
    selector = ScreenAreaSelector()
    return selector.get_coordinates()

def get_anchor_point():
    print("-> Setup 2/4: VISUAL ANCHOR. Click exactly where your Decoration SHOULD be (Target Point).")
    selector = MergingPointsSelector(1)
    pts = selector.get_points()
    return pts[0] if pts else None

def get_merge_points(count):
    print(f"-> Setup 3/4: Click {count} center points for the merging target slots.")
    selector = MergingPointsSelector(count)
    return selector.get_points()

def get_spawner_point():
    print("-> Setup 4/4: Click 1 point to set the Spawner Box location.")
    selector = MergingPointsSelector(1)
    pts = selector.get_points()
    return pts[0] if pts else None

def get_image_file_paths(folder_name='img'):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_folder = os.path.join(base_dir, folder_name)
    
    image_files = []
    if os.path.exists(img_folder):
        for filename in os.listdir(img_folder):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                # تجاهل صورة الزينة حتى لا يدمجها بالخطأ
                if 'anchor' not in filename.lower():
                    image_files.append(os.path.join(img_folder, filename))
        image_files.reverse()
    return image_files


if __name__ == "__main__":
    def on_press(key):
        if key == keyboard.Key.f1:
            print("F1 pressed. Stopping the program.")
            os._exit(0)

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    print("==================================")
    print("Press F1 at any time to stop the bot.")
    print("==================================")

    # مسار صورة الزينة
    base_dir = os.path.dirname(os.path.abspath(__file__))
    anchor_img_path = os.path.join(base_dir, 'img', 'anchor.png')
    
    if not os.path.exists(anchor_img_path):
        print("\n[ERROR] 'anchor.png' not found in 'img' folder!")
        print("Please save a screenshot of your decoration as 'anchor.png'.\n")
        os._exit(1)

    # 1. Setup Sequence
    screen_start_x, screen_start_y, screen_end_x, screen_end_y = get_screen_area()
    anchor_target = get_anchor_point()
    clicked_points = get_merge_points(MERGE_COUNT - 1)
    spawner_point = get_spawner_point()

    if not spawner_point or not clicked_points or not anchor_target:
        print("Setup was incomplete. Exiting.")
        os._exit(1)

    if resize_factor is None:
        resize_factor = ImageFinder.find_best_resize_factor((screen_start_x, screen_start_y, screen_end_x, screen_end_y))
    print(f"Using resize factor: {resize_factor}")

    image_files = get_image_file_paths()
        
    total_merges_pending = 0
    print("Bot is now running...")
    
    # حساب إحداثيات السحب للمحرك
    center_x = screen_start_x + (screen_end_x - screen_start_x) // 2
    bottom_y = screen_end_y - 100
    top_y = screen_start_y + 100

    while True:
# ==========================================================
        # 1. نظام التحقق من المرساة البصرية (Visual Anchor Check)
        # ==========================================================
        # 🌟 FIX: Force resize_factor=1.0 so it doesn't zoom your anchor 🌟
        anchor_locs, _ = ImageFinder.find_image_on_screen(
            anchor_img_path, screen_start_x, screen_start_y, screen_end_x, screen_end_y, resize_factor=1.0, threshold=0.60
        )
        
        if len(anchor_locs) > 0:
            # الزينة موجودة في الشاشة، هل هي في مكانها الصحيح؟
            curr_x, curr_y = anchor_locs[0]
            dist = math.hypot(curr_x - anchor_target[0], curr_y - anchor_target[1])
            
            if dist > 20: # إذا تحركت الشاشة قليلاً، أعدها بدقة
                print("Anchor is visible but shifted. Adjusting map...")
                pyautogui.moveTo(curr_x, curr_y)
                pyautogui.mouseDown()
                pyautogui.sleep(0.05)
                pyautogui.moveTo(anchor_target[0], anchor_target[1], duration=0.4)
                pyautogui.sleep(0.2) # Anti-inertia
                pyautogui.mouseUp()
                pyautogui.sleep(0.3)
        else:
            # الزينة ضائعة! تفعيل بروتوكول البحث
            print("Anchor lost! Initiating Search Protocol...")
            
            # أ. رمي الخريطة للأسفل (سحب سريع للأعلى) بقوة القصور الذاتي
            pyautogui.moveTo(center_x, bottom_y)
            pyautogui.mouseDown()
            pyautogui.moveTo(center_x, top_y, duration=0.15) 
            pyautogui.mouseUp() # بدون توقف للاستفادة من القصور الذاتي
            pyautogui.sleep(1)
            
            # ب. الزحف للأعلى ببطء والبحث
            for attempt in range(10):
                locs, _ = ImageFinder.find_image_on_screen(
                    anchor_img_path, screen_start_x, screen_start_y, screen_end_x, screen_end_y, resize_factor, threshold=0.75
                )
                if len(locs) > 0:
                    print("Anchor found! Re-centering...")
                    curr_x, curr_y = locs[0]
                    pyautogui.moveTo(curr_x, curr_y)
                    pyautogui.mouseDown()
                    pyautogui.sleep(0.05)
                    pyautogui.moveTo(anchor_target[0], anchor_target[1], duration=0.5)
                    pyautogui.sleep(0.2) # Anti-inertia
                    pyautogui.mouseUp()
                    pyautogui.sleep(0.5)
                    break
                else:
                    # سحب الخريطة للأعلى (سحب الفأرة للأسفل ببطء)
                    pyautogui.moveTo(center_x, top_y)
                    pyautogui.mouseDown()
                    pyautogui.sleep(0.05)
                    pyautogui.moveTo(center_x, bottom_y, duration=0.5)
                    pyautogui.sleep(0.2) # Anti-inertia 
                    pyautogui.mouseUp()
                    pyautogui.sleep(0.5)

        # ==========================================================
        # 2. نظام الدمج الأصلي
        # ==========================================================
        merges_this_cycle = 0
        for target_image in image_files:
            template_center_points, modified_screenshot = ImageFinder.find_image_on_screen(
                target_image, screen_start_x, screen_start_y, screen_end_x, screen_end_y, resize_factor
            )
            
            if len(template_center_points) != 0:
                print(f"Found {len(template_center_points)} for {os.path.basename(target_image)}")
                
            if len(template_center_points) > MERGE_COUNT - 1 and len(clicked_points) >= MERGE_COUNT - 1:
                merges_this_cycle += 1
                for i in range(MERGE_COUNT):
                    start_x, start_y = template_center_points[i]
                    end_x, end_y = clicked_points[i % (MERGE_COUNT - 1)]
                    
                    pyautogui.mouseUp()
                    pyautogui.moveTo(start_x, start_y)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(start_x + 3, start_y + 3, duration=0.05) # Micro-drag
                    pyautogui.sleep(0.05)
                    pyautogui.moveTo(end_x, end_y, duration=0.15)
                    pyautogui.mouseUp()
                    pyautogui.sleep(0.1) 
                
                print("Dragging operations completed.")

        # ==========================================================
        # 3. نظام التوليد (AFK)
        # ==========================================================
        if merges_this_cycle > 0:
            total_merges_pending += merges_this_cycle
        else:
            if total_merges_pending > 0:
                clicks_needed = total_merges_pending * 3
                print(f"Board cleared! Spawning {clicks_needed} new items...")
                
                pyautogui.mouseUp()
                for _ in range(clicks_needed):
                    pyautogui.moveTo(spawner_point[0], spawner_point[1])
                    pyautogui.mouseDown()
                    pyautogui.moveTo(spawner_point[0] + 2, spawner_point[1] + 2, duration=0.05) # Micro-drag
                    pyautogui.mouseUp()
                    pyautogui.sleep(0.1)  
                
                pyautogui.sleep(0.5)
                total_merges_pending = 0
                # بعد التوليد مباشرة، ستتحرك الكاميرا تلقائياً، 
                # وسيتكفل "نظام المرساة" في بداية الدورة التالية بإرجاعها بذكاء!
            else:
                print("Waiting for crops to grow...")
                time.sleep(2)