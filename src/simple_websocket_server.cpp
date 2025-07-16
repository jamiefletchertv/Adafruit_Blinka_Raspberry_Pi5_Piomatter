#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <vector>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <signal.h>
#include <iostream>
#include <set>
#include <span>
#include <optional>

// Simple TCP socket implementation instead of WebSocketPP
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/select.h>

#include "piomatter/piomatter.h"

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
    interrupt_received = true;
}

class SimpleTcpServer {
private:
    static constexpr int width = 192;  // 3x 64x64 panels chained horizontally
    static constexpr int height = 64;
    
    int server_fd_;
    std::set<int> client_sockets_;
    std::mutex clients_mutex_;
    std::mutex frame_mutex_;
    std::condition_variable frame_cv_;
    std::queue<std::vector<uint8_t>> frame_queue_;
    std::unique_ptr<piomatter::piomatter_base> matrix_;
    std::thread server_thread_;
    std::thread render_thread_;
    std::vector<uint32_t> framebuffer_;
    
public:
    SimpleTcpServer() : framebuffer_(width * height, 0), server_fd_(-1) {
        // Initialize the Piomatter matrix for 3x2 64x32 panels (192x64 total) - independent rows
        // Physical layout: [3][2][1] top row, [4][5][6] bottom row - no serpentine
        piomatter::matrix_geometry geometry(
            192,    // pixels_across (3 panels x 64 wide)
            5,      // row_select_lines (64-pixel height = 2^6, so 5 address lines)
            5,      // bit_depth (reduced to 5 for maximum refresh speed - 32 color levels)  
            2,      // temporal dither for even more speed
            width,  // tile_width (192)
            height, // tile_height (64)
            false,  // serpentine disabled - independent rows
            piomatter::orientation_r180
        );
        
        // Create the matrix object - use standard Adafruit pinout for correct colors
        auto fb_span = std::span<const uint32_t>(framebuffer_.data(), framebuffer_.size());
        matrix_ = std::make_unique<piomatter::piomatter<piomatter::adafruit_matrix_bonnet_pinout>>(fb_span, geometry);
    }
    
    bool start_server(uint16_t port) {
        // Create socket
        server_fd_ = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd_ == -1) {
            std::cerr << "Failed to create socket" << std::endl;
            return false;
        }
        
        // Set socket options
        int opt = 1;
        if (setsockopt(server_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
            std::cerr << "Failed to set socket options" << std::endl;
            close(server_fd_);
            return false;
        }
        
        // Bind to port
        struct sockaddr_in address;
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(port);
        
        if (bind(server_fd_, (struct sockaddr *)&address, sizeof(address)) < 0) {
            std::cerr << "Failed to bind to port " << port << std::endl;
            close(server_fd_);
            return false;
        }
        
        // Listen for connections
        if (listen(server_fd_, 10) < 0) {
            std::cerr << "Failed to listen on socket" << std::endl;
            close(server_fd_);
            return false;
        }
        
        std::cout << "Simple TCP server listening on port " << port << std::endl;
        std::cout << "Matrix dimensions: " << width << "x" << height << std::endl;
        std::cout << "Expected frame size: " << width * height * 3 << " bytes (RGB888)" << std::endl;
        std::cout << "Ready to receive video frames..." << std::endl;
        
        return true;
    }
    
    void handle_client(int client_socket) {
        std::cout << "Client connected" << std::endl;
        
        // Send matrix info as simple text
        std::string info = "MATRIX:" + std::to_string(width) + "x" + std::to_string(height) + "\n";
        send(client_socket, info.c_str(), info.length(), 0);
        
        std::vector<uint8_t> buffer(width * height * 3 + 1024); // Extra space for commands
        
        while (!interrupt_received) {
            ssize_t bytes_received = recv(client_socket, buffer.data(), buffer.size(), 0);
            
            if (bytes_received <= 0) {
                break; // Client disconnected or error
            }
            
            // Check for text commands
            if (bytes_received < width * height * 3) {
                std::string command(buffer.data(), buffer.data() + bytes_received);
                if (command.find("CMD:CLEAR") != std::string::npos) {
                    std::fill(framebuffer_.begin(), framebuffer_.end(), 0);
                    matrix_->show();
                    continue;
                }
                // Ignore other small packets (probably partial data)
                continue;
            }
            
            // Process frame data (exactly the right size)
            if (bytes_received == width * height * 3) {
                std::vector<uint8_t> frame_data(buffer.data(), buffer.data() + bytes_received);
                
                // Debug: Sample some pixels to see what we're receiving
                static int frame_count = 0;
                if (frame_count++ % 30 == 0) { // Log every 30th frame
                    std::cout << "Frame " << frame_count << " sample pixels:" << std::endl;
                    for (int i = 0; i < 5; i++) {
                        int idx = (i * width * height / 5) * 3;
                        if (idx + 2 < frame_data.size()) {
                            std::cout << "  Pixel " << i << ": R=" << (int)frame_data[idx] 
                                      << " G=" << (int)frame_data[idx+1] 
                                      << " B=" << (int)frame_data[idx+2] << std::endl;
                        }
                    }
                }
                
                {
                    std::lock_guard<std::mutex> lock(frame_mutex_);
                    // Keep only latest frames to prevent lag
                    while (frame_queue_.size() > 2) {
                        frame_queue_.pop();
                    }
                    frame_queue_.push(std::move(frame_data));
                }
                frame_cv_.notify_one();
            }
        }
        
        std::cout << "Client disconnected" << std::endl;
    }
    
