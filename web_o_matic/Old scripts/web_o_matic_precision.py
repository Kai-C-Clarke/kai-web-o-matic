"""
web_o_matic_precision.py

Purpose:
Zoned UI element detection and precision clicking with human-like motion simulation.
"""

import os
import pyautogui
import time
import random
import json
from PIL import Image

# Load grid zones and reference targets
with open("targets_zones.json", "r") as f:
    TARGET_ZONES = json.load(f)

def grid_to_pixel(grid_cell):
    column_map = "ABCDEFGHIJKL"
    col = column_map.index(grid_cell[0])
    row = int(grid_cell[1]) - 1

    anchor_left, anchor_top = 1039, 26
    grid_width = 2047 - 1039
    grid_height = 1066 - 26

    cell_width = grid_width / 12
    cell_height = grid_height / 8

    left = int(anchor_left + col * cell_width)
    top = int(anchor_top + row * cell_height)
    width = int(cell_width)
    height = int(cell_height)

    return (left, top, width, height)

def glide_and_jitter_click(x, y):
    pyautogui.moveTo(x - 40, y - 40, duration=random.uniform(0.4, 0.7))
    for _ in range(random.randint(3, 5)):
        pyautogui.moveTo(
            x + random.randint(-3, 3),
            y + random.randint(-3, 3),
            duration=random.uniform(0.05, 0.15)
        )
        time.sleep(random.uniform(0.05, 0.15))
    pyautogui.moveTo(x, y, duration=0.1)
    time.sleep(random.uniform(0.3, 0.5))
    pyautogui.click()

# TODO: Load screenshot, crop zone, match template, call glide_and_jitter_click()

print("🧠 web_o_matic_precision initialized. Ready for input.")
