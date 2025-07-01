#!/bin/bash

# Build script for Piomatter WebSocket server

echo "Building Piomatter WebSocket server..."

# Install websocketpp if not present
if [ ! -d "/usr/include/websocketpp" ]; then
    echo "WebSocketPP not found. Please install it:"
    echo "  sudo apt-get install libwebsocketpp-dev"
    echo "  or"
    echo "  git clone https://github.com/zaphoyd/websocketpp.git"
    echo "  sudo cp -r websocketpp/websocketpp /usr/include/"
    exit 1
fi

# Check for boost headers
if [ ! -f "/usr/include/boost/version.hpp" ]; then
    echo "Boost not found. Please install it:"
    echo "  sudo apt-get install libboost-all-dev"
    exit 1
fi

# Create build directory
mkdir -p build_websocket
cd build_websocket

# Configure with CMake using the websocket CMakeLists 
cp ../CMakeLists.txt.websocket ./CMakeLists.txt
cmake -DCMAKE_BUILD_TYPE=Release .

# Build
make -j$(nproc)

if [ $? -eq 0 ]; then
    echo "Build successful! Executable: build_websocket/websocket_server"
    echo ""
    echo "To run the server:"
    echo "  sudo ./build_websocket/websocket_server [port]"
    echo ""
    echo "To test with the Python client:"
    echo "  python3 ../video_stream_client.py --test"
else
    echo "Build failed!"
    exit 1
fi