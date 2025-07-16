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

#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>

#include "piomatter/piomatter.h"

using websocketpp::connection_hdl;
using websocketpp::lib::placeholders::_1;
using websocketpp::lib::placeholders::_2;
using websocketpp::lib::bind;

typedef websocketpp::server<websocketpp::config::asio> server;
typedef server::message_ptr message_ptr;

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
    interrupt_received = true;
}

class PiomatterWebSocketServer {
private:
    static constexpr int width = 192;
    static constexpr int height = 64;
    
    server ws_server_;
    std::set<connection_hdl, std::owner_less<connection_hdl>> connections_;
    std::mutex frame_mutex_;
    std::condition_variable frame_cv_;
    std::queue<std::vector<uint8_t>> frame_queue_;
    std::unique_ptr<piomatter::piomatter_base> matrix_;
    std::thread render_thread_;
    std::vector<uint32_t> framebuffer_;
    
public:
    PiomatterWebSocketServer() : framebuffer_(width * height, 0) {
        // Initialize the Piomatter matrix for 3x2 64x32 panels (192x64 total) - independent rows
        // Physical layout: [3][2][1] top row, [4][5][6] bottom row - no serpentine
        piomatter::matrix_geometry geometry(
            192,    // pixels_across (3 panels x 64 wide)
            5,      // row_select_lines (64-pixel height = 2^6, so 5 address lines)
            10,     // bit_depth  
            0,      // swizzle
            width,  // tile_width (192)
            height, // tile_height (64)
            false,  // serpentine disabled - independent rows
            piomatter::orientation_normal
        );
        
        // Create the matrix object
        auto fb_span = std::span<const uint32_t>(framebuffer_.data(), framebuffer_.size());
        matrix_ = std::make_unique<piomatter::piomatter<>>(fb_span, geometry);
        
        // Set up websocket server
        ws_server_.set_access_channels(websocketpp::log::alevel::all);
        ws_server_.clear_access_channels(websocketpp::log::alevel::frame_payload);
        
        ws_server_.init_asio();
        
        ws_server_.set_open_handler(bind(&PiomatterWebSocketServer::on_open, this, ::_1));
        ws_server_.set_close_handler(bind(&PiomatterWebSocketServer::on_close, this, ::_1));
        ws_server_.set_message_handler(bind(&PiomatterWebSocketServer::on_message, this, ::_1, ::_2));
    }
    
    void on_open(connection_hdl hdl) {
        connections_.insert(hdl);
        std::cout << "Client connected. Matrix size: " << width << "x" << height << std::endl;
        
        // Send matrix dimensions to client
        std::string info = "MATRIX:" + std::to_string(width) + "x" + std::to_string(height);
        ws_server_.send(hdl, info, websocketpp::frame::opcode::text);
    }
    
    void on_close(connection_hdl hdl) {
        connections_.erase(hdl);
        std::cout << "Client disconnected" << std::endl;
    }
    
    void on_message(connection_hdl hdl, message_ptr msg) {
        const std::string& payload = msg->get_payload();
        
        // Check for control messages
        if (payload.substr(0, 4) == "CMD:") {
            handle_command(hdl, payload.substr(4));
            return;
        }
        
        // Otherwise treat as frame data (RGB888)
        if (payload.size() == width * height * 3) {
            std::vector<uint8_t> frame_data(payload.begin(), payload.end());
            
            {
                std::lock_guard<std::mutex> lock(frame_mutex_);
                // Keep only latest frames to prevent lag
                while (frame_queue_.size() > 2) {
                    frame_queue_.pop();
                }
                frame_queue_.push(std::move(frame_data));
            }
            frame_cv_.notify_one();
        } else {
            std::cerr << "Invalid frame size: " << payload.size() 
                      << " (expected " << width * height * 3 << ")" << std::endl;
        }
    }
    
    void handle_command(connection_hdl hdl, const std::string& cmd) {
        if (cmd == "CLEAR") {
            std::fill(framebuffer_.begin(), framebuffer_.end(), 0);
            matrix_->show();
        } else if (cmd.substr(0, 10) == "BRIGHTNESS") {
            // Handle brightness commands if needed
            // The Piomatter library may handle this differently
        } else if (cmd == "INFO") {
            // Send current FPS info
            std::string info = "FPS:" + std::to_string(matrix_->fps);
            ws_server_.send(hdl, info, websocketpp::frame::opcode::text);
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
            for (int y = 0; y < height; ++y) {
                for (int x = 0; x < width; ++x) {
                    int idx = (y * width + x) * 3;
                    uint32_t r = frame_data[idx];
                    uint32_t g = frame_data[idx + 1];
                    uint32_t b = frame_data[idx + 2];
                    framebuffer_[y * width + x] = (r << 16) | (g << 8) | b;
                }
            }
            
            // Update the display
            matrix_->show();
        }
    }
    
    void run(uint16_t port) {
        // Start render thread
        render_thread_ = std::thread(&PiomatterWebSocketServer::render_frames, this);
        
        // Start websocket server
        ws_server_.listen(port);
        ws_server_.start_accept();
        
        std::cout << "WebSocket server listening on port " << port << std::endl;
        std::cout << "Matrix dimensions: " << width << "x" << height << std::endl;
        std::cout << "Ready to receive video frames..." << std::endl;
        
        ws_server_.run();
        
        // Clean up
        if (render_thread_.joinable()) {
            render_thread_.join();
        }
    }
    
    void stop() {
        ws_server_.stop();
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
        PiomatterWebSocketServer server;
        server.run(port);
    } catch (websocketpp::exception const & e) {
        std::cerr << "WebSocket error: " << e.what() << std::endl;
        return 1;
    } catch (std::exception const & e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}