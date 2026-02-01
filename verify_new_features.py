import os
import cv2
import numpy as np
from downmess_core import DownmessCore

def create_dummy_image(filename):
    # Create a simple 100x100 black image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Draw a white rectangle
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
    cv2.imwrite(filename, img)
    print(f"Created dummy image: {filename}")

def test_resize(core):
    print("Testing Resize...")
    input_img = "test_img.png"
    create_dummy_image(input_img)
    
    try:
        out = core.resize_image(input_img, 200, 200)
        img = cv2.imread(out)
        if img.shape[:2] == (200, 200):
            print(f"[PASS] Resize successful: {out} is 200x200")
        else:
            print(f"[FAIL] Resize failed. Dimensions: {img.shape[:2]}")
    except Exception as e:
        print(f"[FAIL] Resize error: {e}")

def test_upscale(core):
    print("\nTesting AI Upscale (EDSR x2)...")
    # Using a very small image to speed up
    input_img = "test_small.png"
    # Create 20x20 image
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    cv2.rectangle(img, (5, 5), (15, 15), (255, 0, 0), -1)
    cv2.imwrite(input_img, img)
    
    try:
        # This might trigger model download
        out = core.upscale_image_ai(input_img, model="edsr", scale=2)
        img = cv2.imread(out)
        # Expected: 40x40
        if img.shape[:2] == (40, 40):
            print(f"[PASS] Upscale successful: {out} is 40x40")
        else:
            print(f"[FAIL] Upscale failed. Dimensions: {img.shape[:2]}")
    except Exception as e:
        print(f"[FAIL] Upscale error: {e}")

def main():
    core = DownmessCore()
    
    if not os.path.exists("models"):
        os.makedirs("models")
        
    test_resize(core)
    # Uncomment to test upscale (might take time to download model)
    test_upscale(core)

if __name__ == "__main__":
    main()
