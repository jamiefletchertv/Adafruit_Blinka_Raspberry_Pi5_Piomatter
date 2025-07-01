#!/usr/bin/env python3
"""
Simple TCP client for Piomatter Simple TCP server
Reads video files/images and streams frames to LED matrix
"""

import socket
import cv2
import numpy as np
from PIL import Image
import sys
import time
import argparse
import os
from typing import Optional, Tuple
import threading

class SimpleVideoStreamClient:
    def __init__(self, host: str = "localhost", port: int = 9002):
        self.host = host
        self.port = port
        self.matrix_width = None
        self.matrix_height = None
        self.socket = None
        self.target_fps = 30  # Target FPS for video playback
        
    def connect(self):
        """Connect to the TCP server and get matrix dimensions"""
        print(f"Connecting to {self.host}:{self.port}...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        
        # Wait for matrix info
        data = self.socket.recv(1024).decode('utf-8')
        if data.startswith("MATRIX:"):
            dims = data.strip().split("MATRIX:")[1].split("x")
            self.matrix_width = int(dims[0])
            self.matrix_height = int(dims[1])
            print(f"Connected! Matrix size: {self.matrix_width}x{self.matrix_height}")
        else:
            raise Exception(f"Unexpected server response: {data}")
    
    def resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to match matrix dimensions using PIL for better quality"""
        # Convert from BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Use PIL for high-quality resizing
        pil_image = Image.fromarray(frame_rgb)
        pil_resized = pil_image.resize(
            (self.matrix_width, self.matrix_height), 
            Image.Resampling.LANCZOS
        )
        
        # Convert back to numpy array
        return np.array(pil_resized)
    
    def send_frame(self, frame: np.ndarray):
        """Send a single frame to the server"""
        try:
            # Ensure frame is correct size, resize if needed
            if frame.shape[:2] != (self.matrix_height, self.matrix_width):
                # Only use resize_frame for video frames (BGR format)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # Assume this is already RGB from PIL, just resize
                    pil_image = Image.fromarray(frame)
                    pil_resized = pil_image.resize(
                        (self.matrix_width, self.matrix_height), 
                        Image.Resampling.LANCZOS
                    )
                    frame = np.array(pil_resized)
            
            # Ensure we have the right shape
            if frame.shape != (self.matrix_height, self.matrix_width, 3):
                raise ValueError(f"Frame shape {frame.shape} doesn't match expected {(self.matrix_height, self.matrix_width, 3)}")
            
            # Keep standard RGB format as expected by Adafruit implementation
            # The Adafruit code expects: R=source[i+0], G=source[i+1], B=source[i+2]
            
            # Flatten to bytes (RGB888 format for matrix)
            frame_bytes = frame.tobytes()
            
            # Send as binary frame
            self.socket.sendall(frame_bytes)
            return True
        except Exception as e:
            print(f"Error sending frame: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def send_command(self, command: str):
        """Send a command to the server"""
        cmd_bytes = f"CMD:{command}".encode('utf-8')
        self.socket.sendall(cmd_bytes)
    
    def stream_video(self, video_path: str, loop: bool = False):
        """Stream a video file to the matrix"""
        print(f"Opening video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Failed to open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video info: {fps} FPS, {total_frames} frames")
        
        # Calculate frame delay to maintain proper playback speed
        frame_delay = 1.0 / min(fps, self.target_fps)
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    if loop:
                        # Restart video
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break
                
                # Send frame
                self.send_frame(frame)
                frame_count += 1
                
                # Print progress
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed
                    progress = (frame_count / total_frames) * 100
                    print(f"Progress: {progress:.1f}% | FPS: {actual_fps:.1f}")
                
                # Maintain frame rate
                target_time = start_time + (frame_count * frame_delay)
                current_time = time.time()
                if current_time < target_time:
                    time.sleep(target_time - current_time)
                
        finally:
            cap.release()
            print(f"Streamed {frame_count} frames")
    
    def stream_image(self, image_path: str, animate: bool = False):
        """Display a static image on the matrix, with optional animation effects"""
        print(f"Loading image: {image_path}")
        
        # Load image using PIL
        image = Image.open(image_path)
        
        # Convert to RGBA to handle transparency
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create a background (black by default)
        background = Image.new('RGBA', image.size, (0, 0, 0, 255))
        
        # Composite image over background
        composite = Image.alpha_composite(background, image)
        
        # Convert to RGB
        composite = composite.convert('RGB')
        
        # Resize to matrix dimensions
        resized = composite.resize(
            (self.matrix_width, self.matrix_height), 
            Image.Resampling.LANCZOS
        )
        
        if animate:
            self.animate_image(resized)
        else:
            # Convert to numpy array and send
            frame = np.array(resized)
            # Ensure we have RGB format (PIL gives us RGB, which is what we want)
            print(f"Image loaded: {frame.shape}, color range: {frame.min()}-{frame.max()}")
            self.send_frame(frame)
            print("Image sent to display")
    
    def animate_image(self, image: Image.Image):
        """Apply horizontal scrolling animation to preserve original colors"""
        print("Animating image...")
        base_array = np.array(image)
        height, width = base_array.shape[:2]
        
        # Create larger canvas for scrolling effect (3x wider)
        scroll_width = width * 3
        scroll_canvas = np.zeros((height, scroll_width, 3), dtype=np.uint8)
        
        # Place image at different positions across the canvas
        scroll_canvas[:, 0:width] = base_array                    # Left
        scroll_canvas[:, width:width*2] = base_array              # Center  
        scroll_canvas[:, width*2:width*3] = base_array            # Right
        
        # Animation loop - scroll from right to left
        for i in range(180):  # About 6 seconds at 30fps
            # Calculate scroll position (right to left)
            scroll_pos = int((i / 180.0) * width * 2)
            
            # Extract the visible portion (matrix window)
            start_x = scroll_pos
            end_x = start_x + width
            
            # Make sure we don't exceed canvas bounds
            if end_x <= scroll_width:
                frame = scroll_canvas[:, start_x:end_x]
            else:
                # Wrap around
                remaining = end_x - scroll_width
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                frame[:, :scroll_width-start_x] = scroll_canvas[:, start_x:]
                frame[:, scroll_width-start_x:] = scroll_canvas[:, :remaining]
            
            self.send_frame(frame)
            time.sleep(0.033)  # ~30 FPS
        
        # Send original image at the end
        self.send_frame(base_array)
        print("Animation complete")
    
    def stream_webcam(self, camera_index: int = 0):
        """Stream from webcam"""
        print(f"Opening webcam {camera_index}...")
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise Exception(f"Failed to open webcam {camera_index}")
        
        # Set webcam to reasonable resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        frame_count = 0
        start_time = time.time()
        
        print("Streaming from webcam... Press Ctrl+C to stop")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read from webcam")
                    break
                
                # Send frame
                self.send_frame(frame)
                frame_count += 1
                
                # Print FPS periodically
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"FPS: {fps:.1f}")
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.033)  # ~30 FPS
                
        finally:
            cap.release()
            print(f"Streamed {frame_count} frames")
    
    def run_test_pattern(self):
        """Display a test pattern with clear RGB colors"""
        print("Displaying test pattern...")
        
        # Test pure colors first
        colors = [
            (255, 0, 0),    # Pure red
            (0, 255, 0),    # Pure green  
            (0, 0, 255),    # Pure blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255) # White
        ]
        
        for i, (r, g, b) in enumerate(colors):
            frame = np.zeros((self.matrix_height, self.matrix_width, 3), dtype=np.uint8)
            
            # Fill different sections with different colors
            section_width = self.matrix_width // len(colors)
            start_x = i * section_width
            end_x = min((i + 1) * section_width, self.matrix_width)
            
            frame[:, start_x:end_x] = [r, g, b]
            
            print(f"Showing color {i+1}/{len(colors)}: RGB({r},{g},{b}) - Should see: {'Red' if r==255 and g==0 and b==0 else 'Green' if g==255 and r==0 and b==0 else 'Blue' if b==255 and r==0 and g==0 else 'Mixed'}")
            self.send_frame(frame)
            time.sleep(2.0)  # Longer pause to see each color clearly
        
        # Show all colors at once
        frame = np.zeros((self.matrix_height, self.matrix_width, 3), dtype=np.uint8)
        for i, (r, g, b) in enumerate(colors):
            section_width = self.matrix_width // len(colors)
            start_x = i * section_width
            end_x = min((i + 1) * section_width, self.matrix_width)
            frame[:, start_x:end_x] = [r, g, b]
        
        print("Showing all colors together")
        self.send_frame(frame)
        time.sleep(2.0)
        
        print("Test pattern complete")
    
    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
            print("Disconnected")

def main(args):
    client = SimpleVideoStreamClient(args.host, args.port)
    
    try:
        client.connect()
        
        if args.clear:
            client.send_command("CLEAR")
            return
        
        if args.test:
            client.run_test_pattern()
        elif args.webcam is not None:
            client.stream_webcam(args.webcam)
        elif args.input:
            # Check if input is image or video
            ext = os.path.splitext(args.input)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                client.stream_image(args.input, animate=args.animate)
                # Keep displaying for a while unless specified otherwise
                if not args.no_wait and not args.animate:
                    time.sleep(args.display_time)
            else:
                client.stream_video(args.input, loop=args.loop)
        
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream video to LED matrix via Simple TCP")
    parser.add_argument("input", nargs="?", help="Video file or image to stream")
    parser.add_argument("--host", default="localhost", help="TCP server host")
    parser.add_argument("--port", type=int, default=9002, help="TCP server port")
    parser.add_argument("--loop", action="store_true", help="Loop video playback")
    parser.add_argument("--test", action="store_true", help="Display test pattern")
    parser.add_argument("--clear", action="store_true", help="Clear the display")
    parser.add_argument("--webcam", type=int, help="Use webcam (specify index, e.g., 0)")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait after displaying image")
    parser.add_argument("--display-time", type=float, default=10.0, help="Time to display static images (seconds)")
    parser.add_argument("--animate", action="store_true", help="Animate static images with effects")
    
    args = parser.parse_args()
    
    if not any([args.input, args.test, args.clear, args.webcam is not None]):
        parser.error("Please specify an input file, --test, --clear, or --webcam")
    
    main(args)