#!/usr/bin/env python3
"""
Simple PsyberCell logo animation - moves logo from left to right using TCP server
"""

import time
import numpy as np
from PIL import Image
import os
import sys

# Import our TCP client
from simple_tcp_client import SimpleVideoStreamClient

# Configuration
LOGO_PATH = os.path.expanduser("~/repos/visualiser/assets/images/psybercell-logo.png")
SERVER_HOST = "localhost"
SERVER_PORT = 9002

def load_and_prepare_logo(max_height=28):
    """Load and prepare the logo for animation - scale to fit matrix height"""
    if not os.path.exists(LOGO_PATH):
        print(f"Warning: Logo not found at {LOGO_PATH}")
        print("Creating test pattern instead...")
        # Create a test pattern
        img = Image.new('RGB', (64, 24), color='black')
        # Add some test graphics
        for y in range(24):
            for x in range(64):
                if (x + y) % 8 < 4:
                    img.putpixel((x, y), (255, 0, 255))  # Magenta
        return img
    
    print(f"Loading logo from: {LOGO_PATH}")
    # Load the logo with proper transparency handling
    logo = Image.open(LOGO_PATH)
    
    print(f"Original logo size: {logo.size[0]}x{logo.size[1]}")
    
    # Convert to RGBA for transparency handling
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    
    # Create black background
    background = Image.new('RGBA', logo.size, (0, 0, 0, 255))
    
    # Composite logo over background
    composite = Image.alpha_composite(background, logo)
    
    # Convert to RGB
    logo_rgb = composite.convert('RGB')
    
    # Scale to fit matrix height while preserving aspect ratio
    original_width, original_height = logo_rgb.size
    if original_height > max_height:
        # Calculate new dimensions maintaining aspect ratio
        scale_factor = max_height / original_height
        new_width = int(original_width * scale_factor)
        new_height = max_height
        
        print(f"Scaling logo to fit matrix: {new_width}x{new_height} (scale: {scale_factor:.3f})")
        logo_rgb = logo_rgb.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        print(f"Logo fits matrix height: {original_width}x{original_height}")
    
    return logo_rgb


def animate_logo():
    """Simple right-to-left logo animation"""
    print("🎨 Starting PsyberCell Logo Animation (Right to Left)")
    print("=" * 60)
    
    try:
        # Connect to TCP server
        client = SimpleVideoStreamClient(SERVER_HOST, SERVER_PORT)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        # Load and prepare logo scaled to fit matrix height
        max_logo_height = client.matrix_height - 4  # Leave 2 pixel margin top/bottom
        base_logo = load_and_prepare_logo(max_logo_height)
        logo_array = np.array(base_logo)
        logo_width = base_logo.size[0]
        logo_height = base_logo.size[1]
        
        print(f"📐 Final logo size: {logo_width}x{logo_height}")
        print("🚀 Starting right-to-left animation...")
        print("Press Ctrl+C to stop")
        
        frame_count = 0
        # Calculate animation parameters
        travel_distance = client.matrix_width + logo_width  # Logo travels completely across and off screen
        animation_duration = 6.0  # 6 seconds to cross the screen (half speed)
        frames_per_cycle = int(animation_duration * 30)  # 30 FPS
        
        while True:
            # Create black background
            frame = np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            
            # Calculate logo position
            cycle_frame = frame_count % frames_per_cycle
            progress = cycle_frame / frames_per_cycle  # 0.0 to 1.0
            
            # Logo starts off-screen right (matrix_width) and ends off-screen left (-logo_width)
            logo_x = int(client.matrix_width - (progress * travel_distance))
            logo_y = (client.matrix_height - logo_height) // 2  # Center vertically
            
            # Paste logo onto frame if it's visible
            if logo_x + logo_width > 0 and logo_x < client.matrix_width:
                # Calculate visible portion of logo
                src_x_start = max(0, -logo_x)
                src_x_end = min(logo_width, client.matrix_width - logo_x)
                src_y_start = 0
                src_y_end = logo_height
                
                dst_x_start = max(0, logo_x)
                dst_x_end = min(client.matrix_width, logo_x + logo_width)
                dst_y_start = logo_y
                dst_y_end = logo_y + logo_height
                
                # Copy visible portion
                if (src_x_end > src_x_start and src_y_end > src_y_start and 
                    dst_x_end > dst_x_start and dst_y_end > dst_y_start):
                    frame[dst_y_start:dst_y_end, dst_x_start:dst_x_end] = \
                        logo_array[src_y_start:src_y_end, src_x_start:src_x_end]
            
            # Send frame to matrix
            success = client.send_frame(frame)
            if not success:
                print("❌ Failed to send frame - is server running?")
                break
            
            # Log progress every second
            if frame_count % 30 == 0:
                cycle_seconds = (cycle_frame / 30) + 1
                print(f"🎬 Animation cycle: {cycle_seconds:.1f}s, Logo position: {logo_x:3d}px")
            
            frame_count += 1
            time.sleep(1/30)  # 30 FPS
            
    except KeyboardInterrupt:
        print("\n🛑 Animation stopped by user")
    except Exception as e:
        print(f"❌ Error during animation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            client.disconnect()
            print("✅ Disconnected from server")
        except:
            pass

if __name__ == "__main__":
    animate_logo()