    void accept_clients() {
        fd_set readfds;
        struct timeval timeout;
        
        while (!interrupt_received) {
            FD_ZERO(&readfds);
            FD_SET(server_fd_, &readfds);
            
            int max_fd = server_fd_;
            
            // Add existing client sockets to the set
            {
                std::lock_guard<std::mutex> lock(clients_mutex_);
                for (int client_fd : client_sockets_) {
                    FD_SET(client_fd, &readfds);
                    if (client_fd > max_fd) {
                        max_fd = client_fd;
                    }
                }
            }
            
            timeout.tv_sec = 1;
            timeout.tv_usec = 0;
            
            int activity = select(max_fd + 1, &readfds, nullptr, nullptr, &timeout);
            
            if (activity < 0) {
                if (!interrupt_received) {
                    std::cerr << "Select error" << std::endl;
                }
                break;
            }
            
            // Check for new connections
            if (FD_ISSET(server_fd_, &readfds)) {
                struct sockaddr_in address;
                socklen_t addrlen = sizeof(address);
                int new_socket = accept(server_fd_, (struct sockaddr *)&address, &addrlen);
                
                if (new_socket >= 0) {
                    {
                        std::lock_guard<std::mutex> lock(clients_mutex_);
                        client_sockets_.insert(new_socket);
                    }
                    
                    // Handle client in a separate thread
                    std::thread([this, new_socket]() {
                        handle_client(new_socket);
                        {
                            std::lock_guard<std::mutex> lock(clients_mutex_);
                            client_sockets_.erase(new_socket);
                        }
                        close(new_socket);
                    }).detach();
                }
            }
        }
    }
    
    void render_frames() {
        while (!interrupt_received) {
            std::unique_lock<std::mutex> lock(frame_mutex_);
            frame_cv_.wait(lock, [this] { return !frame_queue_.empty() || interrupt_received; });
            
            if (interrupt_received) break;
            
            auto frame_data = std::move(frame_queue_.front());
            frame_queue_.pop();
            lock.unlock();
            
            // Convert RGB888 to RGB888 packed in uint32_t for Piomatter
            static int render_count = 0;
            bool debug_this_frame = (render_count++ % 30 == 0);
            
            for (int y = 0; y < height; ++y) {
                for (int x = 0; x < width; ++x) {
                    int idx = (y * width + x) * 3;
                    uint32_t r = frame_data[idx];
                    uint32_t g = frame_data[idx + 1];
                    uint32_t b = frame_data[idx + 2];
                    uint32_t packed = (r << 16) | (g << 8) | b;
                    framebuffer_[y * width + x] = packed;
                    
                    // Debug: Log center pixel
                    if (debug_this_frame && x == width/2 && y == height/2) {
                        std::cout << "Center pixel RGB(" << r << "," << g << "," << b 
                                  << ") packed=0x" << std::hex << packed << std::dec << std::endl;
                    }
                }
            }
            
            // Update the display
            matrix_->show();
        }
    }
    
    void run(uint16_t port) {
        if (!start_server(port)) {
            return;
        }
        
        // Start render thread
        render_thread_ = std::thread(&SimpleTcpServer::render_frames, this);
        
        // Start server thread
        server_thread_ = std::thread(&SimpleTcpServer::accept_clients, this);
        
        // Wait for threads
        if (server_thread_.joinable()) {
            server_thread_.join();
        }
        
        if (render_thread_.joinable()) {
            render_thread_.join();
        }
        
        // Clean up
        if (server_fd_ >= 0) {
            close(server_fd_);
        }
    }
};

int main(int argc, char *argv[]) {
    // Port argument
    uint16_t port = 9002;
    if (argc > 1) {
        port = std::stoi(argv[1]);
    }
    
    signal(SIGTERM, InterruptHandler);
    signal(SIGINT, InterruptHandler);
    
    try {
        SimpleTcpServer server;
        server.run(port);
    } catch (std::exception const & e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}