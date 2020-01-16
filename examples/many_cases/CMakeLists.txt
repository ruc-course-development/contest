cmake_minimum_required(VERSION 3.9)
project(printnum)
set (CMAKE_CXX_STANDARD 14)
add_executable(printnum.exe printnum.cpp)
set_target_properties(
    printnum.exe 
    PROPERTIES 
        OUTPUT_NAME "printnum"
        SUFFIX ".exe"
)
install(TARGETS printnum.exe DESTINATION ${PROJECT_SOURCE_DIR})