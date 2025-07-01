cmake_minimum_required(VERSION 3.12)

project(piomatter_simple_server C CXX)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 20)

find_package(Threads REQUIRED)

add_compile_options(-Wall -g3 -O2)

add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/protomatter.pio.h
    COMMAND ../../venv/bin/python ../assemble.py ../protomatter.pio ${CMAKE_CURRENT_BINARY_DIR}/protomatter.pio.h
    DEPENDS ../assemble.py ../protomatter.pio
)

add_executable(simple_server
    ../simple_websocket_server.cpp
    ../piolib/piolib.c
    ../piolib/pio_rp1.c
    ${CMAKE_CURRENT_BINARY_DIR}/protomatter.pio.h
)

target_include_directories(simple_server PRIVATE 
    ../include 
    ../piolib/include
    ${CMAKE_CURRENT_BINARY_DIR}
)

target_link_libraries(simple_server 
    ${CMAKE_THREAD_LIBS_INIT}
    pthread
)