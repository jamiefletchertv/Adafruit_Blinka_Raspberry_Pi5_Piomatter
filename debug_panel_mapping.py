#!/usr/bin/env python3
"""
Debug panel mapping to understand exact layout
"""

import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
from simple_tcp_client import SimpleVideoStreamClient
import argparse

def create_numbered_grid(width, height):
    """Create a grid showing exact pixel coordinates"""
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
    except:
        font = ImageFont.load_default()
    
    # Draw grid lines every 8 pixels
    for x in range(0, width, 8):
        draw.line([(x, 0), (x, height)], fill=(40, 40, 40))
    for y in range(0, height, 8):
        draw.line([(0, y), (width, y)], fill=(40, 40, 40))
    
    # Number each 64x32 section
    for panel_y in range(0, height, 32):
        for panel_x in range(0, width, 64):
            # Calculate panel number based on position
            px = panel_x // 64
            py = panel_y // 32
            panel_num = py * 3 + px + 1
            
            # Draw panel number
            text = str(panel_num)
            text_x = panel_x + 30
            text_y = panel_y + 14
            draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
            
            # Draw corner markers
            draw.rectangle([panel_x, panel_y, panel_x+4, panel_y+4], fill=(255, 0, 0))  # Top-left red
            draw.rectangle([panel_x+60, panel_y, panel_x+64, panel_y+4], fill=(0, 255, 0))  # Top-right green
            draw.rectangle([panel_x, panel_y+28, panel_x+4, panel_y+32], fill=(0, 0, 255))  # Bottom-left blue
            draw.rectangle([panel_x+60, panel_y+28, panel_x+64, panel_y+32], fill=(255, 255, 0))  # Bottom-right yellow
    
    return np.array(img)

def create_logical_sequence_test(width, height):
    """Test logical panel sequence 1-6"""
    frames = []
    
    # Create 6 frames, each lighting up one logical panel
    for logical_panel in range(1, 7):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Calculate position based on logical panel number
        # Logical sequence: 1→2→3→6→5→4 (serpentine)
        if logical_panel <= 3:
            # Top row: panels 1, 2, 3
            py = 0
            px = logical_panel - 1
        else:
            # Bottom row: panels 4, 5, 6 (but in reverse order for serpentine)
            py = 1
            if logical_panel == 4:
                px = 2  # Panel 4 is rightmost in bottom row
            elif logical_panel == 5:
                px = 1  # Panel 5 is middle in bottom row
            elif logical_panel == 6:
                px = 0  # Panel 6 is leftmost in bottom row
        
        # Light up the panel
        x = px * 64
        y = py * 32
        
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        color = colors[logical_panel - 1]
        
        frame[y:y+32, x:x+64] = color
        frames.append(frame)
    
    return frames

def main():
    parser = argparse.ArgumentParser(description='Debug panel mapping')
    parser.add_argument('--host', default='localhost', help='Server hostname/IP')
    parser.add_argument('--port', type=int, default=9002, help='Server port')
    parser.add_argument('--test', choices=['grid', 'sequence'], default='grid',
                        help='Test type')
    args = parser.parse_args()
    
    # Connect to server
    client = SimpleVideoStreamClient(args.host, args.port)
    try:
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        if args.test == 'grid':
            print("🔢 Showing numbered grid...")
            frame = create_numbered_grid(client.matrix_width, client.matrix_height)
            client.send_frame(frame)
            print("Look at the display to see which physical panel shows which number")
            
        elif args.test == 'sequence':
            print("🔢 Showing logical sequence test...")
            frames = create_logical_sequence_test(client.matrix_width, client.matrix_height)
            
            for i, frame in enumerate(frames, 1):
                print(f"Logical panel {i}")
                client.send_frame(frame)
                time.sleep(2)
        
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