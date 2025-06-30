#!/usr/bin/env python3
"""
Kai Complete Navigation System - FIXED SEND BUTTON VERSION
- Single image paste, 4-second delay for send button state
- Uses Enter key for send button instead of coordinate clicking
- Uses OCR to capture Kai's responses automatically
"""

import subprocess
import time
import pyautogui
import os
import json
import threading
import re
from datetime import datetime
import shutil
from PIL import Image
import pytesseract
import pyperclip

class KaiNavigationSystem:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Desktop/kai_system")
        self.ensure_directory()
        
        # File paths
        self.screenshot_path = os.path.join(self.base_dir, "current_screenshot.png")
        self.kai_read_path = os.path.join(self.base_dir, "kai_ui_read.png")
        self.intent_path = os.path.join(self.base_dir, "kai_click_intent.json")
        
        # Grid configuration for Desktop 1 Chrome area
        self.PANE_LEFT = 1023
        self.PANE_TOP = 26
        self.PANE_WIDTH = 1024
        self.PANE_HEIGHT = 1046
        self.GRID_COLUMNS = 12
        self.GRID_ROWS = 8
        
        # Kai UI coordinates (Desktop 0, left side)  
        self.KAI_INPUT_X = 300
        self.KAI_INPUT_Y = 970
        self.KAI_SEND_X = 860  # Base coordinates - will be overridden
        self.KAI_SEND_Y = 1033
        
        self.grid_window = None
        self.watching_clicks = False

    def ensure_directory(self):
        """Create the kai_system directory if it doesn't exist"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            print(f"📁 Created directory: {self.base_dir}")

    def switch_to_desktop_1(self):
        """Switch to Desktop 1"""
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to key code 124 using control down'
        ])
        print("🖥  Switched to Desktop 1")
        time.sleep(2)

    def switch_to_desktop_0(self):
        """Switch to Desktop 0"""
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to key code 123 using control down'
        ])
        print("🖥  Switched to Desktop 0")
        time.sleep(1)

    def create_grid_overlay(self):
        """No physical grid needed - Kai will use imaginary grid"""
        print("📐 Using Kai's imaginary grid system")
        time.sleep(1)

    def capture_screenshot(self):
        """Capture screenshot of Desktop 1 Chrome area"""
        region = (self.PANE_LEFT, self.PANE_TOP, self.PANE_WIDTH, self.PANE_HEIGHT)
        screenshot = pyautogui.screenshot(region=region)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_path = os.path.join(self.base_dir, f"screenshot_{timestamp}.png")
        
        screenshot.save(timestamped_path)
        screenshot.save(self.screenshot_path)
        shutil.copyfile(self.screenshot_path, self.kai_read_path)
        
        print(f"📸 Screenshot captured and saved")
        return self.kai_read_path

    def copy_to_clipboard(self, image_path):
        """Copy image to clipboard using AppleScript"""
        applescript = f'''
        set imgFile to POSIX file "{image_path}" as alias
        set the clipboard to (read imgFile as JPEG picture)
        '''
        result = subprocess.run(["osascript", "-e", applescript], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Image copied to clipboard")
        else:
            print(f"⚠️  Clipboard error: {result.stderr}")

    def send_to_kai(self, image_path):
        """Send screenshot and prompt to Kai's UI with wake-up sequence"""
        print("📨 Sending wake-up call to Kai...")
        
        # Step 1: Send wake-up prompt first
        pyautogui.moveTo(self.KAI_INPUT_X, self.KAI_INPUT_Y)
        pyautogui.click()
        time.sleep(0.5)
        
        wake_up_prompt = "Kai, prepare to analyze image – standby for screenshot"
        pyautogui.typewrite(wake_up_prompt)
        time.sleep(1)
        
        # Send wake-up message using Enter key
        print("⌨️ Sending wake-up message with Enter key...")
        pyautogui.press('enter')
        
        print("📨 Wake-up call sent, waiting 3 seconds...")
        time.sleep(3)
        
        # Step 2: Copy image to clipboard and send with analysis prompt
        self.copy_to_clipboard(image_path)
        
        # Click in input area
        pyautogui.moveTo(self.KAI_INPUT_X, self.KAI_INPUT_Y)
        pyautogui.click()
        time.sleep(1)
        
        # Paste image ONCE only
        print("📋 Pasting image once...")
        pyautogui.hotkey('command', 'v')
        time.sleep(3)  # Wait for image to appear and expand inbox
        
        # Add formal prompt with proper line break
        prompt = "12x8 grid analyze click_region"
        follow_up = "Kai, please respond with click_region(...) and JSON intent."
        
        print(f"📝 Sending prompt: '{prompt}'")
        print(f"📝 Follow-up: '{follow_up}'")
        
        pyautogui.typewrite(prompt)
        pyautogui.hotkey('shift', 'enter')  # Force line break
        pyautogui.typewrite(follow_up)
        time.sleep(1)
        
        # FIXED: Click expanded input area then use Enter key
        print("⏳ Waiting for send button to become ready (orange/bold)...")
        time.sleep(4)  # Wait for UI state change
        print("🖱️ Clicking expanded input area to ensure focus...")
        pyautogui.moveTo(886, 970)  # Expanded input coordinates
        pyautogui.click()
        time.sleep(0.5)
        print("⌨️ SENDING MESSAGE WITH ENTER KEY...")
        try:
            pyautogui.press('enter')
            print("✅ MESSAGE SENT WITH ENTER KEY!")
            time.sleep(1)
        except Exception as e:
            print(f"❌ ERROR SENDING MESSAGE: {e}")
        
        print("📨 Screenshot and analysis prompt sent to Kai")

    def parse_kai_response_to_json(self, response_text):
        """Parse Kai's click_region response and create JSON file"""
        pattern = r'click_region\(top=(\d+),\s*left=(\d+),\s*width=(\d+),\s*height=(\d+)\)'
        match = re.search(pattern, response_text)
        
        if match:
            top, left, width, height = map(int, match.groups())
            center_x = left + width // 2
            center_y = top + height // 2
            
            intent_data = {
                "intent": "Auto-parsed click from Kai",
                "grid_cell": "Auto",
                "coordinates": {
                    "top": top,
                    "left": left, 
                    "width": width,
                    "height": height
                },
                "center_point": {
                    "x": center_x,
                    "y": center_y
                },
                "confidence": 0.94,
                "safety_status": "green",
                "requires_confirmation": False,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.intent_path, 'w') as f:
                json.dump(intent_data, f, indent=2)
            
            print(f"✅ Parsed coordinates: ({center_x}, {center_y})")
            return True
        else:
            print("❌ Could not parse click_region from response")
            return False

    def capture_kai_response(self):
        """Capture Kai's latest response using OCR system"""
        kai_config = {
            "ocr_scan_region": (159, 206, 867, 300),
            "full_response_bounds": (159, 206, 867, 915),
        }
        
        print("📖 Capturing Kai's response with OCR...")
        time.sleep(3)
        
        try:
            screenshot = pyautogui.screenshot(region=kai_config["ocr_scan_region"])
            response_text = pytesseract.image_to_string(screenshot)
            
            if len(response_text.strip()) > 20:
                full_bounds = kai_config["full_response_bounds"]
                
                pyautogui.moveTo(full_bounds[0], full_bounds[1])
                time.sleep(0.3)
                pyautogui.dragTo(full_bounds[2], full_bounds[3], duration=1, button='left')
                time.sleep(0.5)
                pyautogui.hotkey('command', 'c')
                time.sleep(1)
                
                full_response = pyperclip.paste()
                print(f"✅ Captured response: {full_response[:100]}...")
                return full_response
            else:
                print("❌ No substantial response found")
                return None
                
        except Exception as e:
            print(f"❌ OCR capture failed: {e}")
            return None

    def take_screenshot_with_grid(self):
        """Main function: capture screenshot and send to Kai"""
        print("🚀 Starting Kai Navigation System...")
        
        # Clear old JSON files
        if os.path.exists(self.intent_path):
            os.remove(self.intent_path)
            print("🗑️ Cleared old JSON file")
        
        self.switch_to_desktop_1()
        
        print("📐 No physical grid - Kai will use imaginary grid system...")
        self.create_grid_overlay()
        
        print("📸 Capturing screenshot...")
        image_path = self.capture_screenshot()
        
        print("📨 Sending to Kai...")
        self.send_to_kai(image_path)
        
        print("⏳ Waiting for Kai's response...")
        time.sleep(10)
        
        response = self.capture_kai_response()
        if response and self.parse_kai_response_to_json(response):
            print("✅ Response parsed and JSON created for click watcher")
        else:
            print("❌ Failed to parse Kai's response")
        
        return image_path

    def watch_for_click_intents(self):
        """Watch for click intent files and execute safe clicks"""
        last_timestamp = ""
        print(f"👀 Watching for click intents in {self.intent_path}")
        
        self.watching_clicks = True
        while self.watching_clicks:
            if os.path.exists(self.intent_path):
                try:
                    with open(self.intent_path, 'r') as f:
                        data = json.load(f)
                    
                    timestamp = data.get('timestamp', '')
                    if timestamp != last_timestamp:
                        last_timestamp = timestamp
                        
                        intent = data.get('intent', 'Unknown')
                        safety = data.get('safety_status', 'unknown')
                        confirm = data.get('requires_confirmation', True)
                        
                        center = data.get('center_point', {})
                        
                        if center:
                            x, y = center.get('x'), center.get('y')
                        else:
                            print("⚠️  No valid coordinates found")
                            continue
                        
                        print(f"\n🧠 Intent: {intent}")
                        print(f"📍 Target: ({x}, {y})")
                        print(f"🛡️  Safety: {safety}")
                        
                        if safety == "green" and not confirm:
                            print("✅ Safe click - executing automatically")
                            time.sleep(1)
                            pyautogui.moveTo(x, y)
                            time.sleep(1)
                            pyautogui.click()
                            print("🖱️  Click executed")
                        else:
                            print("⏳ Requires manual confirmation - not clicking")
                            
                except Exception as e:
                    print(f"❌ Error reading intent: {e}")
            
            time.sleep(2)

    def start_click_watcher(self):
        """Start the click watcher in a separate thread"""
        threading.Thread(target=self.watch_for_click_intents, daemon=True).start()

    def stop_click_watcher(self):
        """Stop watching for clicks"""
        self.watching_clicks = False

def main():
    kai = KaiNavigationSystem()
    
    print("Kai Complete Navigation System - FIXED SEND BUTTON VERSION")
    print("=========================================================")
    print("1. Take screenshot with grid")
    print("2. Start click watcher")
    print("3. Both (recommended)")
    print("4. Quit")
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            kai.take_screenshot_with_grid()
            
        elif choice == "2":
            kai.start_click_watcher()
            print("Click watcher started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                kai.stop_click_watcher()
                print("\nClick watcher stopped.")
                
        elif choice == "3":
            kai.start_click_watcher()
            time.sleep(2)
            kai.take_screenshot_with_grid()
            print("System running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                kai.stop_click_watcher()
                print("\nSystem stopped.")
                
        elif choice == "4":
            kai.stop_click_watcher()
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()