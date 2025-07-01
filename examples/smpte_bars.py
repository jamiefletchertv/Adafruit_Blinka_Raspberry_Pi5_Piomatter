#!/usr/bin/env python3
"""
SMPTE Color Bars Test Pattern for LED Matrix Testing
Standard broadcast test pattern for calibration and troubleshooting
"""

import numpy as np
import time
from simple_tcp_client import SimpleVideoStreamClient

# Configuration
SERVER_HOST = "localhost"
SERVER_PORT = 9002

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
    """
    Create SMPTE color bars test pattern
    
    Args:
        width: Matrix width in pixels
        height: Matrix height in pixels  
        pattern: "standard", "75%", "100%", or "rainbow"
    
    Returns:
        numpy array with SMPTE color pattern
    """
    
    # Create empty frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    if pattern == "standard":
        # Standard 7-bar SMPTE pattern
        bar_width = width // 7
        remainder = width % 7
        
        x_pos = 0
        for i, color_name in enumerate(SMPTE_SEQUENCE):
            # Handle remainder pixels by making last bar slightly wider
            current_bar_width = bar_width + (1 if i == len(SMPTE_SEQUENCE) - 1 else 0) + (remainder if i == len(SMPTE_SEQUENCE) - 1 else 0)
            
            # Fill the bar with color
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
            
    elif pattern == "100%":
        # 100% amplitude (full saturation)
        bar_width = width // 7
        remainder = width % 7
        
        x_pos = 0
        for i, color_name in enumerate(SMPTE_SEQUENCE):
            current_bar_width = bar_width + (remainder if i == len(SMPTE_SEQUENCE) - 1 else 0)
            color = SMPTE_COLORS[color_name]
            frame[:, x_pos:x_pos + current_bar_width] = color
            x_pos += current_bar_width
            
    elif pattern == "rainbow":
        # Smooth rainbow gradient for testing
        for x in range(width):
            hue = (x / width) * 360
            # Convert HSV to RGB
            h = hue / 60
            c = 255  # Full saturation and value
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
        # Checkerboard pattern for pixel alignment testing
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

def display_smpte_patterns():
    """Display standard SMPTE color bars test pattern"""
    
    print("🎨 SMPTE Color Bars Test Pattern")
    print("=" * 40)
    
    try:
        # Connect to TCP server
        client = SimpleVideoStreamClient(SERVER_HOST, SERVER_PORT)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        print("\n📺 Displaying Standard SMPTE Color Bars")
        print("Press Ctrl+C to stop")
        
        # Generate the standard SMPTE pattern
        frame = create_smpte_bars(
            client.matrix_width, 
            client.matrix_height, 
            "standard"
        )
        
        # Display continuously
        frames_sent = 0
        while True:
            success = client.send_frame(frame)
            if not success:
                print("❌ Failed to send frame - is server running?")
                return
            
            frames_sent += 1
            if frames_sent % 300 == 0:  # Every 10 seconds at 30 FPS
                print(f"   📊 Sent {frames_sent} frames ({frames_sent//30} seconds)")
            
            time.sleep(1/30)  # 30 FPS
                
    except KeyboardInterrupt:
        print("\n🛑 SMPTE pattern display stopped by user")
    except Exception as e:
        print(f"❌ Error during pattern display: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            client.disconnect()
            print("✅ Disconnected from server")
        except:
            pass

def display_single_pattern(pattern_type="standard", duration=10):
    """Display a single SMPTE pattern for testing"""
    
    print(f"🎨 Displaying SMPTE {pattern_type} pattern for {duration} seconds")
    
    try:
        client = SimpleVideoStreamClient(SERVER_HOST, SERVER_PORT)
        client.connect()
        
        frame = create_smpte_bars(
            client.matrix_width, 
            client.matrix_height, 
            pattern_type
        )
        
        start_time = time.time()
        frames_sent = 0
        
        while time.time() - start_time < duration:
            success = client.send_frame(frame)
            if not success:
                print("❌ Failed to send frame")
                break
                
            frames_sent += 1
            time.sleep(1/30)
        
        print(f"✅ Sent {frames_sent} frames")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            client.disconnect()
        except:
            pass

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments that are not host/port flags
    pattern_args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    if len(pattern_args) > 0 and pattern_args[0] not in ['localhost', '127.0.0.1']:
        # Single pattern mode
        pattern = pattern_args[0]
        duration = int(pattern_args[1]) if len(pattern_args) > 1 else 10
        display_single_pattern(pattern, duration)
    else:
        # Full sequence mode
        display_smpte_patterns()