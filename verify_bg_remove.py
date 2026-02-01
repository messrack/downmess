import os
import cv2
import numpy as np
from downmess_core import DownmessCore

def create_circle_image(filename):
    # Create an image with a white circle on black background
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(img, (100, 100), 50, (255, 255, 255), -1)
    cv2.imwrite(filename, img)
    print(f"Created test image: {filename}")

def test_bg_remove(core):
    print("Testing Background Removal...")
    input_img = "test_circle.png"
    create_circle_image(input_img)
    
    try:
        # First run might download model
        out = core.remove_background(input_img)
        
        if os.path.exists(out):
            img = cv2.imread(out, cv2.IMREAD_UNCHANGED)
            # Check if it has alpha channel
            if img.shape[2] == 4:
                print(f"[PASS] Background removal successful. Output has alpha channel: {out}")
            else:
                print(f"[FAIL] Output processed but lacks alpha channel.")
        else:
            print(f"[FAIL] Output file not found.")
            
    except Exception as e:
        print(f"[FAIL] Background removal error: {e}")

def main():
    core = DownmessCore()
    test_bg_remove(core)

if __name__ == "__main__":
    main()
