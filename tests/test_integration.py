#!/usr/bin/env python3
"""
Integration tests for Piomatter WebSocket Video Streaming
"""

import subprocess
import time
import sys
import os
import signal
import socket
import numpy as np
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_tcp_client import SimpleVideoStreamClient

class IntegrationTest:
    def __init__(self):
        self.server_process = None
        self.server_port = 9004  # Use different port for testing
        self.logo_path = os.path.expanduser("~/repos/visualiser/assets/images/psybercell-logo.png")
        
    def start_server(self):
        """Start the simple TCP server in background"""
        print("Starting test server...")
        build_dir = os.path.join(os.path.dirname(__file__), "../src/build_simple")
        server_path = os.path.join(build_dir, "simple_server")
        
        if not os.path.exists(server_path):
            print(f"Error: Server not found at {server_path}")
            print("Please run 'make build' first")
            return False
            
        try:
            # Start server in background
            self.server_process = subprocess.Popen(
                [server_path, str(self.server_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Give server time to start
            
            # Check if server is running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                print(f"Server failed to start: {stderr.decode()}")
                return False
                
            print(f"Server started on port {self.server_port}")
            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the simple TCP server"""
        if self.server_process:
            print("Stopping test server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Server didn't stop gracefully, killing it...")
                self.server_process.kill()
                self.server_process.wait()
            self.server_process = None
    
    def test_connection(self):
        """Test basic connection to server"""
        print("\n=== Test 1: Basic Connection ===")
        client = SimpleVideoStreamClient("localhost", self.server_port)
        try:
            # Connect to server first
            client.connect()
            print(f"✓ Connected successfully")
            print(f"✓ Matrix dimensions: {client.matrix_width}x{client.matrix_height}")
            
            # Create a simple test image
            test_image = np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            test_image[10:20, 10:20] = [255, 0, 0]  # Red square
            
            result = client.send_frame(test_image)
            if result:
                print(f"✓ Test frame sent successfully")
            else:
                print("✗ Failed to send test frame")
                return False
            client.disconnect()
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def test_commands(self):
        """Test sending frames (TCP doesn't have separate commands)"""
        print("\n=== Test 2: Frame Commands ===")
        client = SimpleVideoStreamClient("localhost", self.server_port)
        try:
            client.connect()
            
            # Test CLEAR (black frame)
            clear_frame = np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            result = client.send_frame(clear_frame)
            if result:
                print("✓ CLEAR frame sent")
            else:
                print("✗ CLEAR frame failed")
                return False
            
            time.sleep(0.5)
            
            # Test colored frame 
            color_frame = np.full((client.matrix_height, client.matrix_width, 3), [0, 255, 0], dtype=np.uint8)  # Green
            result = client.send_frame(color_frame)
            if result:
                print("✓ Color frame sent")
            else:
                print("✗ Color frame failed") 
                return False
            
            client.disconnect()
            return True
        except Exception as e:
            print(f"✗ Command test failed: {e}")
            return False
    
    def test_frame_streaming(self):
        """Test streaming frames"""
        print("\n=== Test 3: Frame Streaming ===")
        client = SimpleVideoStreamClient("localhost", self.server_port)
        try:
            client.connect()
            # Create test frames
            for i in range(10):
                # Create gradient frame
                frame = np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
                frame[:, :, 0] = i * 25  # Red gradient  
                frame[:, :, 1] = 255 - i * 25  # Green inverse gradient
                frame[:, :, 2] = 128  # Constant blue
                
                result = client.send_frame(frame)
                if not result:
                    print(f"✗ Failed to send frame {i}")
                    return False
                time.sleep(0.1)
            
            print("✓ Streamed 10 test frames")
            client.disconnect()
            return True
        except Exception as e:
            print(f"✗ Frame streaming failed: {e}")
            return False
    
    def test_logo_display(self):
        """Test displaying a test image"""
        print("\n=== Test 4: Image Display ===")
        
        if not os.path.exists(self.logo_path):
            print(f"⚠ Logo not found at {self.logo_path}, using test image")
            # Create a test image
            test_img = Image.new('RGB', (128, 32), color='red')
            self.logo_path = "/tmp/test_logo.png"
            test_img.save(self.logo_path)
        
        client = SimpleVideoStreamClient("localhost", self.server_port)
        try:
            client.connect()
            # Load and process image exactly like the working debug test
            img = Image.open(self.logo_path)
            print(f"Logo loaded: mode={img.mode}, size={img.size}")
            
            # Convert to RGBA to handle transparency properly
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                print("Converted to RGBA")
            
            # Create black background 
            background = Image.new('RGBA', img.size, (0, 0, 0, 255))
            
            # Composite image over background
            composite = Image.alpha_composite(background, img)
            
            # Convert to RGB
            composite = composite.convert('RGB')
            
            # Resize to matrix size
            resized = composite.resize(
                (client.matrix_width, client.matrix_height),
                Image.Resampling.LANCZOS
            )
            
            # Convert to numpy
            frame = np.array(resized)
            print(f"Debug: Final frame shape: {frame.shape}")
            print(f"Debug: Value range: {frame.min()}-{frame.max()}")
            
            # Sample a few pixels for debugging
            h, w = frame.shape[:2]
            center_pixel = frame[h//2, w//2]
            print(f"Debug: Center pixel RGB{tuple(center_pixel)}")
            
            result = client.send_frame(frame)
            if result:
                print("✓ Image displayed successfully")
                time.sleep(1)
                client.disconnect()
                return True
            else:
                print("✗ Failed to display image")
                client.disconnect()
                return False
        except Exception as e:
            print(f"✗ Image display failed: {e}")
            return False
    
    def test_animation(self):
        """Test simple animation"""
        print("\n=== Test 5: Simple Animation ===")
        
        client = SimpleVideoStreamClient("localhost", self.server_port)
        try:
            client.connect()
            print("Starting animation (5 seconds)...")
            
            # Create simple moving dot animation
            for i in range(50):  # 5 seconds at 10 FPS
                frame = np.zeros((client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
                x = (i * 3) % client.matrix_width  # Moving dot across full width
                y = client.matrix_height // 2  # Center vertically
                
                # Make sure dot doesn't go out of bounds
                x_start = max(0, x-2)
                x_end = min(client.matrix_width, x+3)
                y_start = max(0, y-2) 
                y_end = min(client.matrix_height, y+3)
                
                frame[y_start:y_end, x_start:x_end] = [255, 255, 255]  # White dot
                
                result = client.send_frame(frame)
                if not result:
                    print(f"✗ Failed to send animation frame {i}")
                    return False
                time.sleep(0.1)
            
            print("✓ Animation completed successfully")
            client.disconnect()
            return True
        except Exception as e:
            print(f"✗ Logo animation failed: {e}")
            return False
    
    def test_performance(self):
        """Test streaming performance"""
        print("\n=== Test 6: Performance ===")
        client = SimpleVideoStreamClient("localhost", self.server_port)
        try:
            client.connect()
            # Stream frames and measure FPS
            frame_count = 100
            frame = np.random.randint(0, 255, (client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            
            start_time = time.time()
            for _ in range(frame_count):
                result = client.send_frame(frame)
                if not result:
                    print("✗ Frame send failed during performance test")
                    return False
            end_time = time.time()
            
            fps = frame_count / (end_time - start_time)
            print(f"✓ Achieved {fps:.1f} FPS (sent {frame_count} frames)")
            
            client.disconnect()
            return fps > 10  # Expect at least 10 FPS
        except Exception as e:
            print(f"✗ Performance test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("Starting Integration Tests")
        print("=" * 50)
        
        if not self.start_server():
            print("Failed to start server, aborting tests")
            return False
        
        try:
            results = []
            
            # Run each test
            results.append(self.test_connection())
            results.append(self.test_commands())
            results.append(self.test_frame_streaming())
            results.append(self.test_logo_display())
            results.append(self.test_animation())
            results.append(self.test_performance())
            
            # Summary
            print("\n" + "=" * 50)
            print("Test Summary:")
            passed = sum(results)
            total = len(results)
            print(f"Passed: {passed}/{total}")
            
            return all(results)
            
        finally:
            self.stop_server()

def main():
    """Run integration tests"""
    test = IntegrationTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()