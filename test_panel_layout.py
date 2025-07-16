#!/usr/bin/env python3
"""
Test panel layout and orientation for 3x2 matrix configuration
Expected layout:
[3] ← [2] ← [1] (Row A: right to left)
 ↓
[4] → [5] → [6] (Row B: left to right)
"""

import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
from simple_tcp_client import SimpleVideoStreamClient
import argparse

def create_directional_arrows(width, height, panel_width=64, panel_height=32):
    """Create arrows showing data flow direction"""
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    
    # Panel layout with arrows
    # Row 1: 3 ← 2 ← 1
    # Row 2: 4 → 5 → 6
    
    # Draw arrows between panels
    arrow_color = (255, 255, 255)
    
    # Row 1 arrows (right to left)
    for i in range(2):
        x = (i + 1) * panel_width + panel_width // 2
        y = panel_height // 2
        # Draw arrow pointing left
        draw.line([(x - 20, y), (x + 20, y)], fill=arrow_color, width=3)
        draw.polygon([(x - 20, y), (x - 10, y - 5), (x - 10, y + 5)], fill=arrow_color)
    
    # Vertical arrow from panel 3 to 4
    x = 2 * panel_width + panel_width // 2
    y = panel_height
    draw.line([(x, y - 20), (x, y + 20)], fill=arrow_color, width=3)
    draw.polygon([(x, y + 20), (x - 5, y + 10), (x + 5, y + 10)], fill=arrow_color)
    
    # Row 2 arrows (left to right)
    for i in range(2):
        x = i * panel_width + panel_width // 2
        y = panel_height + panel_height // 2
        # Draw arrow pointing right
        draw.line([(x - 20, y), (x + 20, y)], fill=arrow_color, width=3)
        draw.polygon([(x + 20, y), (x + 10, y - 5), (x + 10, y + 5)], fill=arrow_color)
    
    return np.array(img)

def create_coordinate_test(width, height):
    """Create a test pattern with coordinates"""
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    
    # Draw grid every 16 pixels
    grid_color = (40, 40, 40)
    for x in range(0, width, 16):
        draw.line([(x, 0), (x, height)], fill=grid_color)
    for y in range(0, height, 16):
        draw.line([(0, y), (width, y)], fill=grid_color)
    
    # Draw coordinate markers at key positions
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except:
        font = ImageFont.load_default()
    
    # Mark corners of each panel
    panel_positions = [
        (0, 0, "1:TL"),           # Panel 1 top-left
        (63, 0, "1:TR"),          # Panel 1 top-right
        (64, 0, "2:TL"),          # Panel 2 top-left
        (127, 0, "2:TR"),         # Panel 2 top-right
        (128, 0, "3:TL"),         # Panel 3 top-left
        (191, 0, "3:TR"),         # Panel 3 top-right
        (0, 32, "4:TL"),          # Panel 4 top-left
        (63, 32, "4:TR"),         # Panel 4 top-right
        (64, 32, "5:TL"),         # Panel 5 top-left
        (127, 32, "5:TR"),        # Panel 5 top-right
        (128, 32, "6:TL"),        # Panel 6 top-left
        (191, 32, "6:TR"),        # Panel 6 top-right
    ]
    
    for x, y, label in panel_positions:
        # Draw a bright marker
        draw.rectangle([x-2, y-2, x+2, y+2], fill=(255, 255, 0))
        # Draw label
        draw.text((x+5, y), label, fill=(255, 255, 0), font=font)
    
    return np.array(img)

