# Makefile for Piomatter WebSocket Video Streaming System

# Configuration
CXX = g++
CC = gcc
PYTHON = python3
CMAKE = cmake
CXXFLAGS = -std=c++20 -Wall -O2
LOGO_ASSET = /home/jamie/repos/visualiser/assets/images/psybercell-logo.png
SERVER_PORT = 9002
HOST ?= localhost

# Directories
SRC_DIR = src
BUILD_DIR = $(SRC_DIR)/build_simple
WEBSOCKET_BUILD_DIR = $(SRC_DIR)/build_websocket
TEST_DIR = tests
VENV_DIR = venv

# Targets
.PHONY: all build clean test deploy install-deps run-server run-client animate-logo integration-test help test-setup status perf-test build-websocket test-10s test-png test-colors test-smpte test-animated-logo test-new-features test-video

# Default target
all: install-deps build test

# Help target
help:
	@echo "Piomatter Video Streaming System - Make Targets"
	@echo "=============================================="
	@echo "  make all              - Install deps, build, and test"
	@echo "  make install-deps     - Install all dependencies"
	@echo "  make build            - Build the Simple TCP server (working)"
	@echo "  make build-websocket  - Build WebSocket server (has compatibility issues)"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make test             - Run all tests"
	@echo "  make test-setup       - Test virtual environment setup"
	@echo "  make status           - Check build and dependency status"
	@echo "  make run-server       - Run the TCP server (requires sudo)"
	@echo "  make run-client       - Run test pattern on client"
	@echo "  make animate-logo     - Animate the PsyberCell logo"
	@echo "  make integration-test - Run full integration tests"
	@echo "  make perf-test        - Run performance tests"
	@echo "  make test-10s         - Run 10-second test with server and client"
	@echo "  make test-smpte       - Test SMPTE color bars patterns"
	@echo "  make test-animated-logo - Test animated PsyberCell logo effects"
	@echo "  make test-new-features - Test both new features comprehensively"
	@echo "  make test-video       - Test Big Buck Bunny video playback (Pi 5 only)"
	@echo "  make test-video-client - Test video client on macOS (connect to remote Pi 5)"
	@echo "  make deploy           - Deploy to Raspberry Pi (set PI_HOST env var)"
	@echo ""
	@echo "Environment Variables:"
	@echo "  HOST     - TCP server host (default: localhost)"
	@echo "  PI_HOST  - Raspberry Pi hostname for deployment"

# Install dependencies
install-deps: install-system-deps install-python-deps

install-system-deps:
	@echo "Checking system dependencies..."
	@which cmake > /dev/null || (echo "Please install cmake: sudo apt-get install cmake" && false)
	@which g++ > /dev/null || (echo "Please install g++: sudo apt-get install g++" && false)
	@echo "Checking for websocketpp..."
	@if [ ! -d "/usr/include/websocketpp" ]; then \
		echo "WebSocketPP not found. Please install:"; \
		echo "  sudo apt-get install libwebsocketpp-dev"; \
		echo "  or manually install from https://github.com/zaphoyd/websocketpp"; \
		exit 1; \
	fi
	@echo "Checking for boost..."
	@if [ ! -f "/usr/include/boost/version.hpp" ]; then \
		echo "Boost not found. Please install:"; \
		echo "  sudo apt-get install libboost-all-dev"; \
		exit 1; \
	fi
	@echo "System dependencies OK"

install-python-deps:
	@echo "Installing Python dependencies..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@. $(VENV_DIR)/bin/activate && pip install --upgrade pip
	@. $(VENV_DIR)/bin/activate && pip install -r requirements_video.txt
	@. $(VENV_DIR)/bin/activate && pip install adafruit-circuitpython-pioasm click
	@echo "Python dependencies installed"

# Build the C++ server (Simple TCP by default)
build: $(BUILD_DIR)/simple_server

$(BUILD_DIR)/simple_server: $(SRC_DIR)/simple_websocket_server.cpp install-python-deps
	@echo "Building Simple TCP server..."
	@cd $(SRC_DIR) && chmod +x build_simple.sh
	@cd $(SRC_DIR) && ./build_simple.sh
	@echo "Build complete: $(BUILD_DIR)/simple_server"

# Build WebSocket server (has compatibility issues)
build-websocket: $(WEBSOCKET_BUILD_DIR)/websocket_server

$(WEBSOCKET_BUILD_DIR)/websocket_server: $(SRC_DIR)/websocket_server.cpp install-python-deps
	@echo "Building WebSocket server (may fail due to WebSocketPP compatibility)..."
	@cd $(SRC_DIR) && chmod +x build_websocket.sh
	@cd $(SRC_DIR) && ./build_websocket.sh
	@echo "Build complete: $(WEBSOCKET_BUILD_DIR)/websocket_server"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -rf $(WEBSOCKET_BUILD_DIR)
	@rm -rf $(TEST_DIR)/__pycache__
	@rm -rf *.pyc
	@echo "Clean complete"

