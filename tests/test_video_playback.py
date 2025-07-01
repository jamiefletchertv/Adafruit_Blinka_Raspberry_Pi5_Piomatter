#!/usr/bin/env python3
"""
Test video playback using the big-buck-bunny_600k.mp4 file
"""

import time
import numpy as np
import cv2
import os
import sys

# Import our TCP client
from simple_tcp_client import SimpleVideoStreamClient

# Configuration
VIDEO_PATH = "big-buck-bunny_600k.mp4"
SERVER_HOST = "localhost"
SERVER_PORT = 9002
TARGET_FPS = 30

def play_video():
    """Play the Big Buck Bunny video on the RGB matrix"""
    print("🎬 Starting Big Buck Bunny Video Playback")
    print("=" * 60)
    
    # Check if video file exists
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video file not found: {VIDEO_PATH}")
        return
    
    try:
        # Connect to TCP server
        client = SimpleVideoStreamClient(SERVER_HOST, SERVER_PORT)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        # Open video file
        cap = cv2.VideoCapture(VIDEO_PATH)
        if not cap.isOpened():
            print(f"❌ Could not open video file: {VIDEO_PATH}")
            return
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📹 Video info:")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps:.1f}")
        print(f"   Frames: {frame_count}")
        print(f"   Duration: {duration:.1f}s")
        print(f"🔄 Will scale to matrix: {client.matrix_width}x{client.matrix_height}")
        print("Press Ctrl+C to stop")
        
        frame_num = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("🔄 End of video - restarting from beginning")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
                continue
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize to matrix dimensions
            frame_resized = cv2.resize(frame_rgb, (client.matrix_width, client.matrix_height), 
                                     interpolation=cv2.INTER_AREA)
            
            # Convert to numpy array with correct dtype
            frame_array = np.array(frame_resized, dtype=np.uint8)
            
            # Send frame to matrix
            success = client.send_frame(frame_array)
            if not success:
                print("❌ Failed to send frame - is server running?")
                break
            
            # Log progress every 5 seconds
            if frame_num % (TARGET_FPS * 5) == 0:
                elapsed = time.time() - start_time
                current_video_time = frame_num / TARGET_FPS
                print(f"🎥 Frame {frame_num:4d} | Video time: {current_video_time:.1f}s | Elapsed: {elapsed:.1f}s")
            
            frame_num += 1
            
            # Control playback speed
            time.sleep(1/TARGET_FPS)
            
    except KeyboardInterrupt:
        print("\n🛑 Video playback stopped by user")
    except Exception as e:
        print(f"❌ Error during video playback: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            cap.release()
            client.disconnect()
            print("✅ Video released and disconnected from server")
        except:
            pass

if __name__ == "__main__":
    play_video()