def create_panel_test_with_corners(width, height, panel_width=64, panel_height=32):
    """Create test pattern with distinct corners for each panel"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    panels_x = width // panel_width
    panels_y = height // panel_height
    
    # Expected physical layout:
    # [3] [2] [1]
    # [4] [5] [6]
    
    # But logical layout might be different due to serpentine
    panel_colors = {
        1: (255, 0, 0),     # Red
        2: (0, 255, 0),     # Green
        3: (0, 0, 255),     # Blue
        4: (255, 255, 0),   # Yellow
        5: (255, 0, 255),   # Magenta
        6: (0, 255, 255),   # Cyan
    }
    
    # Physical positions for 3x2 serpentine (where we expect panels to be)
    # Layout: 3 ← 2 ← 1 ← Pi
    #         4 → 5 → 6
    physical_positions = {
        1: (2, 0),  # Top-right (first from Pi)
        2: (1, 0),  # Top-middle (second from Pi)
        3: (0, 0),  # Top-left (third from Pi)
        4: (0, 1),  # Bottom-left (fourth, serpentine continues)
        5: (1, 1),  # Bottom-middle (fifth)
        6: (2, 1),  # Bottom-right (sixth)
    }
    
    for panel_num, (px, py) in physical_positions.items():
        x = px * panel_width
        y = py * panel_height
        color = panel_colors[panel_num]
        
        # Draw panel outline
        img[y:y+2, x:x+panel_width] = color
        img[y+panel_height-2:y+panel_height, x:x+panel_width] = color
        img[y:y+panel_height, x:x+2] = color
        img[y:y+panel_height, x+panel_width-2:x+panel_width] = color
        
        # Draw panel number in center
        cx = x + panel_width // 2
        cy = y + panel_height // 2
        
        # Create a large number
        size = 10
        img[cy-size:cy+size, cx-size:cx+size] = color
        
        # Add corner markers
        # Top-left: solid square
        img[y:y+8, x:x+8] = color
        
        # Top-right: horizontal lines
        for i in range(0, 8, 2):
            img[y+i, x+panel_width-8:x+panel_width] = color
            
        # Bottom-left: vertical lines
        for i in range(0, 8, 2):
            img[y+panel_height-8:y+panel_height, x+i] = color
            
        # Bottom-right: checkerboard
        for i in range(0, 8, 2):
            for j in range(0, 8, 2):
                img[y+panel_height-8+i, x+panel_width-8+j] = color
    
    return img

def main():
    parser = argparse.ArgumentParser(description='Test panel layout and orientation')
    parser.add_argument('--host', default='localhost', help='Server hostname/IP')
    parser.add_argument('--port', type=int, default=9002, help='Server port')
    parser.add_argument('--test', choices=['arrows', 'coords', 'corners', 'sequence'], default='corners',
                        help='Test pattern type')
    args = parser.parse_args()
    
    # Connect to server
    client = SimpleVideoStreamClient(args.host, args.port)
    try:
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        print(f"📐 Expected layout:")
        print("   [3] ← [2] ← [1] (Row A: right to left)")
        print("    ↓")
        print("   [4] → [5] → [6] (Row B: left to right)")
        
        if args.test == 'arrows':
            print("➡️ Showing data flow arrows...")
            frame = create_directional_arrows(client.matrix_width, client.matrix_height)
            client.send_frame(frame)
            
        elif args.test == 'coords':
            print("📍 Showing coordinate grid...")
            frame = create_coordinate_test(client.matrix_width, client.matrix_height)
            client.send_frame(frame)
            
        elif args.test == 'corners':
            print("🔲 Showing panel corners and numbers...")
            frame = create_panel_test_with_corners(client.matrix_width, client.matrix_height)
            client.send_frame(frame)
            
        elif args.test == 'sequence':
            print("🔢 Showing panel sequence...")
            # Light up panels in sequence
            for panel_num in range(1, 7):
                print(f"Panel {panel_num} (physical position)")
                frame = np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
                print(f"Matrix dimensions: {client.matrix_width}x{client.matrix_height}")
                
                # Physical positions
                physical_positions = {
                    1: (2, 0),  # Top-right
                    2: (1, 0),  # Top-middle
                    3: (0, 0),  # Top-left
                    4: (0, 1),  # Bottom-left
                    5: (1, 1),  # Bottom-middle
                    6: (2, 1),  # Bottom-right
                }
                
                px, py = physical_positions[panel_num]
                x = px * 64
                y = py * 32
                
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
                color = colors[panel_num - 1]
                
                frame[y:y+32, x:x+64] = color
                client.send_frame(frame)
                time.sleep(1)
        
        print("✅ Test complete! Press Ctrl+C to exit")
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clear display
        if client.matrix_height and client.matrix_width:
            client.send_frame(np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8))
        client.disconnect()

if __name__ == "__main__":
    main()