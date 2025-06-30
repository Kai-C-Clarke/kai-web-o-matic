#!/usr/bin/env python3
"""
Human Mouse Movement Analyzer
Records real human mouse movements to understand natural patterns
"""

import pyautogui
import time
import json
import threading
from datetime import datetime

class MouseMovementAnalyzer:
    def __init__(self):
        self.recording = False
        self.movements = []
        self.start_time = None
        
    def start_recording(self, duration=10):
        """Record mouse movements for specified duration"""
        print(f"🎬 Starting mouse movement recording for {duration} seconds...")
        print("📍 Move your mouse naturally to Gmail icon and click it")
        print("⏰ Recording will start in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("🔴 RECORDING NOW! Move naturally to Gmail and click!")
        
        self.recording = True
        self.movements = []
        self.start_time = time.time()
        
        # Record movements
        end_time = time.time() + duration
        while time.time() < end_time and self.recording:
            current_time = time.time()
            x, y = pyautogui.position()
            
            movement_data = {
                "timestamp": current_time - self.start_time,
                "x": x,
                "y": y,
                "relative_time": current_time - self.start_time
            }
            
            self.movements.append(movement_data)
            time.sleep(0.01)  # 100Hz sampling rate
        
        self.recording = False
        print("🛑 Recording stopped!")
        return self.movements
    
    def analyze_movements(self):
        """Analyze recorded movement patterns"""
        if not self.movements:
            print("❌ No movements recorded")
            return
        
        print("\n📊 MOVEMENT ANALYSIS")
        print("=" * 50)
        
        # Basic stats
        total_points = len(self.movements)
        duration = self.movements[-1]["timestamp"]
        
        print(f"📈 Total data points: {total_points}")
        print(f"⏱️  Total duration: {duration:.2f} seconds")
        print(f"📊 Sample rate: {total_points/duration:.1f} Hz")
        
        # Calculate velocities and accelerations
        velocities = []
        accelerations = []
        
        for i in range(1, len(self.movements)):
            prev = self.movements[i-1]
            curr = self.movements[i]
            
            dt = curr["timestamp"] - prev["timestamp"]
            if dt > 0:
                dx = curr["x"] - prev["x"]
                dy = curr["y"] - prev["y"]
                distance = (dx**2 + dy**2)**0.5
                velocity = distance / dt
                velocities.append(velocity)
                
                if len(velocities) > 1:
                    dv = velocities[-1] - velocities[-2]
                    acceleration = dv / dt
                    accelerations.append(acceleration)
        
        if velocities:
            avg_velocity = sum(velocities) / len(velocities)
            max_velocity = max(velocities)
            print(f"🚀 Average velocity: {avg_velocity:.1f} pixels/sec")
            print(f"⚡ Peak velocity: {max_velocity:.1f} pixels/sec")
        
        # Movement phases analysis
        self.analyze_movement_phases()
        
        # Save data for later analysis
        filename = f"mouse_movement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "movements": self.movements,
                "analysis": {
                    "total_points": total_points,
                    "duration": duration,
                    "avg_velocity": avg_velocity if velocities else 0,
                    "max_velocity": max_velocity if velocities else 0
                }
            }, f, indent=2)
        
        print(f"💾 Data saved to: {filename}")
        
    def analyze_movement_phases(self):
        """Identify different phases of movement"""
        if len(self.movements) < 10:
            return
            
        print("\n🎯 MOVEMENT PHASES")
        print("-" * 30)
        
        # Find periods of rapid movement vs settling
        velocities = []
        for i in range(1, len(self.movements)):
            prev = self.movements[i-1]
            curr = self.movements[i]
            dt = curr["timestamp"] - prev["timestamp"]
            if dt > 0:
                dx = curr["x"] - prev["x"]
                dy = curr["y"] - prev["y"]
                distance = (dx**2 + dy**2)**0.5
                velocity = distance / dt
                velocities.append((curr["timestamp"], velocity))
        
        if not velocities:
            return
            
        # Find movement phases
        avg_velocity = sum(v[1] for v in velocities) / len(velocities)
        threshold = avg_velocity * 0.3  # 30% of average = "settled"
        
        phases = []
        current_phase = None
        
        for timestamp, velocity in velocities:
            if velocity > threshold:
                if current_phase != "moving":
                    phases.append(("moving", timestamp))
                    current_phase = "moving"
            else:
                if current_phase != "settled":
                    phases.append(("settled", timestamp))
                    current_phase = "settled"
        
        for phase_type, timestamp in phases[:10]:  # Show first 10 phases
            print(f"   {timestamp:.2f}s: {phase_type}")
            
    def generate_human_movement_function(self, target_x, target_y):
        """Generate a movement function based on recorded patterns"""
        if not self.movements:
            print("❌ No movement data to analyze")
            return None
            
        # This would generate movement commands based on learned patterns
        print(f"\n🧬 GENERATING HUMAN-LIKE MOVEMENT TO ({target_x}, {target_y})")
        
        # Extract movement characteristics
        total_duration = self.movements[-1]["timestamp"]
        start_x, start_y = self.movements[0]["x"], self.movements[0]["y"]
        end_x, end_y = self.movements[-1]["x"], self.movements[-1]["y"]
        
        print(f"📍 Original movement: ({start_x}, {start_y}) → ({end_x}, {end_y})")
        print(f"⏱️  Duration: {total_duration:.2f} seconds")
        
        # Generate movement commands (simplified example)
        movement_commands = []
        for i, movement in enumerate(self.movements[::5]):  # Subsample
            progress = i / (len(self.movements[::5]) - 1)
            # Map to new target
            new_x = start_x + (target_x - start_x) * progress
            new_y = start_y + (target_y - start_y) * progress
            
            movement_commands.append({
                "x": int(new_x),
                "y": int(new_y),
                "delay": movement["timestamp"] / total_duration
            })
            
        return movement_commands

def main():
    analyzer = MouseMovementAnalyzer()
    
    print("Human Mouse Movement Analyzer")
    print("=" * 40)
    print("1. Record mouse movement")
    print("2. Analyze last recording")
    print("3. Generate movement pattern")
    print("4. Quit")
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            duration = input("Recording duration (seconds, default 10): ").strip()
            duration = int(duration) if duration.isdigit() else 10
            movements = analyzer.start_recording(duration)
            analyzer.analyze_movements()
            
        elif choice == "2":
            analyzer.analyze_movements()
            
        elif choice == "3":
            if analyzer.movements:
                target_x = int(input("Target X coordinate: "))
                target_y = int(input("Target Y coordinate: "))
                commands = analyzer.generate_human_movement_function(target_x, target_y)
                if commands:
                    print(f"Generated {len(commands)} movement commands")
            else:
                print("❌ No movement data recorded yet")
                
        elif choice == "4":
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()