#!/bin/bash

# Build script for Simple TCP server (no WebSocket dependencies)

echo "Building Simple TCP server..."

# Check for basic requirements
if ! which cmake > /dev/null; then
    echo "CMake not found. Please install it:"
    echo "  sudo apt-get install cmake"
    exit 1
fi

if ! which g++ > /dev/null; then
    echo "g++ not found. Please install it:"
    echo "  sudo apt-get install g++"
    exit 1
fi

# Create build directory
mkdir -p build_simple
cd build_simple

# Configure with CMake using the simple CMakeLists 
cp ../CMakeLists.txt.simple ./CMakeLists.txt
cmake -DCMAKE_BUILD_TYPE=Release .

# Build
make -j$(nproc)

if [ $? -eq 0 ]; then
    echo "Build successful! Executable: build_simple/simple_server"
    echo ""
    echo "To run the server:"
    echo "  sudo ./build_simple/simple_server [port]"
    echo ""
    echo "To test with the Python client:"
    echo "  python3 ../simple_tcp_client.py --test"
else
    echo "Build failed!"
    exit 1
fi