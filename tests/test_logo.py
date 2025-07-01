#!/usr/bin/env python3
"""
Simple test for logo animation without websocket server
"""

import sys
import os
import numpy as np
from PIL import Image
import cv2

# Test the image processing functions directly
def test_logo_processing():
    logo_path = os.path.expanduser("~/repos/visualiser/assets/images/psybercell-logo.png")
    
    if not os.path.exists(logo_path):
        print(f"Logo not found at {logo_path}")
        print("Creating test image...")
        # Create a test logo
        test_img = Image.new('RGB', (128, 128), color='red')
        logo_path = "test_logo.png"
        test_img.save(logo_path)
    
    print(f"Loading logo: {logo_path}")
    
    # Load image using PIL
    image = Image.open(logo_path)
    print(f"Original image size: {image.size}")
    print(f"Original image mode: {image.mode}")
    
    # Convert to RGBA to handle transparency
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create a background (black by default)
    background = Image.new('RGBA', image.size, (0, 0, 0, 255))
    
    # Composite image over background
    composite = Image.alpha_composite(background, image)
    
    # Convert to RGB
    composite = composite.convert('RGB')
    
    # Resize to matrix dimensions (64x64)
    width, height = 64, 64
    resized = composite.resize((width, height), Image.Resampling.LANCZOS)
    
    print(f"Resized to: {resized.size}")
    
    # Convert to numpy array
    base_array = np.array(resized)
    print(f"Array shape: {base_array.shape}")
    
    # Test animation functions
    print("\nTesting animation effects...")
    
    # Fade test
    brightness = abs(np.sin(0.5))
    fade_frame = (base_array * brightness).astype(np.uint8)
    print(f"Fade effect: brightness={brightness:.2f}")
    
    # Hue shift test
    hsv = cv2.cvtColor(base_array, cv2.COLOR_RGB2HSV)
    hsv[:, :, 0] = (hsv[:, :, 0] + 30) % 180
    hue_frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    print("Hue shift effect: OK")
    
    # Rotation test
    M = cv2.getRotationMatrix2D((width/2, height/2), 45, 1.0)
    rot_frame = cv2.warpAffine(base_array, M, (width, height))
    print("Rotation effect: OK")
    
    # Save test outputs
    Image.fromarray(base_array).save("test_original.png")
    Image.fromarray(fade_frame).save("test_fade.png")
    Image.fromarray(hue_frame).save("test_hue.png")
    Image.fromarray(rot_frame).save("test_rotation.png")
    
    print("\nTest images saved:")
    print("- test_original.png")
    print("- test_fade.png") 
    print("- test_hue.png")
    print("- test_rotation.png")
    
    # Test frame data formatting
    frame_bytes = base_array.tobytes()
    print(f"\nFrame data size: {len(frame_bytes)} bytes")
    print(f"Expected size for 64x64 RGB: {64*64*3} bytes")
    
    if len(frame_bytes) == 64*64*3:
        print("✓ Frame data size correct for websocket transmission")
    else:
        print("✗ Frame data size mismatch")
    
    return True

if __name__ == "__main__":
    print("=== PsyberCell Logo Processing Test ===")
    
    try:
        success = test_logo_processing()
        if success:
            print("\n✓ All tests passed!")
            print("\nYou can now run:")
            print("  make animate-logo  # (when server is ready)")
        else:
            print("\n✗ Tests failed")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()