# Run the server (requires sudo on Pi)
run-server: build
	@echo "Starting Simple TCP server on port $(SERVER_PORT)..."
	@if [ -e "/dev/pio0" ]; then \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT); \
	else \
		echo "Warning: /dev/pio0 not found - running in test mode"; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT); \
	fi

# Run client with test pattern
run-client:
	@echo "Running test pattern client..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) simple_tcp_client.py --test --host $(HOST) --port $(SERVER_PORT)

# Animate the PsyberCell logo
animate-logo:
	@echo "Animating PsyberCell logo..."
	@if [ ! -f "$(LOGO_ASSET)" ]; then \
		echo "Error: Logo not found at $(LOGO_ASSET)"; \
		exit 1; \
	fi
	@. $(VENV_DIR)/bin/activate && $(PYTHON) simple_tcp_client.py "$(LOGO_ASSET)" --animate --host $(HOST) --port $(SERVER_PORT)

# Create test directory and files
$(TEST_DIR):
	@mkdir -p $(TEST_DIR)

# Test setup and dependencies
test-setup: install-python-deps
	@echo "Testing virtual environment setup..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) tests/test_setup.py

# Unit tests
test: test-setup unit-test integration-test test-new-features

unit-test: build $(TEST_DIR)
	@echo "Running unit tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) -m pytest $(TEST_DIR)/test_unit.py -v || true

# Integration tests
integration-test: $(TEST_DIR)
	@echo "Running integration tests..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) $(TEST_DIR)/test_integration.py

# Deploy to Raspberry Pi
deploy:
	@if [ -z "$(PI_HOST)" ]; then \
		echo "Error: Please set PI_HOST environment variable"; \
		echo "Example: make deploy PI_HOST=raspberrypi.local"; \
		exit 1; \
	fi
	@echo "Deploying to $(PI_HOST)..."
	@ssh $(PI_HOST) "mkdir -p ~/piomatter_websocket"
	@rsync -av --exclude=$(BUILD_DIR) --exclude=$(VENV_DIR) --exclude=__pycache__ \
		$(SRC_DIR)/ video_stream_client.py requirements_video.txt Makefile \
		$(PI_HOST):~/piomatter_websocket/
	@echo "Deployment complete. On the Pi, run:"
	@echo "  cd ~/piomatter_websocket && make build && make run-server"

# Development targets
watch-logo:
	@echo "Continuously displaying logo (press Ctrl+C to stop)..."
	@while true; do \
		. $(VENV_DIR)/bin/activate && $(PYTHON) video_stream_client.py "$(LOGO_ASSET)" \
			--host $(HOST) --port $(SERVER_PORT) --no-wait || break; \
		sleep 1; \
	done

# Performance test
perf-test: build
	@echo "Running performance test..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) $(TEST_DIR)/test_performance.py --host $(HOST) --port $(SERVER_PORT)

# Check build status and dependencies
status:
	@echo "=== Piomatter WebSocket Status ==="
	@echo "Virtual Environment:"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "  ✓ venv exists"; \
		. $(VENV_DIR)/bin/activate && $(PYTHON) test_setup.py 2>/dev/null | head -20; \
	else \
		echo "  ✗ venv missing - run 'make install-deps'"; \
	fi
	@echo ""
	@echo "Build Status:"
	@if [ -f "$(BUILD_DIR)/simple_server" ]; then \
		echo "  ✓ Simple TCP server built"; \
		echo "  Size: $$(du -h $(BUILD_DIR)/simple_server | cut -f1)"; \
	else \
		echo "  ✗ Simple TCP server not built - run 'make build'"; \
	fi
	@if [ -f "$(WEBSOCKET_BUILD_DIR)/websocket_server" ]; then \
		echo "  ✓ WebSocket server also built"; \
	else \
		echo "  ⚠ WebSocket server not built (has compatibility issues)"; \
	fi
	@echo ""
	@echo "System Dependencies:"
	@if [ -f "/usr/include/boost/version.hpp" ]; then \
		echo "  ✓ Boost installed"; \
	else \
		echo "  ✗ Boost missing"; \
	fi
	@if [ -d "/usr/include/websocketpp" ]; then \
		echo "  ✓ WebSocketPP installed"; \
	else \
		echo "  ✗ WebSocketPP missing"; \
	fi
	@echo ""

