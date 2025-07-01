#!/bin/bash
# Server process management script for Pi 5 RGB matrix server

PORT=${1:-9002}
SERVER_BINARY="./src/build_simple/simple_server"
SERVER_NAME="simple_server"

show_help() {
    echo "Pi 5 RGB Matrix Server Manager"
    echo "============================="
    echo "Usage: $0 [command] [port]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the server (default)"
    echo "  stop      - Stop the server"
    echo "  restart   - Restart the server"
    echo "  status    - Show server status"
    echo "  kill      - Force kill all server processes"
    echo "  help      - Show this help"
    echo ""
    echo "Port: Default is 9002"
    echo ""
    echo "Examples:"
    echo "  $0 start          # Start on port 9002"
    echo "  $0 start 9003     # Start on port 9003"
    echo "  $0 stop           # Stop server"
    echo "  $0 kill           # Force kill all servers"
}

check_server_binary() {
    if [ ! -f "$SERVER_BINARY" ]; then
        echo "❌ Server binary not found: $SERVER_BINARY"
        echo "💡 Run 'make build' first to compile the server"
        exit 1
    fi
}

get_server_pids() {
    # Find all processes with the server name
    pgrep -f "$SERVER_NAME" 2>/dev/null || true
}

get_port_pids() {
    # Find processes using the specific port
    lsof -ti:$PORT 2>/dev/null || true
}

start_server() {
    echo "🚀 Starting RGB Matrix Server on port $PORT..."
    
    check_server_binary
    
    # Check if server is already running on this port
    existing_pids=$(get_port_pids)
    if [ -n "$existing_pids" ]; then
        echo "⚠️  Port $PORT is already in use by PID(s): $existing_pids"
        echo "💡 Run '$0 stop' first, or use a different port"
        exit 1
    fi
    
    # Start server with proper permissions
    if [ -e "/dev/pio0" ]; then
        echo "🔧 Pi 5 detected - starting with sudo for PIO access..."
        sudo $SERVER_BINARY $PORT &
        SERVER_PID=$!
        echo "✅ Server started with PID $SERVER_PID (sudo)"
    else
        echo "🔧 Non-Pi 5 system - starting in test mode..."
        $SERVER_BINARY $PORT &
        SERVER_PID=$!
        echo "✅ Server started with PID $SERVER_PID"
    fi
    
    # Wait a moment and check if it's still running
    sleep 2
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "🎉 Server is running successfully on port $PORT"
        echo "📡 Clients can connect to: $(hostname -I | awk '{print $1}'):$PORT"
    else
        echo "❌ Server failed to start or crashed immediately"
        exit 1
    fi
}

stop_server() {
    echo "🛑 Stopping RGB Matrix Server..."
    
    # Find processes using the port
    port_pids=$(get_port_pids)
    server_pids=$(get_server_pids)
    
    # Combine and deduplicate PIDs
    all_pids=$(echo "$port_pids $server_pids" | tr ' ' '\n' | sort -u | tr '\n' ' ')
    
    if [ -z "$all_pids" ]; then
        echo "ℹ️  No server processes found"
        return 0
    fi
    
    echo "🔍 Found server PID(s): $all_pids"
    
    # Try graceful shutdown first
    for pid in $all_pids; do
        if kill -0 $pid 2>/dev/null; then
            echo "📤 Sending TERM signal to PID $pid..."
            sudo kill -TERM $pid 2>/dev/null || kill -TERM $pid 2>/dev/null
        fi
    done
    
    # Wait for graceful shutdown
    echo "⏳ Waiting for graceful shutdown..."
    sleep 3
    
    # Check if any processes are still running
    remaining_pids=""
    for pid in $all_pids; do
        if kill -0 $pid 2>/dev/null; then
            remaining_pids="$remaining_pids $pid"
        fi
    done
    
    # Force kill if necessary
    if [ -n "$remaining_pids" ]; then
        echo "💥 Force killing remaining processes: $remaining_pids"
        for pid in $remaining_pids; do
            sudo kill -KILL $pid 2>/dev/null || kill -KILL $pid 2>/dev/null
        done
        sleep 1
    fi
    
    # Final check
    final_pids=$(get_port_pids)
    if [ -z "$final_pids" ]; then
        echo "✅ Server stopped successfully"
    else
        echo "⚠️  Some processes may still be running: $final_pids"
    fi
}

force_kill() {
    echo "💥 Force killing ALL server processes..."
    
    # Kill by process name
    sudo pkill -KILL -f "$SERVER_NAME" 2>/dev/null || true
    pkill -KILL -f "$SERVER_NAME" 2>/dev/null || true
    
    # Kill by port
    port_pids=$(get_port_pids)
    if [ -n "$port_pids" ]; then
        echo "🔫 Killing processes on port $PORT: $port_pids"
        for pid in $port_pids; do
            sudo kill -KILL $pid 2>/dev/null || kill -KILL $pid 2>/dev/null
        done
    fi
    
    echo "✅ Force kill completed"
}

show_status() {
    echo "📊 RGB Matrix Server Status"
    echo "=========================="
    
    # Check server binary
    if [ -f "$SERVER_BINARY" ]; then
        echo "✅ Server binary: $SERVER_BINARY"
    else
        echo "❌ Server binary missing: $SERVER_BINARY"
    fi
    
    # Check Pi 5 PIO device
    if [ -e "/dev/pio0" ]; then
        echo "✅ Pi 5 PIO device: /dev/pio0"
    else
        echo "ℹ️  No Pi 5 PIO device (test mode only)"
    fi
    
    # Check running processes
    server_pids=$(get_server_pids)
    port_pids=$(get_port_pids)
    
    if [ -n "$server_pids" ]; then
        echo "🟢 Server processes running: $server_pids"
    else
        echo "🔴 No server processes found"
    fi
    
    if [ -n "$port_pids" ]; then
        echo "🟢 Port $PORT in use by PID(s): $port_pids"
    else
        echo "🔴 Port $PORT is free"
    fi
    
    # Show detailed process info
    echo ""
    echo "Detailed process information:"
    ps aux | grep -E "$SERVER_NAME|PID" | grep -v grep || echo "No server processes found"
}

# Main command handling
COMMAND=${1:-start}

case $COMMAND in
    start)
        if [ -n "$2" ]; then
            PORT=$2
        fi
        start_server
        ;;
    stop)
        if [ -n "$2" ]; then
            PORT=$2
        fi
        stop_server
        ;;
    restart)
        if [ -n "$2" ]; then
            PORT=$2
        fi
        stop_server
        sleep 2
        start_server
        ;;
    status)
        if [ -n "$2" ]; then
            PORT=$2
        fi
        show_status
        ;;
    kill)
        if [ -n "$2" ]; then
            PORT=$2
        fi
        force_kill
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac