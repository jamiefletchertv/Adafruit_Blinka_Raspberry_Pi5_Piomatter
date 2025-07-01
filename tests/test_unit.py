#!/usr/bin/env python3
"""
Unit tests for Piomatter WebSocket Video Streaming components
"""

import unittest
import numpy as np
from PIL import Image
import cv2
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_stream_client import VideoStreamClient


class TestImageProcessing(unittest.TestCase):
    """Test image processing functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = VideoStreamClient()
        # Simulate matrix dimensions
        self.client.matrix_width = 64
        self.client.matrix_height = 64
        
    def test_resize_frame_basic(self):
        """Test basic frame resizing"""
        # Create a test frame
        input_frame = np.ones((128, 128, 3), dtype=np.uint8) * 255
        
        # Resize it
        output_frame = self.client.resize_frame(input_frame)
        
        # Check dimensions
        self.assertEqual(output_frame.shape[0], self.client.matrix_height)
        self.assertEqual(output_frame.shape[1], self.client.matrix_width)
        self.assertEqual(output_frame.shape[2], 3)
        
    def test_resize_frame_aspect_ratio(self):
        """Test resizing with different aspect ratios"""
        # Wide image
        wide_frame = np.ones((100, 200, 3), dtype=np.uint8) * 128
        output = self.client.resize_frame(wide_frame)
        self.assertEqual(output.shape[:2], (64, 64))
        
        # Tall image
        tall_frame = np.ones((200, 100, 3), dtype=np.uint8) * 128
        output = self.client.resize_frame(tall_frame)
        self.assertEqual(output.shape[:2], (64, 64))
        
    def test_color_conversion(self):
        """Test BGR to RGB conversion in resize"""
        # Create BGR frame with distinct colors
        bgr_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        bgr_frame[:, :, 0] = 255  # Blue channel
        bgr_frame[:, :, 1] = 128  # Green channel
        bgr_frame[:, :, 2] = 64   # Red channel
        
        # Resize (which includes conversion)
        rgb_frame = self.client.resize_frame(bgr_frame)
        
        # Check that colors were swapped correctly
        # Original BGR (255, 128, 64) should become RGB (64, 128, 255)
        self.assertAlmostEqual(rgb_frame[32, 32, 0], 64, delta=5)
        self.assertAlmostEqual(rgb_frame[32, 32, 1], 128, delta=5)
        self.assertAlmostEqual(rgb_frame[32, 32, 2], 255, delta=5)


class TestFrameGeneration(unittest.TestCase):
    """Test frame generation for animations"""
    
    def test_gradient_generation(self):
        """Test gradient frame generation"""
        width, height = 64, 64
        
        # Create gradient
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for x in range(width):
            frame[:, x, 0] = int(255 * x / width)  # Red gradient
            
        # Check gradient values
        self.assertEqual(frame[0, 0, 0], 0)  # Start of gradient
        self.assertGreater(frame[0, width-1, 0], 250)  # End of gradient
        
    def test_hsv_color_generation(self):
        """Test HSV to RGB conversion for rainbow effects"""
        # Create HSV color - OpenCV uses H:0-179, S:0-255, V:0-255
        hsv = np.array([[[60, 255, 255]]], dtype=np.uint8)  # Green hue (60 degrees)
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        # Check it's greenish - OpenCV HSV->RGB may not give pure colors
        # Just verify we got a valid RGB conversion with reasonable values
        self.assertGreaterEqual(rgb[0, 0, 1], 200)  # Green channel should be dominant
        self.assertLessEqual(rgb[0, 0, 0], 100)     # Red should be low
        self.assertLessEqual(rgb[0, 0, 2], 100)     # Blue should be low


class TestAnimationLogic(unittest.TestCase):
    """Test animation calculations"""
    
    def test_fade_calculation(self):
        """Test fade in/out brightness calculation"""
        # Test various points in the sine wave
        brightness = abs(np.sin(0))
        self.assertAlmostEqual(brightness, 0, places=2)
        
        brightness = abs(np.sin(np.pi/2))
        self.assertAlmostEqual(brightness, 1, places=2)
        
        brightness = abs(np.sin(np.pi))
        self.assertAlmostEqual(brightness, 0, places=2)
        
    def test_rotation_matrix(self):
        """Test rotation matrix generation"""
        width, height = 64, 64
        angle = 45
        
        # Create rotation matrix
        M = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
        
        # Check matrix shape
        self.assertEqual(M.shape, (2, 3))
        
        # Test rotation of center point (should stay same)
        center = np.array([width/2, height/2, 1])
        rotated = M @ center
        self.assertAlmostEqual(rotated[0], width/2, places=1)
        self.assertAlmostEqual(rotated[1], height/2, places=1)
        
    def test_wave_distortion(self):
        """Test wave distortion calculation"""
        height = 64
        
        # Test wave shift calculation
        for y in range(height):
            shift = int(5 * np.sin(y * 0.2))
            self.assertLessEqual(abs(shift), 5)


class TestProtocolFormatting(unittest.TestCase):
    """Test protocol message formatting"""
    
    def test_matrix_info_parsing(self):
        """Test parsing matrix dimension info"""
        message = "MATRIX:128x64"
        
        # Parse dimensions
        if message.startswith("MATRIX:"):
            dims = message[7:].split("x")
            width = int(dims[0])
            height = int(dims[1])
            
            self.assertEqual(width, 128)
            self.assertEqual(height, 64)
            
    def test_command_formatting(self):
        """Test command message formatting"""
        commands = ["CLEAR", "INFO", "BRIGHTNESS:50"]
        
        for cmd in commands:
            formatted = f"CMD:{cmd}"
            self.assertTrue(formatted.startswith("CMD:"))
            self.assertEqual(formatted[4:], cmd)
            
    def test_frame_size_calculation(self):
        """Test frame size calculations"""
        width, height = 64, 64
        
        # RGB frame size
        expected_size = width * height * 3
        self.assertEqual(expected_size, 12288)
        
        # Create frame and check size
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        self.assertEqual(frame.nbytes, expected_size)


class TestLogoHandling(unittest.TestCase):
    """Test logo/image handling"""
    
    def setUp(self):
        """Create test images"""
        self.test_dir = "/tmp/piomatter_test"
        os.makedirs(self.test_dir, exist_ok=True)
        
    def test_png_with_transparency(self):
        """Test handling PNG with alpha channel"""
        # Create RGBA image
        img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
        
        # Add fully transparent pixels
        for x in range(50):
            for y in range(50):
                img.putpixel((x, y), (0, 0, 0, 0))
                
        path = os.path.join(self.test_dir, "test_alpha.png")
        img.save(path)
        
        # Load and check
        loaded = Image.open(path)
        self.assertEqual(loaded.mode, 'RGBA')
        
        # Test alpha compositing
        background = Image.new('RGBA', loaded.size, (0, 0, 0, 255))
        composite = Image.alpha_composite(background, loaded)
        composite_rgb = composite.convert('RGB')
        
        # Check composited result
        self.assertEqual(composite_rgb.mode, 'RGB')
        
        # Clean up
        os.remove(path)
        
    def test_image_formats(self):
        """Test different image format support"""
        formats = [
            ('test.jpg', 'RGB'),
            ('test.png', 'RGBA'),
            ('test.bmp', 'RGB')
        ]
        
        for filename, expected_mode in formats:
            # Create test image
            if expected_mode == 'RGBA':
                img = Image.new('RGBA', (50, 50), (255, 0, 0, 255))
            else:
                img = Image.new('RGB', (50, 50), (255, 0, 0))
                
            path = os.path.join(self.test_dir, filename)
            img.save(path)
            
            # Check it exists and is readable
            self.assertTrue(os.path.exists(path))
            loaded = Image.open(path)
            self.assertIsNotNone(loaded)
            
            # Clean up
            os.remove(path)
    
    def tearDown(self):
        """Clean up test directory"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)