# 10-second test with automatic cleanup
test-20s: build
	@echo "Starting 20-second test with server and client..."
	@bash -c ' \
	set -e; \
	cleanup() { \
		echo "Cleaning up..."; \
		[ -n "$$SERVER_PID" ] && kill -TERM $$SERVER_PID 2>/dev/null || true; \
		[ -n "$$CLIENT_PID" ] && kill -TERM $$CLIENT_PID 2>/dev/null || true; \
		sleep 2; \
		[ -n "$$SERVER_PID" ] && kill -KILL $$SERVER_PID 2>/dev/null || true; \
		[ -n "$$CLIENT_PID" ] && kill -KILL $$CLIENT_PID 2>/dev/null || true; \
		pkill -f "simple_server" 2>/dev/null || true; \
		pkill -f "simple_tcp_client.py" 2>/dev/null || true; \
		if [ -e "/dev/pio0" ]; then \
			sudo pkill -f "simple_server" 2>/dev/null || true; \
		fi; \
		echo "Cleanup complete!"; \
	}; \
	trap cleanup EXIT; \
	if [ -e "/dev/pio0" ]; then \
		echo "Pi 5 detected - starting server with sudo..."; \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		SERVER_PID=$$!; \
	else \
		echo "Non-Pi 5 system - starting server in test mode..."; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		SERVER_PID=$$!; \
	fi; \
	echo "Server started with PID $$SERVER_PID"; \
	sleep 3; \
	echo "Starting client test pattern..."; \
	. $(VENV_DIR)/bin/activate && $(PYTHON) simple_tcp_client.py --test --host $(HOST) --port $(SERVER_PORT) & \
	CLIENT_PID=$$!; \
	echo "Client started with PID $$CLIENT_PID"; \
	echo "Running for 20 seconds..."; \
	sleep 20; \
	echo "Test complete!"; \
	'

# Test with PNG asset and monitor refresh rate
test-png: build
	@echo "Testing PNG asset with corrected RGB format..."
	@if [ ! -f "$(LOGO_ASSET)" ]; then \
		echo "Error: PNG asset not found at $(LOGO_ASSET)"; \
		exit 1; \
	fi
	@echo "Cleaning any existing processes..."
	@sudo killall -9 simple_server 2>/dev/null || true
	@sleep 1
	@if [ -e "/dev/pio0" ]; then \
		echo "Starting Pi 5 server..."; \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing PNG asset: $(LOGO_ASSET)"; \
		. $(VENV_DIR)/bin/activate && timeout 15 $(PYTHON) simple_tcp_client.py "$(LOGO_ASSET)" --host $(HOST) --port $(SERVER_PORT) --animate; \
		echo "Stopping server..."; \
		sudo killall -9 simple_server 2>/dev/null || true; \
	else \
		echo "Starting test server..."; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing PNG asset: $(LOGO_ASSET)"; \
		. $(VENV_DIR)/bin/activate && timeout 15 $(PYTHON) simple_tcp_client.py "$(LOGO_ASSET)" --host $(HOST) --port $(SERVER_PORT) --animate; \
		echo "Stopping server..."; \
		killall -9 simple_server 2>/dev/null || true; \
	fi
	@echo "PNG test complete!"

# Test basic colors to verify RGB format
test-colors: build
	@echo "Testing basic color patterns..."
	@echo "Cleaning any existing processes..."
	@sudo killall -9 simple_server 2>/dev/null || true
	@sleep 1
	@if [ -e "/dev/pio0" ]; then \
		echo "Starting Pi 5 server..."; \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing color patterns..."; \
		. $(VENV_DIR)/bin/activate && timeout 15 $(PYTHON) simple_tcp_client.py --test --host $(HOST) --port $(SERVER_PORT); \
		echo "Stopping server..."; \
		sudo killall -9 simple_server 2>/dev/null || true; \
	else \
		echo "Starting test server..."; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing color patterns..."; \
		. $(VENV_DIR)/bin/activate && timeout 15 $(PYTHON) simple_tcp_client.py --test --host $(HOST) --port $(SERVER_PORT); \
		echo "Stopping server..."; \
		killall -9 simple_server 2>/dev/null || true; \
	fi
	@echo "Color test complete!"

# Test SMPTE color bars patterns
test-smpte: build
	@echo "Testing SMPTE color bars patterns..."
	@echo "Cleaning any existing processes..."
	@sudo killall -9 simple_server 2>/dev/null || true
	@sleep 1
	@if [ -e "/dev/pio0" ]; then \
		echo "Starting Pi 5 server..."; \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing SMPTE patterns..."; \
		. $(VENV_DIR)/bin/activate && timeout 20 $(PYTHON) examples/smpte_bars.py --host $(HOST) --port $(SERVER_PORT) || true; \
		echo "Stopping server..."; \
		sudo killall -9 simple_server 2>/dev/null || true; \
	else \
		echo "Starting test server..."; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing SMPTE patterns..."; \
		. $(VENV_DIR)/bin/activate && timeout 20 $(PYTHON) examples/smpte_bars.py --host $(HOST) --port $(SERVER_PORT) || true; \
		echo "Stopping server..."; \
		killall -9 simple_server 2>/dev/null || true; \
	fi
	@echo "SMPTE test complete!"

