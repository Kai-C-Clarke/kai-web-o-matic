
import cv2
import numpy as np
from PIL import Image
import os

# Grid setup
GRID_LEFT = 1023
GRID_TOP = 26
CELL_WIDTH = 85
CELL_HEIGHT = 130

def grid_to_coords(cell_id):
    col_letters = "ABCDEFGHIJKL"
    if len(cell_id) != 2 or cell_id[0] not in col_letters or not cell_id[1].isdigit():
        raise ValueError("Invalid cell ID. Use format like 'J2'.")

    col = col_letters.index(cell_id[0])
    row = int(cell_id[1]) - 1
    left = GRID_LEFT + col * CELL_WIDTH
    top = GRID_TOP + row * CELL_HEIGHT
    return (left, top, CELL_WIDTH, CELL_HEIGHT)

def match_reference(screenshot_path, reference_path, cell_id):
    # Load full screenshot
    image = cv2.imread(screenshot_path)
    if image is None:
        raise FileNotFoundError(f"Could not read screenshot: {screenshot_path}")

    # Load reference image
    ref = cv2.imread(reference_path)
    if ref is None:
        raise FileNotFoundError(f"Could not read reference image: {reference_path}")

    # Crop grid cell from screenshot
    left, top, w, h = grid_to_coords(cell_id)
    cell_img = image[top:top+h, left:left+w]

    # Perform template matching
    result = cv2.matchTemplate(cell_img, ref, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    threshold = 0.7
    if max_val >= threshold:
        match_top_left = (left + max_loc[0], top + max_loc[1])
        match_width, match_height = ref.shape[1], ref.shape[0]
        center_x = match_top_left[0] + match_width // 2
        center_y = match_top_left[1] + match_height // 2
        print(f"✅ Match found in cell {cell_id} at ({center_x}, {center_y}) with confidence {max_val:.2f}")
        return {
            "top": match_top_left[1],
            "left": match_top_left[0],
            "width": match_width,
            "height": match_height,
            "center_point": { "x": center_x, "y": center_y },
            "confidence": float(f"{max_val:.2f}")
        }
    else:
        print(f"❌ No confident match found in cell {cell_id} (max score {max_val:.2f})")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to full screenshot")
    parser.add_argument("--target", required=True, help="Name of reference image without extension")
    parser.add_argument("--cell", required=True, help="Grid cell (e.g. J2)")

    args = parser.parse_args()

    # Default ref image path
    ref_path = os.path.expanduser(f"~/Desktop/web_o_matic/kai_ui_refs/{args.target}.png")
    match_reference(args.image, ref_path, args.cell)
