
import pyautogui
import time
import random
import math

# Target coordinates
target_x = 920
target_y = 480

def generate_human_movement(start_x, start_y, end_x, end_y):
    bursts = []
    total_distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    direction_x = (end_x - start_x) / total_distance
    direction_y = (end_x - start_x) / total_distance
    num_bursts = random.randint(4, 6)
    current_x, current_y = start_x, start_y

    for burst in range(num_bursts):
        progress = (burst + 1) / num_bursts
        target_progress = progress + random.uniform(-0.1, 0.1)
        target_progress = max(0, min(1, target_progress))

        target_x_burst = start_x + (end_x - start_x) * target_progress
        target_y_burst = start_y + (end_y - start_y) * target_progress

        curve_offset = random.uniform(-20, 20) if burst < num_bursts - 1 else 0
        target_x_burst += curve_offset * direction_y
        target_y_burst += curve_offset * direction_x

        burst_duration = random.uniform(0.02, 0.05)
        burst_steps = max(2, int(burst_duration * 100))
        for step in range(burst_steps):
            step_progress = step / (burst_steps - 1)
            step_x = current_x + (target_x_burst - current_x) * step_progress
            step_y = current_y + (target_y_burst - current_y) * step_progress
            step_x += random.uniform(-1, 1)
            step_y += random.uniform(-1, 1)
            pyautogui.moveTo(int(step_x), int(step_y), duration=0)
            time.sleep(burst_duration / burst_steps)

        current_x, current_y = target_x_burst, target_y_burst

        if burst < num_bursts - 1:
            if burst == 1:
                time.sleep(random.uniform(0.4, 0.5))
            else:
                time.sleep(random.uniform(0.05, 0.2))

    for _ in range(3):
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        pyautogui.moveTo(end_x + offset_x, end_y + offset_y, duration=0)
        time.sleep(random.uniform(0.05, 0.1))

    pyautogui.moveTo(end_x, end_y, duration=0)

print("🧠 Starting Jon-style movement to Gmail icon...")
start_x, start_y = pyautogui.position()
generate_human_movement(start_x, start_y, target_x, target_y)
time.sleep(0.2)
pyautogui.click()
print("✅ Clicked Gmail icon with Jon's signature style.")
