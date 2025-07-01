#!/usr/bin/env python3
"""
macOS-compatible test patterns client for remote Pi 5 RGB matrix server
Run this on macOS to test various color patterns on your Pi 5 RGB matrix
"""

import time
import numpy as np
import sys
import argparse

# Import our TCP client
from simple_tcp_client import SimpleVideoStreamClient

def create_test_patterns(width, height):
    """Generate various test patterns"""
    patterns = {}
    
    # 1. Pure color bars
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green  
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 255, 255) # White
    ]
    
    color_bars = np.zeros((height, width, 3), dtype=np.uint8)
    section_width = width // len(colors)
    for i, (r, g, b) in enumerate(colors):
        start_x = i * section_width
        end_x = start_x + section_width if i < len(colors) - 1 else width
        color_bars[:, start_x:end_x] = [r, g, b]
    patterns["color_bars"] = color_bars
    
    # 2. RGB gradient
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for x in range(width):
        # Horizontal RGB gradient
        r = int((x / width) * 255)
        g = int(((width - x) / width) * 255)
        b = 128
        gradient[:, x] = [r, g, b]
    patterns["rgb_gradient"] = gradient
    
    # 3. Checkerboard
    checkerboard = np.zeros((height, width, 3), dtype=np.uint8)
    square_size = 4
    for y in range(height):
        for x in range(width):
            if ((x // square_size) + (y // square_size)) % 2:
                checkerboard[y, x] = [255, 255, 255]  # White
            else:
                checkerboard[y, x] = [0, 0, 0]        # Black
    patterns["checkerboard"] = checkerboard
    
    # 4. Rainbow
    rainbow = np.zeros((height, width, 3), dtype=np.uint8)
    for x in range(width):
        hue = (x / width) * 360
        # Simple HSV to RGB conversion
        if hue < 60:
            r, g, b = 255, int(hue * 255 / 60), 0
        elif hue < 120:
            r, g, b = int((120 - hue) * 255 / 60), 255, 0
        elif hue < 180:
            r, g, b = 0, 255, int((hue - 120) * 255 / 60)
        elif hue < 240:
            r, g, b = 0, int((240 - hue) * 255 / 60), 255
        elif hue < 300:
            r, g, b = int((hue - 240) * 255 / 60), 0, 255
        else:
            r, g, b = 255, 0, int((360 - hue) * 255 / 60)
        rainbow[:, x] = [r, g, b]
    patterns["rainbow"] = rainbow
    
    # 5. Moving dot
    dot_frames = []
    for frame_i in range(width + height):
        dot = np.zeros((height, width, 3), dtype=np.uint8)
        if frame_i < width:
            # Horizontal movement
            x = frame_i
            y = height // 2
        else:
            # Vertical movement
            x = width // 2
            y = frame_i - width
            if y >= height:
                break
        if 0 <= x < width and 0 <= y < height:
            dot[y, x] = [255, 255, 255]  # White dot
        dot_frames.append(dot)
    patterns["moving_dot"] = dot_frames
    
    return patterns

def run_test_patterns(host, port):
    """Run all test patterns on remote server"""
    print("🎨 macOS Test Patterns Client")
    print("=" * 40)
    print(f"📡 Target server: {host}:{port}")
    
    try:
        # Connect to TCP server
        print(f"🔗 Connecting to server at {host}:{port}...")
        client = SimpleVideoStreamClient(host, port)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        # Generate test patterns
        patterns = create_test_patterns(client.matrix_width, client.matrix_height)
        
        print("\n🎨 Running test patterns (press Ctrl+C to stop)...")
        
        # Run each pattern
        for pattern_name, pattern_data in patterns.items():
            print(f"\n🔹 Pattern: {pattern_name}")
            
            if isinstance(pattern_data, list):  # Animated pattern
                for i, frame in enumerate(pattern_data):
                    success = client.send_frame(frame)
                    if not success:
                        print("❌ Failed to send frame")
                        return False
                    time.sleep(0.1)  # 10 FPS for animation
            else:  # Static pattern
                success = client.send_frame(pattern_data)
                if not success:
                    print("❌ Failed to send frame")
                    return False
                time.sleep(2)  # Show for 2 seconds
        
        print("\n🎉 All test patterns completed!")
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Test patterns stopped by user")
        return True
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running on the Pi 5")
        return False
    except Exception as e:
        print(f"❌ Error during test patterns: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            client.disconnect()
            print("✅ Disconnected from server")
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description="Run test patterns on remote RGB matrix server")
    parser.add_argument("--host", default="192.168.3.1", 
                       help="RGB matrix server hostname/IP (default: 192.168.3.1)")
    parser.add_argument("--port", type=int, default=9002, 
                       help="RGB matrix server port (default: 9002)")
    
    args = parser.parse_args()
    
    success = run_test_patterns(args.host, args.port)
    
    if success:
        print("🎉 Test patterns completed successfully!")
    else:
        print("❌ Test patterns failed - check server connection")
        sys.exit(1)

if __name__ == "__main__":
    main()