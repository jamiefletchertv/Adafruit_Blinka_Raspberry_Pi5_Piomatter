#!/usr/bin/env python3
"""
macOS-compatible animated logo client for remote Pi 5 RGB matrix server
Loads and animates images on the remote RGB matrix display
"""

import time
import numpy as np
from PIL import Image
import os
import sys
import argparse
from simple_tcp_client import SimpleVideoStreamClient

def load_and_prepare_image(image_path, max_height=28):
    """Load and prepare an image for animation"""
    if not os.path.exists(image_path):
        print(f"Warning: Image not found at {image_path}")
        print("Creating test pattern instead...")
        # Create a test pattern
        img = Image.new('RGB', (64, 24), color='black')
        # Add some test graphics
        for y in range(24):
            for x in range(64):
                if (x + y) % 8 < 4:
                    img.putpixel((x, y), (255, 0, 255))  # Magenta
        return img
    
    print(f"Loading image from: {image_path}")
    # Load the image with proper transparency handling
    img = Image.open(image_path)
    
    print(f"Original image size: {img.size[0]}x{img.size[1]}")
    
    # Convert to RGBA for transparency handling
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create black background
    background = Image.new('RGBA', img.size, (0, 0, 0, 255))
    
    # Composite image over background
    composite = Image.alpha_composite(background, img)
    
    # Convert to RGB
    rgb_img = composite.convert('RGB')
    
    # Scale to fit matrix height while maintaining aspect ratio
    aspect_ratio = rgb_img.size[0] / rgb_img.size[1]
    new_height = min(max_height, rgb_img.size[1])
    new_width = int(new_height * aspect_ratio)
    
    print(f"Scaled image size: {new_width}x{new_height}")
    resized_img = rgb_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return resized_img

def create_scroll_animation(img, matrix_width, matrix_height, scroll_type="horizontal"):
    """Create scrolling animation frames"""
    print(f"Creating {scroll_type} scroll animation...")
    
    img_array = np.array(img)
    img_height, img_width = img_array.shape[:2]
    
    frames = []
    
    if scroll_type == "horizontal":
        # Horizontal scroll (left to right)
        # Start with image off-screen left, end with image off-screen right
        total_travel = matrix_width + img_width
        num_frames = total_travel * 2  # Slow it down
        
        for frame_i in range(num_frames):
            # Calculate image position
            progress = frame_i / num_frames
            img_x = int(-img_width + progress * total_travel)
            
            # Create frame
            frame = np.zeros((matrix_height, matrix_width, 3), dtype=np.uint8)
            
            # Calculate placement (center vertically)
            img_y = (matrix_height - img_height) // 2
            
            # Copy visible portion of image to frame
            for y in range(img_height):
                frame_y = img_y + y
                if 0 <= frame_y < matrix_height:
                    for x in range(img_width):
                        frame_x = img_x + x
                        if 0 <= frame_x < matrix_width:
                            frame[frame_y, frame_x] = img_array[y, x]
            
            frames.append(frame)
    
    elif scroll_type == "vertical":
        # Vertical scroll (top to bottom)
        total_travel = matrix_height + img_height
        num_frames = total_travel * 2
        
        for frame_i in range(num_frames):
            progress = frame_i / num_frames
            img_y = int(-img_height + progress * total_travel)
            
            frame = np.zeros((matrix_height, matrix_width, 3), dtype=np.uint8)
            
            # Center horizontally
            img_x = (matrix_width - img_width) // 2
            
            # Copy visible portion
            for y in range(img_height):
                frame_y = img_y + y
                if 0 <= frame_y < matrix_height:
                    for x in range(img_width):
                        frame_x = img_x + x
                        if 0 <= frame_x < matrix_width:
                            frame[frame_y, frame_x] = img_array[y, x]
            
            frames.append(frame)
    
    elif scroll_type == "bounce":
        # Bouncing animation
        margin = 10
        max_x = matrix_width - img_width - margin
        max_y = matrix_height - img_height - margin
        
        if max_x <= margin or max_y <= margin:
            # Image too big, just center it
            frames = [np.zeros((matrix_height, matrix_width, 3), dtype=np.uint8)]
            img_x = (matrix_width - img_width) // 2
            img_y = (matrix_height - img_height) // 2
            
            for y in range(img_height):
                for x in range(img_width):
                    if (0 <= img_y + y < matrix_height and 
                        0 <= img_x + x < matrix_width):
                        frames[0][img_y + y, img_x + x] = img_array[y, x]
        else:
            num_frames = 120  # 4 seconds at 30fps
            
            for frame_i in range(num_frames):
                # Bouncing motion
                t = (frame_i / num_frames) * 4 * np.pi  # 2 complete bounces
                img_x = margin + int((max_x - margin) * (np.sin(t) + 1) / 2)
                img_y = margin + int((max_y - margin) * (np.cos(t) + 1) / 2)
                
                frame = np.zeros((matrix_height, matrix_width, 3), dtype=np.uint8)
                
                for y in range(img_height):
                    for x in range(img_width):
                        frame_y = img_y + y
                        frame_x = img_x + x
                        if (0 <= frame_y < matrix_height and 
                            0 <= frame_x < matrix_width):
                            frame[frame_y, frame_x] = img_array[y, x]
                
                frames.append(frame)
    
    print(f"Generated {len(frames)} animation frames")
    return frames

def run_animated_logo(host, port, image_path, animation_type="horizontal"):
    """Run animated logo on remote server"""
    print("🎨 macOS Animated Logo Client")
    print("=" * 40)
    print(f"📡 Target server: {host}:{port}")
    print(f"🖼️  Image: {image_path}")
    print(f"🎬 Animation: {animation_type}")
    
    try:
        # Connect to TCP server
        print(f"🔗 Connecting to server at {host}:{port}...")
        client = SimpleVideoStreamClient(host, port)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        # Load and prepare image
        img = load_and_prepare_image(image_path, client.matrix_height - 4)  # Leave some margin
        
        # Create animation frames
        frames = create_scroll_animation(img, client.matrix_width, client.matrix_height, animation_type)
        
        print(f"\n🎬 Playing animation (press Ctrl+C to stop)...")
        
        # Play animation
        while True:
            for frame in frames:
                success = client.send_frame(frame)
                if not success:
                    print("❌ Failed to send frame")
                    return False
                
                time.sleep(1/30)  # 30 FPS
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Animation stopped by user")
        return True
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running on the Pi 5")
        return False
    except Exception as e:
        print(f"❌ Error during animation: {e}")
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
    parser = argparse.ArgumentParser(description="Animate images on remote RGB matrix server")
    parser.add_argument("image", nargs="?", 
                       default=os.path.expanduser("~/repos/visualiser/assets/images/psybercell-logo.png"),
                       help="Path to image file")
    parser.add_argument("--host", default="192.168.3.1", 
                       help="RGB matrix server hostname/IP (default: 192.168.3.1)")
    parser.add_argument("--port", type=int, default=9002, 
                       help="RGB matrix server port (default: 9002)")
    parser.add_argument("--animation", default="horizontal",
                       choices=["horizontal", "vertical", "bounce"],
                       help="Animation type (default: horizontal)")
    
    args = parser.parse_args()
    
    success = run_animated_logo(args.host, args.port, args.image, args.animation)
    
    if success:
        print("🎉 Animation completed successfully!")
    else:
        print("❌ Animation failed - check server connection")
        sys.exit(1)

if __name__ == "__main__":
    main()