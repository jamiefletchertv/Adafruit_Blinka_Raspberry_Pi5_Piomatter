#!/usr/bin/env python3
"""
Test 3x2 serpentine configuration for 6x 64x32 panels

Physical wiring:
[1] → [2] → [3] (connected to Pi)
[6] ← [5] ← [4]

This creates a 192x64 display from 6 panels in serpentine configuration.
"""

import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

import adafruit_blinka_raspberry_pi5_piomatter as piomatter

def create_test_pattern(width, height):
    """Create a test pattern showing panel numbers and data flow"""
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Panel colors
    panel_colors = [
        (255, 100, 100),  # Panel 1 - Red
        (100, 255, 100),  # Panel 2 - Green
        (100, 100, 255),  # Panel 3 - Blue
        (255, 255, 100),  # Panel 4 - Yellow
        (255, 100, 255),  # Panel 5 - Magenta
        (100, 255, 255),  # Panel 6 - Cyan
    ]
    
    # Draw panels with numbers
    # Corrected mapping to match actual front view
    # Panel 1 = top-left, Panel 4 = bottom-right, Panel 6 = bottom-left
    # Top row: 1, 2, 3 (left to right)
    # Bottom row: 6, 5, 4 (left to right)
    panel_positions = {
        1: (0, 0),  # Top-left
        2: (1, 0),  # Top-middle
        3: (2, 0),  # Top-right
        4: (2, 1),  # Bottom-right (serpentine continues from panel 3)
        5: (1, 1),  # Bottom-middle
        6: (0, 1),  # Bottom-left
    }
    
    for panel_num in range(1, 7):
        px, py = panel_positions[panel_num]
        
        x = px * 64
        y = (1 - py) * 32  # Invert y-coordinate to swap rows
        color = panel_colors[panel_num - 1]
        
        # Fill panel with color
        draw.rectangle([x, y, x + 64, y + 32], fill=color)
        
        # Draw panel number
        text = str(panel_num)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x + (64 - text_width) // 2
        text_y = y + (32 - text_height) // 2
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
        
        # Draw corner markers
        draw.rectangle([x, y, x + 4, y + 4], fill=(255, 255, 255))  # Top-left
        draw.rectangle([x + 60, y, x + 64, y + 4], fill=(255, 255, 255))  # Top-right
        draw.rectangle([x, y + 28, x + 4, y + 32], fill=(255, 255, 255))  # Bottom-left
        draw.rectangle([x + 60, y + 28, x + 64, y + 32], fill=(255, 255, 255))  # Bottom-right
    
    # Draw arrows showing data flow
    arrow_color = (255, 255, 255)
    
    # Top row arrows (right to left): 1 ← 2 ← 3
    for i in range(2):
        x = (2 - i) * 64 - 10  # Between panels
        y = 16  # Middle of top row
        draw.line([(x - 10, y), (x + 10, y)], fill=arrow_color, width=2)
        draw.polygon([(x - 10, y), (x - 5, y - 3), (x - 5, y + 3)], fill=arrow_color)
    
    # Vertical connection from panel 3 to panel 4
    draw.line([(160, 32), (160, 40)], fill=arrow_color, width=2)
    draw.polygon([(160, 40), (157, 35), (163, 35)], fill=arrow_color)
    
    # Bottom row arrows (left to right): 4 → 5 → 6
    for i in range(2):
        x = i * 64 + 64 + 10  # Between panels
        y = 48  # Middle of bottom row
        draw.line([(x - 10, y), (x + 10, y)], fill=arrow_color, width=2)
        draw.polygon([(x + 10, y), (x + 5, y - 3), (x + 5, y + 3)], fill=arrow_color)
    
    return np.array(img)

def main():
    print("🔧 Testing 3x2 serpentine configuration...")
    print("Physical wiring:")
    print("   [1] → [2] → [3] (connected to Pi)")
    print("   [6] ← [5] ← [4]")
    
    # Create geometry for 3x2 serpentine (192x64 total)
    # Each panel is 64x32, so 3 panels wide = 192, 2 panels tall = 64
    geometry = piomatter.Geometry(
        width=192,
        height=64,
        n_addr_lines=4,  # For 64x32 panels
        n_planes=10,
        n_temporal_planes=0,
        rotation=piomatter.Orientation.Normal,
        serpentine=True  # Enable serpentine to match wiring
    )
    
    # Create test pattern
    framebuffer = create_test_pattern(192, 64)
    
    # Initialize matrix with serpentine enabled
    matrix = piomatter.PioMatter(
        colorspace=piomatter.Colorspace.RGB888Packed,
        pinout=piomatter.Pinout.AdafruitMatrixBonnet,
        framebuffer=framebuffer,
        geometry=geometry
    )
    
    print("✅ Matrix initialized. Displaying test pattern...")
    matrix.show()
    
    print("🔍 Check your display:")
    print("- Panel 1 (red) should be top-left")
    print("- Panel 2 (green) should be top-middle") 
    print("- Panel 3 (blue) should be top-right")
    print("- Panel 4 (yellow) should be bottom-right")
    print("- Panel 5 (magenta) should be bottom-middle")
    print("- Panel 6 (cyan) should be bottom-left")
    print()
    print("Corrected mapping: 1,2,3 (top), 6,5,4 (bottom)")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()