#!/usr/bin/env python3
"""
web_o_matic_precision.py

Purpose:
Zoned UI element detection and precision clicking with human-like motion simulation.
Integrates Jon's burst-and-pause movement pattern with Kai's precision targeting.
"""

import os
import pyautogui
import time
import random
import json
import cv2
import numpy as np
import math
from PIL import Image
from datetime import datetime

class WebOMatic_Precision:
    def __init__(self):
        # Use the script's directory instead of a separate kai_system folder
        self.base_dir = os.path.dirname(__file__)
        self.targets_config_path = os.path.join(os.path.dirname(__file__), "targets_zones.json")
        self.screenshot_path = os.path.join(self.base_dir, "current_screenshot.png")
        self.intent_path = os.path.join(self.base_dir, "kai_click_intent.json")
        
        # Load target zones configuration
        self.load_target_zones()
        
        # Grid configuration - Browser pane coordinates (base 1600x900)
        self.BASE_ANCHOR_LEFT = 1039  # Browser pane left edge  
        self.BASE_ANCHOR_TOP = 26     # Browser pane top edge
        self.BASE_GRID_WIDTH = 2047 - 1039   # Browser pane width (1008px)
        self.BASE_GRID_HEIGHT = 1066 - 26    # Browser pane height (1040px)
        self.GRID_COLUMNS = 12
        self.GRID_ROWS = 8
        
        # Will be set dynamically based on actual screenshot dimensions
        self.scale_factor = 1.0
        self.ANCHOR_LEFT = self.BASE_ANCHOR_LEFT
        self.ANCHOR_TOP = self.BASE_ANCHOR_TOP  
        self.GRID_WIDTH = self.BASE_GRID_WIDTH
        self.GRID_HEIGHT = self.BASE_GRID_HEIGHT

    def calculate_scale_factor(self, screenshot_width):
        """Calculate scale factor based on actual screenshot dimensions"""
        expected_width = 1600  # Expected logical resolution width
        self.scale_factor = screenshot_width / expected_width
        
        # Scale all grid coordinates
        self.ANCHOR_LEFT = int(self.BASE_ANCHOR_LEFT * self.scale_factor)
        self.ANCHOR_TOP = int(self.BASE_ANCHOR_TOP * self.scale_factor)
        self.GRID_WIDTH = int(self.BASE_GRID_WIDTH * self.scale_factor)
        self.GRID_HEIGHT = int(self.BASE_GRID_HEIGHT * self.scale_factor)
        
        print(f"🔧 Scale factor: {self.scale_factor:.2f}")
        print(f"🔧 Scaled coordinates: anchor=({self.ANCHOR_LEFT}, {self.ANCHOR_TOP}), size=({self.GRID_WIDTH}x{self.GRID_HEIGHT})")

    def load_target_zones(self):
        """Load target zones configuration"""
        try:
            with open(self.targets_config_path, "r") as f:
                self.TARGET_ZONES = json.load(f)
            print(f"✅ Loaded {len(self.TARGET_ZONES)} target zones")
        except FileNotFoundError:
            print(f"❌ targets_zones.json not found at {self.targets_config_path}")
            self.TARGET_ZONES = {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in targets_zones.json: {e}")
            self.TARGET_ZONES = {}

    def grid_to_pixel(self, grid_cell):
        """Convert grid cell (like 'B3') to pixel coordinates"""
        column_map = "ABCDEFGHIJKL"
        if len(grid_cell) != 2 or grid_cell[0] not in column_map:
            raise ValueError(f"Invalid grid cell: {grid_cell}")
        
        col = column_map.index(grid_cell[0])
        row = int(grid_cell[1]) - 1

        cell_width = self.GRID_WIDTH / self.GRID_COLUMNS
        cell_height = self.GRID_HEIGHT / self.GRID_ROWS

        left = int(self.ANCHOR_LEFT + col * cell_width)
        top = int(self.ANCHOR_TOP + row * cell_height)
        width = int(cell_width)
        height = int(cell_height)

        return (left, top, width, height)

    def get_zone_bounds(self, grid_zone):
        """Get pixel bounds for a zone defined by grid cells"""
        if len(grid_zone) != 2:
            raise ValueError("Zone must have exactly 2 grid cells (top-left, bottom-right)")
        
        top_left_cell, bottom_right_cell = grid_zone
        
        # Get bounds of both cells
        tl_left, tl_top, tl_width, tl_height = self.grid_to_pixel(top_left_cell)
        br_left, br_top, br_width, br_height = self.grid_to_pixel(bottom_right_cell)
        
        # Calculate zone bounds
        zone_left = tl_left
        zone_top = tl_top
        zone_width = (br_left + br_width) - tl_left
        zone_height = (br_top + br_height) - tl_top
        
        # Debug output
        print(f"🔍 Zone calculation debug:")
        print(f"   Top-left {top_left_cell}: ({tl_left}, {tl_top}, {tl_width}, {tl_height})")
        print(f"   Bottom-right {bottom_right_cell}: ({br_left}, {br_top}, {br_width}, {br_height})")
        print(f"   Final zone: ({zone_left}, {zone_top}, {zone_width}, {zone_height})")
        
        return (zone_left, zone_top, zone_width, zone_height)

    def load_and_crop_zone(self, image_path, grid_zone):
        """Load image and crop to specified zone"""
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Debug: Show actual screenshot dimensions
        img_height, img_width = img.shape[:2]
        print(f"🖼️ Screenshot dimensions: {img_width}x{img_height} pixels")

        left, top, width, height = self.get_zone_bounds(grid_zone)
        print(f"🎯 Requested crop: ({left}, {top}) with size {width}x{height}")
        
        # Ensure bounds are within image (OpenCV uses [height, width] format!)
        left = max(0, min(left, img_width))
        top = max(0, min(top, img_height))
        right = max(left, min(left + width, img_width))
        bottom = max(top, min(top + height, img_height))
        
        print(f"🔧 Adjusted bounds: left={left}, top={top}, right={right}, bottom={bottom}")
        
        cropped = img[top:bottom, left:right]
        print(f"🔍 Cropped zone {grid_zone} to {cropped.shape[1]}x{cropped.shape[0]} pixels (WxH)")
        return cropped, (left, top)

    def find_best_match_in_zone(self, image_path, ref_image_path, grid_zone, confidence_threshold=0.75):
        """Find best template match within specified zone"""
        try:
            # Load and crop zone using scaled coordinates for image analysis
            zone_img, zone_offset = self.load_and_crop_zone(image_path, grid_zone)
            
            # Load reference template
            template = cv2.imread(ref_image_path)
            if template is None:
                print(f"❌ Reference template not found: {ref_image_path}")
                return None

            # Perform template matching
            result = cv2.matchTemplate(zone_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            print(f"🎯 Template match confidence: {max_val:.3f} (threshold: {confidence_threshold})")

            if max_val < confidence_threshold:
                print(f"⚠️ Low match confidence: {max_val:.3f} < {confidence_threshold}")
                return None

            # Calculate absolute screen coordinates
            template_height, template_width = template.shape[:2]
            zone_left, zone_top = zone_offset
            
            # Convert back to logical coordinates for mouse movement
            absolute_x = zone_left + max_loc[0] + (template_width // 2)
            absolute_y = zone_top + max_loc[1] + (template_height // 2)
            match_result = {
                "center_x": int(absolute_x),
                "center_y": int(absolute_y),
                "center_y": int(logical_y),
                "confidence": float(max_val),
                "template_size": (template_width, template_height),
                "zone": grid_zone
            }
            
            print(f"✅ Found match at logical coordinates ({int(logical_x)}, {int(logical_y)}) with confidence {max_val:.3f}")
            return match_result

        except Exception as e:
            print(f"❌ Template matching failed: {e}")
            return None

    def find_target(self, target_name, screenshot_path=None):
        """Find target using zoned search with fallback expansion"""
        if target_name not in self.TARGET_ZONES:
            print(f"❌ Unknown target: {target_name}")
            return None

        target_config = self.TARGET_ZONES[target_name]
        grid_zone = target_config["grid_zone"]
        ref_image_path = target_config.get("ref_image")
        
        if not ref_image_path:
            print(f"❌ No reference image configured for {target_name}")
            return None

        # Use provided screenshot or default - FIXED: actually use the provided screenshot!
        if screenshot_path is None:
            screenshot_path = self.screenshot_path
            print(f"🔍 Using default screenshot: {screenshot_path}")
        else:
            print(f"🔍 Using fresh screenshot: {screenshot_path}")

        if not os.path.exists(screenshot_path):
            print(f"❌ Screenshot not found: {screenshot_path}")
            return None

        # Construct full path to reference image
        ref_full_path = os.path.join(os.path.dirname(__file__), "kai_ui_refs", ref_image_path)
        
        if not os.path.exists(ref_full_path):
            print(f"❌ Reference image not found: {ref_full_path}")
            return None

        print(f"🎯 Searching for {target_name} in zone {grid_zone}")
        
        # Primary search in specified zone
        match = self.find_best_match_in_zone(screenshot_path, ref_full_path, grid_zone)
        
        if match:
            return match

        # TODO: Fallback search in expanded zones if needed
        print(f"⚠️ {target_name} not found in primary zone {grid_zone}")
        return None

    def generate_human_movement_bursts(self, start_x, start_y, end_x, end_y):
        """Generate Jon's realistic human movement bursts"""
        movement_bursts = []
        
        # Calculate total distance and direction
        total_distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        if total_distance == 0:
            return movement_bursts
            
        direction_x = (end_x - start_x) / total_distance
        direction_y = (end_y - start_y) / total_distance
        
        # Jon's pattern: 4-5 movement bursts with settling between
        num_bursts = random.randint(4, 6)
        current_x, current_y = start_x, start_y
        
        for burst in range(num_bursts):
            # Calculate progress (how far along the path we should be)
            progress = (burst + 1) / num_bursts
            
            # Target for this burst (with some randomness)
            target_progress = progress + random.uniform(-0.1, 0.1)
            target_progress = max(0, min(1, target_progress))  # Keep in bounds
            
            target_x = start_x + (end_x - start_x) * target_progress
            target_y = start_y + (end_y - start_y) * target_progress
            
            # Add curve and randomness to target
            curve_offset = random.uniform(-20, 20) if burst < num_bursts - 1 else 0
            target_x += curve_offset * direction_y  # Perpendicular to main direction
            target_y += curve_offset * direction_x
            
            # Movement burst (20-50ms like Jon's pattern)
            burst_duration = random.uniform(0.02, 0.05)
            burst_steps = max(2, int(burst_duration * 100))  # Steps within burst
            
            burst_movements = []
            for step in range(burst_steps):
                step_progress = step / (burst_steps - 1)
                step_x = current_x + (target_x - current_x) * step_progress
                step_y = current_y + (target_y - current_y) * step_progress
                
                # Add micro-tremor
                step_x += random.uniform(-1, 1)
                step_y += random.uniform(-1, 1)
                
                burst_movements.append({
                    'x': int(step_x),
                    'y': int(step_y),
                    'delay': burst_duration / burst_steps
                })
            
            movement_bursts.append({
                'type': 'movement',
                'movements': burst_movements,
                'duration': burst_duration
            })
            
            # Update current position
            current_x, current_y = target_x, target_y
            
            # Settling pause (50-460ms like Jon's pattern)
            if burst < num_bursts - 1:  # Don't pause after final burst
                if burst == 1:  # Longer pause like Jon's 460ms pause
                    pause_duration = random.uniform(0.4, 0.5)
                else:  # Shorter pauses
                    pause_duration = random.uniform(0.05, 0.2)
                
                movement_bursts.append({
                    'type': 'pause',
                    'duration': pause_duration,
                    'position': (int(current_x), int(current_y))
                })
        
        return movement_bursts

    def execute_human_movement(self, target_x, target_y):
        """Execute Jon's burst-and-pause movement pattern"""
        print(f"🎯 Moving to ({target_x}, {target_y}) using Jon's movement signature")
        
        # Get current position
        current_x, current_y = pyautogui.position()
        
        # Calculate distance
        distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
        
        if distance < 10:
            print("🎯 Already very close to target, adding micro-adjustments...")
            # Just do micro-settling
            for _ in range(2):
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                pyautogui.moveTo(target_x + offset_x, target_y + offset_y, duration=0)
                time.sleep(random.uniform(0.05, 0.15))
            pyautogui.moveTo(target_x, target_y, duration=0)
            return

        # Generate and execute movement bursts
        bursts = self.generate_human_movement_bursts(current_x, current_y, target_x, target_y)
        
        print(f"🚀 Executing {len(bursts)} movement bursts/pauses")
        
        total_time = 0
        for i, burst in enumerate(bursts):
            if burst['type'] == 'movement':
                print(f"   📍 Burst {i+1}: {len(burst['movements'])} micro-movements over {burst['duration']*1000:.0f}ms")
                
                # Execute rapid micro-movements
                for movement in burst['movements']:
                    pyautogui.moveTo(movement['x'], movement['y'], duration=0)
                    time.sleep(movement['delay'])
                
                total_time += burst['duration']
                
            elif burst['type'] == 'pause':
                print(f"   ⏸️  Pause {i+1}: {burst['duration']*1000:.0f}ms at ({burst['position'][0]}, {burst['position'][1]})")
                
                # Stay at position during pause (crucial for browser detection)
                pyautogui.moveTo(burst['position'][0], burst['position'][1], duration=0)
                time.sleep(burst['duration'])
                
                total_time += burst['duration']
        
        # Final positioning with micro-settling
        print("🎯 Final micro-settling...")
        for _ in range(3):
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            pyautogui.moveTo(target_x + offset_x, target_y + offset_y, duration=0)
            time.sleep(random.uniform(0.05, 0.1))
        
        # Final exact position
        pyautogui.moveTo(target_x, target_y, duration=0)
        
        print(f"✅ Movement complete in {total_time:.3f}s")

    def take_fresh_screenshot(self):
        """Take a new screenshot on current desktop"""
        print("📸 Taking fresh screenshot...")
        screenshot = pyautogui.screenshot()
        screenshot.save(self.screenshot_path)
        print(f"✅ Screenshot saved: {self.screenshot_path}")
        
        # Check actual dimensions and calculate scale factor
        img = cv2.imread(self.screenshot_path)
        if img is not None:
            h, w = img.shape[:2]
            print(f"📏 New screenshot dimensions: {w}x{h} pixels")
            # Calculate scale factor based on actual screenshot width
            self.calculate_scale_factor(w)
        return self.screenshot_path

    def precision_click(self, target_name, screenshot_path=None):
        """Main function: find target and click with human movement"""
        print(f"\n🎯 PRECISION CLICK: {target_name}")
        print("=" * 50)
        
        # Switch to desktop 1 first (removed duplicate - only switch once)
        self.switch_to_desktop_1()
        
        # Take fresh screenshot on desktop 1
        fresh_screenshot = self.take_fresh_screenshot()
        
        # Find the target using fresh screenshot
        match = self.find_target(target_name, fresh_screenshot)
        if not match:
            print(f"❌ Could not locate {target_name}")
            return False

        center_x = match["center_x"]
        center_y = match["center_y"]
        confidence = match["confidence"]
        
        print(f"🎯 Target found at ({center_x}, {center_y}) with {confidence:.3f} confidence")
        
        # Execute human-like movement and click
        self.execute_human_movement(center_x, center_y)
        
        # Click with slight delay after settling
        time.sleep(random.uniform(0.2, 0.4))
        pyautogui.click(button='left', clicks=1, interval=0.25)
        
        print(f"✅ Precision click executed on {target_name}")
        
        # Create intent JSON for compatibility
        intent_data = {
            "intent": f"Precision click on {target_name}",
            "target": target_name,
            "coordinates": {
                "center_x": center_x,
                "center_y": center_y
            },
            "confidence": confidence,
            "zone": match["zone"],
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.intent_path, 'w') as f:
            json.dump(intent_data, f, indent=2)
        
        return True

    def switch_to_desktop_1(self):
        """Switch to desktop 1 by pressing Control + Right arrow"""
        print("🖥️ Switching to desktop 1...")
        try:
            import subprocess
            subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to key code 124 using control down'
            ], check=True)
            time.sleep(1.0)  # Give time for desktop switch
            print("✅ Switched to desktop 1 (via Control + Right)")
            return True
        except (subprocess.CalledProcessError, ImportError) as e:
            print(f"⚠️ Desktop switching failed: {e}")
            return False

    def activate_browser_window(self):
        """Activate browser window and ensure it's in focus"""
        print("🌐 Activating browser window...")
        
        # Desktop switching is now handled in precision_click() - don't switch here
        
        try:
            import subprocess
            subprocess.run([
                "osascript", "-e",
                'tell application "Google Chrome" to activate'
            ], check=True)
            time.sleep(0.5)
            print("✅ Chrome activated via AppleScript")
        except (subprocess.CalledProcessError, ImportError):
            print("⚠️  AppleScript activation failed")
        
        # Fallback: Click in browser area
        browser_center_x = self.ANCHOR_LEFT + (self.GRID_WIDTH // 2)
        browser_center_y = self.ANCHOR_TOP + (self.GRID_HEIGHT // 2)
        
        pyautogui.moveTo(browser_center_x, browser_center_y, duration=0.3)
        time.sleep(0.2)
        pyautogui.click()
        time.sleep(0.5)
        print("✅ Browser window focused")

def main():
    """Main function for testing"""
    precision = WebOMatic_Precision()
    
    print("🧠 Web-O-Matic Precision System")
    print("=" * 40)
    print("Available targets:")
    for target_name in precision.TARGET_ZONES.keys():
        print(f"  - {target_name}")
    
    while True:
        print("\nCommands:")
        print("1. click <target_name> - Precision click on target")
        print("2. activate - Activate browser window")
        print("3. quit - Exit")
        
        cmd = input("\nEnter command: ").strip().lower()
        
        if cmd.startswith("click "):
            target = cmd[6:].strip()
            # Make target matching case-insensitive
            target_match = None
            for zone_name in precision.TARGET_ZONES.keys():
                if zone_name.lower() == target.lower():
                    target_match = zone_name
                    break
            
            if target_match:
                precision.activate_browser_window()
                time.sleep(0.5)
                precision.precision_click(target_match)
            else:
                print(f"❌ Unknown target: {target}")
                
        elif cmd == "activate":
            precision.activate_browser_window()
            
        elif cmd == "quit":
            break
            
        else:
            print("❌ Invalid command")

if __name__ == "__main__":
    print("🧠 web_o_matic_precision initialized. Ready for input.")
    main()