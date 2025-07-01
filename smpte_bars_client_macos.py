#!/usr/bin/env python3
"""
macOS-compatible SMPTE Color Bars client for remote Pi 5 RGB matrix server
Standard broadcast test patterns for calibration and troubleshooting
"""

import numpy as np
import time
import argparse
import sys
from simple_tcp_client import SimpleVideoStreamClient

# Standard SMPTE color bars (RGB values 0-255)
SMPTE_COLORS = {
    'white':    (255, 255, 255),
    'yellow':   (255, 255, 0),
    'cyan':     (0, 255, 255),
    'green':    (0, 255, 0),
    'magenta':  (255, 0, 255),
    'red':      (255, 0, 0),
    'blue':     (0, 0, 255),
    'black':    (0, 0, 0),
}

# Standard SMPTE bar sequence
SMPTE_SEQUENCE = ['white', 'yellow', 'cyan', 'green', 'magenta', 'red', 'blue']

def create_smpte_bars(width, height, pattern="standard"):
    """Create SMPTE color bars test pattern"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    if pattern == "standard":
        # Standard 7-bar SMPTE pattern
        bar_width = width // 7
        remainder = width % 7
        
        x_pos = 0
        for i, color_name in enumerate(SMPTE_SEQUENCE):
            current_bar_width = bar_width + (remainder if i == len(SMPTE_SEQUENCE) - 1 else 0)
            color = SMPTE_COLORS[color_name]
            frame[:, x_pos:x_pos + current_bar_width] = color
            x_pos += current_bar_width
            
    elif pattern == "75%":  
        # 75% amplitude SMPTE bars (broadcast standard)
        colors_75 = [
            (191, 191, 191),  # 75% white
            (191, 191, 0),    # 75% yellow
            (0, 191, 191),    # 75% cyan  
            (0, 191, 0),      # 75% green
            (191, 0, 191),    # 75% magenta
            (191, 0, 0),      # 75% red
            (0, 0, 191),      # 75% blue
        ]
        
        bar_width = width // 7
        remainder = width % 7
        
        x_pos = 0
        for i, color in enumerate(colors_75):
            current_bar_width = bar_width + (remainder if i == len(colors_75) - 1 else 0)
            frame[:, x_pos:x_pos + current_bar_width] = color
            x_pos += current_bar_width
            
    elif pattern == "rainbow":
        # Smooth rainbow gradient
        for x in range(width):
            hue = (x / width) * 360
            h = hue / 60
            c = 255
            x_val = c * (1 - abs((h % 2) - 1))
            
            if h < 1:
                rgb = (c, x_val, 0)
            elif h < 2:  
                rgb = (x_val, c, 0)
            elif h < 3:
                rgb = (0, c, x_val)
            elif h < 4:
                rgb = (0, x_val, c)
            elif h < 5:
                rgb = (x_val, 0, c)
            else:
                rgb = (c, 0, x_val)
                
            frame[:, x] = rgb
    
    elif pattern == "checkerboard":
        # Checkerboard pattern for pixel alignment
        square_size = min(width // 16, height // 8)
        if square_size < 1:
            square_size = 1
            
        for y in range(height):
            for x in range(width):
                if ((x // square_size) + (y // square_size)) % 2 == 0:
                    frame[y, x] = (255, 255, 255)  # White
                else:
                    frame[y, x] = (0, 0, 0)        # Black
                    
    elif pattern == "gradient":
        # Horizontal gradient for brightness testing
        for x in range(width):
            intensity = int((x / width) * 255)
            frame[:, x] = (intensity, intensity, intensity)
    
    return frame

def run_smpte_patterns(host, port, pattern_type="all", duration=10):
    """Run SMPTE color bars on remote server"""
    print("📺 macOS SMPTE Color Bars Client")
    print("=" * 40)
    print(f"📡 Target server: {host}:{port}")
    print(f"🎨 Pattern type: {pattern_type}")
    
    try:
        # Connect to TCP server
        print(f"🔗 Connecting to server at {host}:{port}...")
        client = SimpleVideoStreamClient(host, port)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        if pattern_type == "all":
            # Show all patterns in sequence
            patterns = ["standard", "75%", "rainbow", "checkerboard", "gradient"]
            print(f"\n📺 Running all SMPTE patterns ({duration}s each)")
            
            for pattern in patterns:
                print(f"\n🔹 Pattern: {pattern}")
                frame = create_smpte_bars(client.matrix_width, client.matrix_height, pattern)
                
                start_time = time.time()
                frames_sent = 0
                
                while time.time() - start_time < duration:
                    success = client.send_frame(frame)
                    if not success:
                        print("❌ Failed to send frame")
                        return False
                    
                    frames_sent += 1
                    time.sleep(1/30)  # 30 FPS
                
                print(f"   ✅ Sent {frames_sent} frames")
        else:
            # Show single pattern
            print(f"\n📺 Displaying {pattern_type} pattern")
            frame = create_smpte_bars(client.matrix_width, client.matrix_height, pattern_type)
            
            print("Press Ctrl+C to stop...")
            frames_sent = 0
            
            while True:
                success = client.send_frame(frame)
                if not success:
                    print("❌ Failed to send frame")
                    return False
                
                frames_sent += 1
                if frames_sent % 300 == 0:  # Every 10 seconds at 30 FPS
                    print(f"   📊 Sent {frames_sent} frames ({frames_sent//30} seconds)")
                
                time.sleep(1/30)  # 30 FPS
        
        print("\n🎉 SMPTE patterns completed!")
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 SMPTE patterns stopped by user")
        return True
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running on the Pi 5")
        return False
    except Exception as e:
        print(f"❌ Error during SMPTE patterns: {e}")
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
    parser = argparse.ArgumentParser(description="Run SMPTE color bars on remote RGB matrix server")
    parser.add_argument("--host", default="192.168.3.1", 
                       help="RGB matrix server hostname/IP (default: 192.168.3.1)")
    parser.add_argument("--port", type=int, default=9002, 
                       help="RGB matrix server port (default: 9002)")
    parser.add_argument("--pattern", default="all",
                       choices=["all", "standard", "75%", "rainbow", "checkerboard", "gradient"],
                       help="Pattern type to display (default: all)")
    parser.add_argument("--duration", type=int, default=10,
                       help="Duration for each pattern in seconds (default: 10)")
    
    args = parser.parse_args()
    
    success = run_smpte_patterns(args.host, args.port, args.pattern, args.duration)
    
    if success:
        print("🎉 SMPTE patterns completed successfully!")
    else:
        print("❌ SMPTE patterns failed - check server connection")
        sys.exit(1)

if __name__ == "__main__":
    main()