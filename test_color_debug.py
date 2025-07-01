#!/usr/bin/env python3
"""
Test to debug color issues by sending simple test patterns
"""

import sys
import os
import numpy as np
from PIL import Image
import time

sys.path.append("/home/jamie/repos/rpi-rgb-led-matrix/Adafruit_Blinka_Raspberry_Pi5_Piomatter")
from simple_tcp_client import SimpleVideoStreamClient

def test_basic_colors():
    """Test with basic solid colors"""
    client = SimpleVideoStreamClient("localhost", 9002)
    
    try:
        client.connect()
        print(f"Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        # Test 1: Solid colors with debug output
        test_colors = [
            ("Black", [0, 0, 0]),
            ("Pure Red", [255, 0, 0]),
            ("Pure Green", [0, 255, 0]),
            ("Pure Blue", [0, 0, 255]),
            ("White", [255, 255, 255]),
            ("Yellow", [255, 255, 0]),
            ("Cyan", [0, 255, 255]),
            ("Magenta", [255, 0, 255]),
            ("Gray", [128, 128, 128]),
        ]
        
        for name, color in test_colors:
            print(f"\n=== Testing {name}: RGB{color} ===")
            frame = np.full((client.matrix_height, client.matrix_width, 3), color, dtype=np.uint8)
            
            # Debug: Check what we're sending
            print(f"Frame shape: {frame.shape}")
            print(f"Frame dtype: {frame.dtype}")
            sample_pixel = frame[client.matrix_height//2, client.matrix_width//2]
            print(f"Center pixel being sent: RGB{tuple(sample_pixel)}")
            
            success = client.send_frame(frame)
            print(f"Send result: {success}")
            
            input(f"Check matrix display for {name}. Press Enter to continue...")
        
        # Test 2: Logo with extra debug
        print("\n=== Testing Logo ===")
        logo_path = os.path.expanduser("~/repos/visualiser/assets/images/psybercell-logo.png")
        
        if os.path.exists(logo_path):
            # Load exactly like the client
            image = Image.open(logo_path)
            print(f"Logo loaded: mode={image.mode}, size={image.size}")
            
            # Convert to RGBA
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
                print("Converted to RGBA")
            
            # Create black background
            background = Image.new('RGBA', image.size, (0, 0, 0, 255))
            
            # Composite
            composite = Image.alpha_composite(background, image)
            
            # Convert to RGB
            composite = composite.convert('RGB')
            
            # Resize to matrix size
            resized = composite.resize(
                (client.matrix_width, client.matrix_height),
                Image.Resampling.LANCZOS
            )
            
            # Convert to numpy
            frame = np.array(resized)
            print(f"Resized logo shape: {frame.shape}")
            print(f"Resized logo dtype: {frame.dtype}")
            print(f"Value range: {frame.min()}-{frame.max()}")
            
            # Sample multiple pixels
            h, w = frame.shape[:2]
            print("\nSample pixels from logo:")
            for i in range(5):
                y = int(i * h / 5)
                x = int(i * w / 5)
                pixel = frame[y, x]
                print(f"  ({x:3d}, {y:3d}): RGB{tuple(pixel)}")
            
            # Check center pixel
            center_pixel = frame[h//2, w//2]
            print(f"\nCenter pixel: RGB{tuple(center_pixel)}")
            
            # Send to matrix
            print("\nSending logo to matrix...")
            success = client.send_frame(frame)
            print(f"Send result: {success}")
            
            input("Check the logo display. Press Enter to continue...")
        else:
            print(f"Logo not found at {logo_path}")
        
        client.disconnect()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Color Debug Test")
    print("=" * 40)
    print("1. Start the debug server:")
    print("   sudo ./src/build_simple/simple_server")
    print("2. Watch the server console for debug output")
    print("=" * 40)
    input("Press Enter when server is ready...")
    
    test_basic_colors()