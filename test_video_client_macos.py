#!/usr/bin/env python3
"""
macOS-compatible video client test for streaming to remote Pi 5 server
Run this on macOS to test video streaming to your Pi 5 RGB matrix server
"""

import time
import numpy as np
import cv2
import os
import sys
import argparse

# Import our TCP client
from simple_tcp_client import SimpleVideoStreamClient

def play_video_to_remote_server(video_path, host, port):
    """Play a video file to a remote RGB matrix server"""
    print("🎬 Starting Video Playback to Remote Server")
    print("=" * 60)
    print(f"📡 Target server: {host}:{port}")
    print(f"📹 Video file: {video_path}")
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    try:
        # Connect to TCP server
        print(f"🔗 Connecting to server at {host}:{port}...")
        client = SimpleVideoStreamClient(host, port)
        client.connect()
        print(f"✅ Connected to matrix: {client.matrix_width}x{client.matrix_height}")
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video file: {video_path}")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📹 Video properties:")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps:.1f}")
        print(f"   Frames: {frame_count}")
        print(f"   Duration: {duration:.1f}s")
        print(f"🔄 Scaling to matrix: {client.matrix_width}x{client.matrix_height}")
        print("Press Ctrl+C to stop playback")
        print()
        
        frame_num = 0
        start_time = time.time()
        target_fps = min(fps, 30)  # Cap at 30 FPS for network streaming
        
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
            
            # Log progress every 150 frames (5 seconds at 30fps)
            if frame_num % 150 == 0:
                elapsed = time.time() - start_time
                current_video_time = frame_num / target_fps
                print(f"🎥 Frame {frame_num:4d} | Video: {current_video_time:.1f}s | Elapsed: {elapsed:.1f}s")
            
            frame_num += 1
            
            # Control playback speed
            time.sleep(1/target_fps)
            
    except KeyboardInterrupt:
        print("\n🛑 Video playback stopped by user")
        return True
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running on the Pi 5")
        return False
    except Exception as e:
        print(f"❌ Error during video playback: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            cap.release()
            client.disconnect()
            print("✅ Video released and disconnected from server")
        except:
            pass
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Stream video to remote RGB matrix server")
    parser.add_argument("video", nargs="?", default="big-buck-bunny_600k.mp4", 
                       help="Path to video file (default: big-buck-bunny_600k.mp4)")
    parser.add_argument("--host", default="192.168.3.1", 
                       help="RGB matrix server hostname/IP (default: 192.168.3.1)")
    parser.add_argument("--port", type=int, default=9002, 
                       help="RGB matrix server port (default: 9002)")
    
    args = parser.parse_args()
    
    print("🍎 macOS RGB Matrix Video Client")
    print("=" * 40)
    
    success = play_video_to_remote_server(args.video, args.host, args.port)
    
    if success:
        print("🎉 Video streaming completed successfully!")
    else:
        print("❌ Video streaming failed - check server connection")
        sys.exit(1)

if __name__ == "__main__":
    main()