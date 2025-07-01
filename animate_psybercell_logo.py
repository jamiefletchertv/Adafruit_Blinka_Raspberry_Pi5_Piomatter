#!/usr/bin/env python3
"""
Simple script to animate the PsyberCell logo using the existing Adafruit library
"""

import time
import math
import numpy as np
from PIL import Image, ImageEnhance
import os
import sys

# Add the src directory to the path
sys.path.insert(0, '/home/jamie/repos/rpi-rgb-led-matrix/Adafruit_Blinka_Raspberry_Pi5_Piomatter/src')

import adafruit_blinka_raspberry_pi5_piomatter as piomatter

# Configuration
LOGO_PATH = os.path.expanduser("~/repos/visualiser/assets/images/psybercell-logo.png")
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64

def load_and_resize_logo():
    """Load and resize the logo to fit the matrix"""
    if not os.path.exists(LOGO_PATH):
        print(f"Error: Logo not found at {LOGO_PATH}")
        # Create a simple test image
        img = Image.new('RGB', (MATRIX_WIDTH, MATRIX_HEIGHT), color='red')
        return img
    
    # Load the logo
    logo = Image.open(LOGO_PATH)
    
    # Convert to RGB if needed
    if logo.mode != 'RGB':
        logo = logo.convert('RGB')
    
    # Resize to matrix dimensions
    logo = logo.resize((MATRIX_WIDTH, MATRIX_HEIGHT), Image.Resampling.LANCZOS)
    
    return logo

def animate_logo():
    """Animate the logo with various effects"""
    # Load the logo
    base_logo = load_and_resize_logo()
    base_array = np.array(base_logo)
    
    # Initialize the matrix (following the example pattern)
    geometry = piomatter.Geometry(width=MATRIX_WIDTH, height=MATRIX_HEIGHT, 
                                  n_addr_lines=4, rotation=piomatter.Orientation.Normal)
    
    print("Starting logo animation...")
    print("Press Ctrl+C to stop")
    
    try:
        frame_count = 0
        while True:
            # Cycle through different animations every 3 seconds (90 frames at 30fps)
            animation_type = (frame_count // 90) % 4
            t = (frame_count % 90) / 90.0  # 0 to 1 for each animation cycle
            
            if animation_type == 0:
                # Fade in/out
                brightness = abs(math.sin(t * math.pi * 2))
                frame = (base_array * brightness).astype(np.uint8)
                print(f"Fade animation: brightness={brightness:.2f}")
                
            elif animation_type == 1:
                # Color cycling (hue shift)
                # Convert to HSV, shift hue, convert back
                hsv_img = Image.fromarray(base_array).convert('HSV')
                hsv_array = np.array(hsv_img)
                hue_shift = int(t * 255)
                hsv_array[:, :, 0] = (hsv_array[:, :, 0] + hue_shift) % 256
                frame = np.array(Image.fromarray(hsv_array, 'HSV').convert('RGB'))
                print(f"Hue shift animation: shift={hue_shift}")
                
            elif animation_type == 2:
                # Brightness pulse
                enhancer = ImageEnhance.Brightness(Image.fromarray(base_array))
                brightness = 0.3 + 0.7 * abs(math.sin(t * math.pi * 4))
                frame = np.array(enhancer.enhance(brightness))
                print(f"Brightness pulse: level={brightness:.2f}")
                
            else:
                # Static display with different colors
                frame = base_array.copy()
                print("Static display")
            
            # Create matrix with current frame
            matrix = piomatter.PioMatter(colorspace=piomatter.Colorspace.RGB888Packed,
                                       pinout=piomatter.Pinout.AdafruitMatrixBonnet,
                                       framebuffer=frame,
                                       geometry=geometry)
            matrix.show()
            
            frame_count += 1
            time.sleep(1.0)  # 1 FPS for testing
            
            # Exit after a few cycles for testing
            if frame_count > 20:
                break
            
    except KeyboardInterrupt:
        print("\nStopping animation...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    animate_logo()