# Test animated PsyberCell logo effects  
test-animated-logo: build
	@echo "Testing animated PsyberCell logo effects..."
	@echo "Cleaning any existing processes..."
	@sudo killall -9 simple_server 2>/dev/null || true
	@sleep 1
	@if [ -e "/dev/pio0" ]; then \
		echo "Starting Pi 5 server..."; \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing animated logo..."; \
		. $(VENV_DIR)/bin/activate && timeout 30 $(PYTHON) examples/animate_psybercell_logo.py || true; \
		echo "Stopping server..."; \
		sudo killall -9 simple_server 2>/dev/null || true; \
	else \
		echo "Starting test server..."; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing animated logo..."; \
		. $(VENV_DIR)/bin/activate && timeout 30 $(PYTHON) examples/animate_psybercell_logo.py || true; \
		echo "Stopping server..."; \
		killall -9 simple_server 2>/dev/null || true; \
	fi
	@echo "Animated logo test complete!"

# Test both new features comprehensively
test-new-features: build
	@echo "Testing both new features comprehensively..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) tests/test_new_features.py

# Test Big Buck Bunny video playback
test-video:
	@echo "Testing Big Buck Bunny video playback..."
	@if [ ! -f "$(BUILD_DIR)/simple_server" ]; then \
		echo "Error: Server not built. Run 'make build' first."; \
		exit 1; \
	fi
	@if [ ! -f "big-buck-bunny_600k.mp4" ]; then \
		echo "Error: Video file not found: big-buck-bunny_600k.mp4"; \
		exit 1; \
	fi
	@echo "Cleaning any existing processes..."
	@sudo killall -9 simple_server 2>/dev/null || true
	@sleep 1
	@if [ -e "/dev/pio0" ]; then \
		echo "Starting Pi 5 server..."; \
		sudo $(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing video playback (60 seconds)..."; \
		. $(VENV_DIR)/bin/activate && timeout 60 $(PYTHON) tests/test_video_playback.py || true; \
		echo "Stopping server..."; \
		sudo killall -9 simple_server 2>/dev/null || true; \
	else \
		echo "Starting test server..."; \
		$(BUILD_DIR)/simple_server $(SERVER_PORT) & \
		sleep 3; \
		echo "Testing video playback (30 seconds)..."; \
		. $(VENV_DIR)/bin/activate && timeout 30 $(PYTHON) tests/test_video_playback.py || true; \
		echo "Stopping server..."; \
		killall -9 simple_server 2>/dev/null || true; \
	fi
	@echo "Video test complete!"

# Test video client on macOS (no server build required)
test-video-client:
	@echo "Testing video client on macOS..."
	@if [ ! -f "big-buck-bunny_600k.mp4" ]; then \
		echo "Error: Video file not found: big-buck-bunny_600k.mp4"; \
		exit 1; \
	fi
	@echo "Starting video client for remote server..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) test_video_client_macos.py --host $(HOST) --port $(SERVER_PORT)

# Test patterns client on macOS (no server build required)
test-patterns-client:
	@echo "Testing patterns client on macOS..."
	@echo "Starting test patterns client for remote server..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) test_patterns_client_macos.py --host $(HOST) --port $(SERVER_PORT)

# Test SMPTE bars client on macOS (no server build required)
test-smpte-client:
	@echo "Testing SMPTE bars client on macOS..."
	@echo "Starting SMPTE client for remote server..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) smpte_bars_client_macos.py --host $(HOST) --port $(SERVER_PORT)

# Test animated logo client on macOS (no server build required)
test-logo-client:
	@echo "Testing animated logo client on macOS..."
	@echo "Starting logo animation client for remote server..."
	@. $(VENV_DIR)/bin/activate && $(PYTHON) animated_logo_client_macos.py --host $(HOST) --port $(SERVER_PORT)

# Run all macOS client tests
test-all-clients: test-patterns-client test-smpte-client test-logo-client test-video-client

# Server management targets
server-start:
	@echo "Starting RGB matrix server..."
	@./server_manager.sh start $(SERVER_PORT)

server-stop:
	@echo "Stopping RGB matrix server..."
	@./server_manager.sh stop $(SERVER_PORT)

server-restart:
	@echo "Restarting RGB matrix server..."
	@./server_manager.sh restart $(SERVER_PORT)

server-status:
	@echo "Checking RGB matrix server status..."
	@./server_manager.sh status $(SERVER_PORT)

server-kill:
	@echo "Force killing RGB matrix server..."
	@./server_manager.sh kill $(SERVER_PORT)
