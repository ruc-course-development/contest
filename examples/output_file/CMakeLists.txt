cmake_minimum_required(VERSION 3.9)
project(numbers)
set (CMAKE_CXX_STANDARD 14)
add_executable(numbers.exe numbers.cpp)
set_target_properties(
    numbers.exe 
    PROPERTIES 
        OUTPUT_NAME "numbers"
        SUFFIX ".exe"
)
install(TARGETS numbers.exe DESTINATION ${PROJECT_SOURCE_DIR})