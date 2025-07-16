#!/usr/bin/env python3
"""
Simple test to see current panel configuration
"""

import numpy as np
from PIL import Image, ImageDraw

import adafruit_blinka_raspberry_pi5_piomatter as piomatter

def create_simple_test():
    """Create a simple test pattern"""
    # Test with a single panel first
    img = Image.new('RGB', (64, 32), 'black')
    draw = ImageDraw.Draw(img)
    
    # Draw a red square in top-left
    draw.rectangle([0, 0, 16, 16], fill=(255, 0, 0))
    
    # Draw a green square in top-right  
    draw.rectangle([48, 0, 64, 16], fill=(0, 255, 0))
    
    # Draw a blue square in bottom-left
    draw.rectangle([0, 16, 16, 32], fill=(0, 0, 255))
    
    # Draw a yellow square in bottom-right
    draw.rectangle([48, 16, 64, 32], fill=(255, 255, 0))
    
    return np.array(img)

print("Testing single 64x32 panel...")

geometry = piomatter.Geometry(
    width=64,
    height=32,
    n_addr_lines=4,
    n_planes=10,
    n_temporal_planes=0,
    rotation=piomatter.Orientation.Normal
)

framebuffer = create_simple_test()

matrix = piomatter.PioMatter(
    colorspace=piomatter.Colorspace.RGB888Packed,
    pinout=piomatter.Pinout.AdafruitMatrixBonnet,
    framebuffer=framebuffer,
    geometry=geometry
)

print("✅ Single panel test - should show colored squares")
matrix.show()

input("Press Enter to continue to 3x2 test...")

# Now test 3x2 without serpentine first
print("\nTesting 3x2 layout without serpentine...")

geometry_3x2 = piomatter.Geometry(
    width=192,
    height=64,
    n_addr_lines=4,
    n_planes=10,
    n_temporal_planes=0,
    rotation=piomatter.Orientation.Normal,
    serpentine=False
)

# Create 3x2 test pattern
img_3x2 = Image.new('RGB', (192, 64), 'black')
draw_3x2 = ImageDraw.Draw(img_3x2)

# Draw different colors in each 64x32 section
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
for i in range(6):
    x = (i % 3) * 64
    y = (i // 3) * 32
    draw_3x2.rectangle([x, y, x + 64, y + 32], fill=colors[i])
    
    # Draw panel number
    draw_3x2.text((x + 30, y + 14), str(i + 1), fill=(255, 255, 255))

framebuffer_3x2 = np.array(img_3x2)

matrix_3x2 = piomatter.PioMatter(
    colorspace=piomatter.Colorspace.RGB888Packed,
    pinout=piomatter.Pinout.AdafruitMatrixBonnet,
    framebuffer=framebuffer_3x2,
    geometry=geometry_3x2
)

print("✅ 3x2 test without serpentine")
matrix_3x2.show()

input("Press Enter to test with serpentine...")

# Test with serpentine
print("\nTesting 3x2 layout WITH serpentine...")

geometry_3x2_serpentine = piomatter.Geometry(
    width=192,
    height=64,
    n_addr_lines=4,
    n_planes=10,
    n_temporal_planes=0,
    rotation=piomatter.Orientation.Normal,
    serpentine=True
)

matrix_3x2_serpentine = piomatter.PioMatter(
    colorspace=piomatter.Colorspace.RGB888Packed,
    pinout=piomatter.Pinout.AdafruitMatrixBonnet,
    framebuffer=framebuffer_3x2,
    geometry=geometry_3x2_serpentine
)

print("✅ 3x2 test WITH serpentine")
matrix_3x2_serpentine.show()

input("Press Enter to exit...")