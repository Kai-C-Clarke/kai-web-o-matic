
import pyautogui
import time

# Corrected Gmail icon center coordinates
logical_x = 920
logical_y = 480

print(f"🧭 Moving to Gmail icon at ({logical_x}, {logical_y})...")
time.sleep(1.0)

pyautogui.moveTo(logical_x, logical_y, duration=0.4)
pyautogui.click()

print("✅ Clicked Gmail icon successfully.")
