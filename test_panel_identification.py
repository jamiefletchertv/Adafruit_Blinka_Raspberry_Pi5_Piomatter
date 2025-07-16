#!/usr/bin/env python3
"""
Panel identification test - displays panel numbers to identify correct ordering
"""

import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
from simple_tcp_client import SimpleVideoStreamClient
import argparse

def create_panel_test_pattern(width, height, panel_width=64, panel_height=32):
    """Create a test pattern showing panel numbers"""
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    
    # Calculate number of panels
    panels_x = width // panel_width
    panels_y = height // panel_height
    
    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    panel_num = 1
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    
    for row in range(panels_y):
        for col in range(panels_x):
            # Calculate panel position
            x = col * panel_width
            y = row * panel_height
            
            # Draw panel border
            color = colors[panel_num - 1]
            draw.rectangle([x, y, x + panel_width - 1, y + panel_height - 1], outline=color, width=2)
            
            # Draw panel number
            text = str(panel_num)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x + (panel_width - text_width) // 2
            text_y = y + (panel_height - text_height) // 2
            draw.text((text_x, text_y), text, fill=color, font=font)
            
            # Draw small corner markers
            # Top-left
            draw.rectangle([x, y, x+5, y+5], fill=color)
            # Top-right
            draw.rectangle([x + panel_width - 6, y, x + panel_width - 1, y+5], fill='white')
            
            panel_num += 1
    
    return np.array(img)

def create_individual_panel_test(width, height, panel_num, panel_width=64, panel_height=32):
    """Light up only a specific panel"""
    img = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(img)
    
    panels_x = width // panel_width
    panels_y = height // panel_height
    
    # Calculate which panel to light up
    panel_idx = panel_num - 1
    row = panel_idx // panels_x
    col = panel_idx % panels_x
    
    x = col * panel_width
    y = row * panel_height
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    color = colors[panel_idx % len(colors)]
    
    # Fill the panel
    draw.rectangle([x, y, x + panel_width - 1, y + panel_height - 1], fill=color)
    
    # Draw panel number
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    text = str(panel_num)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = x + (panel_width - text_width) // 2
    text_y = y + (panel_height - text_height) // 2
    draw.text((text_x, text_y), text, fill='black', font=font)
    
    return np.array(img)

def create_gradient_test(width, height):
    """Create a gradient to see if panels are continuous"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Horizontal gradient
    for x in range(width):
        color_val = int(255 * x / width)
        img[:, x] = [color_val, 0, 255 - color_val]
    
    return img

def main():
    parser = argparse.ArgumentParser(description='Test panel identification')
    parser.add_argument('--host', default='raspberrypi.local', help='Server hostname/IP')
    parser.add_argument('--port', type=int, default=9999, help='Server port')
    parser.add_argument('--mode', choices=['all', 'individual', 'gradient'], default='all',
                        help='Test mode')
    parser.add_argument('--panel', type=int, default=1, help='Panel number for individual mode')
    args = parser.parse_args()
    
    # Connect to server
    client = SimpleVideoStreamClient(args.host, args.port)
    try:
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        if args.mode == 'all':
            # Show all panel numbers
            print("🔢 Showing all panel numbers...")
            frame = create_panel_test_pattern(client.matrix_width, client.matrix_height)
            client.send_frame(frame)
            time.sleep(10)
            
        elif args.mode == 'individual':
            # Show panels one by one
            num_panels = (client.matrix_width // 64) * (client.matrix_height // 32)
            print(f"🔢 Showing panels 1-{num_panels} individually...")
            
            for panel in range(1, num_panels + 1):
                print(f"Panel {panel}")
                frame = create_individual_panel_test(client.matrix_width, client.matrix_height, panel)
                client.send_frame(frame)
                time.sleep(2)
                
        elif args.mode == 'gradient':
            # Show gradient
            print("🌈 Showing gradient test...")
            frame = create_gradient_test(client.matrix_width, client.matrix_height)
            client.send_frame(frame)
            time.sleep(10)
            
        # Clear display
        print("⬛ Clearing display...")
        client.send_frame(np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8))
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()