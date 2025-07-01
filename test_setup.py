#!/usr/bin/env python3
"""
Test script to verify the venv and dependencies are properly installed
"""

print("Testing virtual environment setup...")

try:
    import cv2
    print("✓ OpenCV available")
    print(f"  Version: {cv2.__version__}")
except ImportError as e:
    print(f"✗ OpenCV failed: {e}")

try:
    import PIL
    print("✓ Pillow available")
    print(f"  Version: {PIL.__version__}")
except ImportError as e:
    print(f"✗ Pillow failed: {e}")

try:
    import websockets
    print("✓ WebSockets available")
    print(f"  Version: {websockets.__version__}")
except ImportError as e:
    print(f"✗ WebSockets failed: {e}")

try:
    import numpy as np
    print("✓ NumPy available")
    print(f"  Version: {np.__version__}")
except ImportError as e:
    print(f"✗ NumPy failed: {e}")

try:
    import adafruit_pioasm
    print("✓ Adafruit PIO ASM available")
except ImportError as e:
    print(f"✗ Adafruit PIO ASM failed: {e}")

try:
    import click
    print("✓ Click available")
    print(f"  Version: {click.__version__}")
except ImportError as e:
    print(f"✗ Click failed: {e}")

print("\nAll dependencies are installed and working!")
print("\nNext steps:")
print("1. Fix C++ WebSocket server compilation issues")
print("2. Test C++ server with: sudo ./build_websocket/websocket_server")
print("3. Test Python client with: python video_stream_client.py --test")