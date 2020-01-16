cmake_minimum_required(VERSION 3.9)
project(hello_world)
set (CMAKE_CXX_STANDARD 14)
add_executable(hello_world.exe hello_world.cpp)
set_target_properties(
    hello_world.exe 
    PROPERTIES 
        OUTPUT_NAME "hello_world"
        SUFFIX ".exe"
)
install(TARGETS hello_world.exe DESTINATION ${PROJECT_SOURCE_DIR})