#!/usr/bin/env python3
"""
Performance tests for Piomatter WebSocket Video Streaming
"""

import asyncio
import time
import sys
import os
import argparse
import numpy as np
from PIL import Image
import psutil
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_stream_client import VideoStreamClient


class PerformanceTest:
    def __init__(self, host="localhost", port=9002):
        self.host = host
        self.port = port
        self.results = {
            'fps_tests': [],
            'latency_tests': [],
            'memory_usage': [],
            'cpu_usage': []
        }
    
    async def test_sustained_fps(self, duration=10, target_fps=30):
        """Test sustained frame rate over time"""
        print(f"\n=== Sustained FPS Test ({duration}s @ {target_fps} FPS) ===")
        client = VideoStreamClient(self.host, self.port)
        
        try:
            await client.connect()
            
            # Create test frame
            frame = np.random.randint(0, 255, 
                (client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            
            frame_count = 0
            frame_times = []
            start_time = time.time()
            frame_interval = 1.0 / target_fps
            
            while time.time() - start_time < duration:
                frame_start = time.time()
                
                # Send frame
                await client.send_frame(frame)
                frame_count += 1
                
                # Track timing
                frame_end = time.time()
                frame_times.append(frame_end - frame_start)
                
                # Maintain target FPS
                elapsed = frame_end - frame_start
                if elapsed < frame_interval:
                    await asyncio.sleep(frame_interval - elapsed)
            
            # Calculate results
            total_time = time.time() - start_time
            actual_fps = frame_count / total_time
            avg_frame_time = statistics.mean(frame_times) * 1000  # ms
            
            print(f"Target FPS: {target_fps}")
            print(f"Actual FPS: {actual_fps:.2f}")
            print(f"Frames sent: {frame_count}")
            print(f"Avg frame time: {avg_frame_time:.2f}ms")
            print(f"Efficiency: {(actual_fps/target_fps)*100:.1f}%")
            
            self.results['fps_tests'].append({
                'target_fps': target_fps,
                'actual_fps': actual_fps,
                'frame_count': frame_count,
                'avg_frame_time_ms': avg_frame_time
            })
            
            await client.disconnect()
            return actual_fps
            
        except Exception as e:
            print(f"Error: {e}")
            return 0
    
    async def test_burst_performance(self, burst_size=100):
        """Test maximum burst transmission rate"""
        print(f"\n=== Burst Performance Test ({burst_size} frames) ===")
        client = VideoStreamClient(self.host, self.port)
        
        try:
            await client.connect()
            
            # Create test frame
            frame = np.random.randint(0, 255, 
                (client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            
            # Send burst
            start_time = time.time()
            for _ in range(burst_size):
                await client.send_frame(frame)
            end_time = time.time()
            
            # Calculate results
            duration = end_time - start_time
            burst_fps = burst_size / duration
            
            print(f"Burst size: {burst_size} frames")
            print(f"Duration: {duration:.2f}s")
            print(f"Burst FPS: {burst_fps:.2f}")
            print(f"Avg time per frame: {(duration/burst_size)*1000:.2f}ms")
            
            await client.disconnect()
            return burst_fps
            
        except Exception as e:
            print(f"Error: {e}")
            return 0
    
    async def test_frame_size_impact(self):
        """Test impact of different frame sizes"""
        print("\n=== Frame Size Impact Test ===")
        
        # Test with different matrix sizes (simulated)
        test_sizes = [(32, 32), (64, 64), (128, 64), (128, 128)]
        results = []
        
        for width, height in test_sizes:
            print(f"\nTesting {width}x{height}...")
            
            # Create frame of specific size
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            frame_size_bytes = frame.nbytes
            
            # Measure transmission time
            start_time = time.time()
            
            # Simulate sending (in real test, would resize)
            frame_data = frame.tobytes()
            
            transmission_time = time.time() - start_time
            
            print(f"Frame size: {frame_size_bytes/1024:.1f}KB")
            print(f"Transmission time: {transmission_time*1000:.2f}ms")
            
            results.append({
                'dimensions': f"{width}x{height}",
                'size_kb': frame_size_bytes/1024,
                'time_ms': transmission_time*1000
            })
        
        return results
    
    async def test_animation_performance(self):
        """Test performance of different animation types"""
        print("\n=== Animation Performance Test ===")
        
        # Create test image
        test_image = Image.new('RGB', (64, 64), color='red')
        base_array = np.array(test_image)
        
        animations = {
            'fade': self._test_fade_animation,
            'rotate': self._test_rotate_animation,
            'hue_shift': self._test_hue_animation
        }
        
        results = {}
        
        for name, func in animations.items():
            print(f"\nTesting {name} animation...")
            start_time = time.time()
            frames_generated = 0
            
            # Generate 30 frames
            for i in range(30):
                frame = func(base_array, i)
                frames_generated += 1
            
            duration = time.time() - start_time
            fps = frames_generated / duration
            
            print(f"{name}: {fps:.1f} FPS generation rate")
            results[name] = fps
        
        return results
    
    def _test_fade_animation(self, base_frame, i):
        """Test fade animation performance"""
        brightness = abs(np.sin(i * 0.1))
        return (base_frame * brightness).astype(np.uint8)
    
    def _test_rotate_animation(self, base_frame, i):
        """Test rotation animation performance"""
        import cv2
        height, width = base_frame.shape[:2]
        angle = i * 12  # 12 degrees per frame
        M = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
        return cv2.warpAffine(base_frame, M, (width, height))
    
    def _test_hue_animation(self, base_frame, i):
        """Test hue shift animation performance"""
        import cv2
        hsv = cv2.cvtColor(base_frame, cv2.COLOR_RGB2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + i * 6) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    async def test_system_resources(self, duration=30):
        """Monitor system resources during streaming"""
        print(f"\n=== System Resource Test ({duration}s) ===")
        client = VideoStreamClient(self.host, self.port)
        
        try:
            await client.connect()
            
            # Create test frame
            frame = np.random.randint(0, 255, 
                (client.matrix_height, client.matrix_width, 3), dtype=np.uint8)
            
            # Monitor resources while streaming
            process = psutil.Process()
            cpu_samples = []
            memory_samples = []
            
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration:
                # Send frame
                await client.send_frame(frame)
                frame_count += 1
                
                # Sample resources every 10 frames
                if frame_count % 10 == 0:
                    cpu_samples.append(process.cpu_percent())
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                
                await asyncio.sleep(0.033)  # ~30 FPS
            
            # Calculate results
            avg_cpu = statistics.mean(cpu_samples[1:])  # Skip first sample
            avg_memory = statistics.mean(memory_samples)
            max_memory = max(memory_samples)
            
            print(f"Frames sent: {frame_count}")
            print(f"Avg CPU usage: {avg_cpu:.1f}%")
            print(f"Avg memory usage: {avg_memory:.1f}MB")
            print(f"Peak memory usage: {max_memory:.1f}MB")
            
            self.results['cpu_usage'] = cpu_samples
            self.results['memory_usage'] = memory_samples
            
            await client.disconnect()
            
        except Exception as e:
            print(f"Error: {e}")
    
    async def run_all_tests(self):
        """Run all performance tests"""
        print("=== Piomatter WebSocket Performance Tests ===")
        print(f"Server: {self.host}:{self.port}")
        
        # Test different target frame rates
        for fps in [10, 30, 60]:
            await self.test_sustained_fps(duration=5, target_fps=fps)
        
        # Test burst performance
        await self.test_burst_performance(burst_size=100)
        
        # Test frame size impact
        await self.test_frame_size_impact()
        
        # Test animation performance
        await self.test_animation_performance()
        
        # Test system resources
        await self.test_system_resources(duration=10)
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("PERFORMANCE TEST SUMMARY")
        print("="*50)
        
        if self.results['fps_tests']:
            print("\nFPS Test Results:")
            for test in self.results['fps_tests']:
                efficiency = (test['actual_fps'] / test['target_fps']) * 100
                print(f"  {test['target_fps']} FPS target: "
                      f"{test['actual_fps']:.1f} actual ({efficiency:.0f}% efficiency)")
        
        if self.results['cpu_usage']:
            print(f"\nResource Usage:")
            print(f"  Avg CPU: {statistics.mean(self.results['cpu_usage'][1:]):.1f}%")
            print(f"  Avg Memory: {statistics.mean(self.results['memory_usage']):.1f}MB")


async def main():
    parser = argparse.ArgumentParser(description="Performance test for Piomatter WebSocket")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=9002, help="Server port")
    
    args = parser.parse_args()
    
    test = PerformanceTest(args.host, args.port)
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())