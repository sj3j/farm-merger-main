import json
import math
from pynput import keyboard, mouse
import os

class NativeDragRecorder:
    def __init__(self):
        self.drags = []
        self.current_start = None
        self.recording = True

        print("\n" + "="*50)
        print("-> DRAG RECORDER (Map Reset)")
        print("1. Go to your game window.")
        print("2. Click and drag the map as many times as needed to reset it.")
        print("   (The game will respond normally so you can see the changes).")
        print("3. Press the 'SPACEBAR' when you are completely finished.")
        print("="*50 + "\n")

        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.keyboard_listener.join()
        self.mouse_listener.stop()

    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return False
        
        if pressed:
            self.current_start = (x, y)
        else:
            if self.current_start:
                # Calculate distance to ignore tiny accidental clicks
                dist = math.hypot(x - self.current_start[0], y - self.current_start[1])
                if dist > 10:
                    self.drags.append((self.current_start, (x, y)))
                    print(f"   [+] Recorded Drag {len(self.drags)}")
                self.current_start = None

    def on_press(self, key):
        if key == keyboard.Key.space:
            print("   -> Finished recording map reset drags.\n")
            self.recording = False
            return False 

    def save_to_file(self, filename="dragreset.json"):
        with open(filename, 'w') as f:
            json.dump(self.drags, f)
        print(f"Saved {len(self.drags)} drags to {filename}")

if __name__ == "__main__":
    recorder = NativeDragRecorder()
    recorder.save_to_file()