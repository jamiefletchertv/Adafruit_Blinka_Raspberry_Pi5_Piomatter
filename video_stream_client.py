#!/usr/bin/env python3
"""
Video streaming client for Piomatter WebSocket server
Reads video files/images and streams frames to LED matrix
"""

import asyncio
import websockets
import cv2
import numpy as np
from PIL import Image
import sys
import time
import argparse
import os
from typing import Optional, Tuple
import struct

class VideoStreamClient:
    def __init__(self, host: str = "localhost", port: int = 9002):
        self.uri = f"ws://{host}:{port}"
        self.matrix_width = None
        self.matrix_height = None
        self.websocket = None
        self.target_fps = 30  # Target FPS for video playback
        
    async def connect(self):
        """Connect to the WebSocket server and get matrix dimensions"""
        print(f"Connecting to {self.uri}...")
        self.websocket = await websockets.connect(self.uri)
        
        # Wait for matrix info
        message = await self.websocket.recv()
        if message.startswith("MATRIX:"):
            dims = message[7:].split("x")
            self.matrix_width = int(dims[0])
            self.matrix_height = int(dims[1])
            print(f"Connected! Matrix size: {self.matrix_width}x{self.matrix_height}")
        else:
            raise Exception(f"Unexpected server response: {message}")
    
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
    
    async def send_frame(self, frame: np.ndarray):
        """Send a single frame to the server"""
        # Ensure frame is in RGB format and correct size
        if frame.shape != (self.matrix_height, self.matrix_width, 3):
            frame = self.resize_frame(frame)
        
        # Flatten to bytes (RGB888 format)
        frame_bytes = frame.tobytes()
        
        # Send as binary frame
        await self.websocket.send(frame_bytes)
    
    async def send_command(self, command: str):
        """Send a command to the server"""
        await self.websocket.send(f"CMD:{command}")
    
    async def stream_video(self, video_path: str):
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
                    if args.loop:
                        # Restart video
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break
                
                # Send frame
                await self.send_frame(frame)
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
                    await asyncio.sleep(target_time - current_time)
                
        finally:
            cap.release()
            print(f"Streamed {frame_count} frames")
    
    async def stream_image(self, image_path: str, animate: bool = False):
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
            await self.animate_image(resized)
        else:
            # Convert to numpy array and send
            frame = np.array(resized)
            await self.send_frame(frame)
            print("Image sent to display")
    
    async def animate_image(self, image: Image.Image):
        """Apply various animation effects to an image"""
        print("Animating image...")
        base_array = np.array(image)
        height, width = base_array.shape[:2]
        
        # Animation loop
        for i in range(300):  # About 10 seconds at 30fps
            frame = base_array.copy()
            
            # Choose animation based on cycle
            animation_type = (i // 60) % 5
            
            if animation_type == 0:
                # Fade in/out
                brightness = abs(np.sin(i * 0.05))
                frame = (frame * brightness).astype(np.uint8)
                
            elif animation_type == 1:
                # Rotating hue shift
                hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
                hsv[:, :, 0] = (hsv[:, :, 0] + i * 2) % 180
                frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
                
            elif animation_type == 2:
                # Zoom in/out
                scale = 1.0 + 0.3 * np.sin(i * 0.05)
                M = cv2.getRotationMatrix2D((width/2, height/2), 0, scale)
                frame = cv2.warpAffine(frame, M, (width, height))
                
            elif animation_type == 3:
                # Rotation
                angle = i * 2
                M = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
                frame = cv2.warpAffine(frame, M, (width, height))
                
            else:
                # Wave distortion
                for y in range(height):
                    shift = int(5 * np.sin(y * 0.2 + i * 0.1))
                    frame[y] = np.roll(frame[y], shift, axis=0)
            
            await self.send_frame(frame)
            await asyncio.sleep(0.033)  # ~30 FPS
        
        # Send original image at the end
        await self.send_frame(base_array)
        print("Animation complete")
    
    async def stream_webcam(self, camera_index: int = 0):
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
                await self.send_frame(frame)
                frame_count += 1
                
                # Print FPS periodically
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"FPS: {fps:.1f}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.033)  # ~30 FPS
                
        finally:
            cap.release()
            print(f"Streamed {frame_count} frames")
    
    async def run_test_pattern(self):
        """Display a test pattern"""
        print("Displaying test pattern...")
        
        # Create rainbow gradient
        frame = np.zeros((self.matrix_height, self.matrix_width, 3), dtype=np.uint8)
        
        for i in range(10):
            # Create shifting rainbow
            for x in range(self.matrix_width):
                for y in range(self.matrix_height):
                    hue = ((x + y + i * 10) % 180)
                    # Create HSV color
                    hsv = np.array([[[hue, 255, 255]]], dtype=np.uint8)
                    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
                    frame[y, x] = rgb[0, 0]
            
            await self.send_frame(frame)
            await asyncio.sleep(0.1)
        
        print("Test pattern complete")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected")

async def main(args):
    client = VideoStreamClient(args.host, args.port)
    
    try:
        await client.connect()
        
        if args.clear:
            await client.send_command("CLEAR")
            return
        
        if args.test:
            await client.run_test_pattern()
        elif args.webcam is not None:
            await client.stream_webcam(args.webcam)
        elif args.input:
            # Check if input is image or video
            ext = os.path.splitext(args.input)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                await client.stream_image(args.input, animate=args.animate)
                # Keep displaying for a while unless specified otherwise
                if not args.no_wait and not args.animate:
                    await asyncio.sleep(args.display_time)
            else:
                await client.stream_video(args.input)
        
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream video to LED matrix via WebSocket")
    parser.add_argument("input", nargs="?", help="Video file or image to stream")
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=9002, help="WebSocket server port")
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
    
    asyncio.run(main(args))