// compile me with:
// Visual Studio:
//   cl /EHsc hello_world.cpp /Femain.exe
//
// GCC g++:
//   g++ hello_world.cpp -o main.exe
//
#include <iostream>
#include <string>
int main()
{
    std::cout << "Hello! What is your name?\n";
    std::string name;
    std::cin >> name;
    std::cout << "Welcome to the world, " << name << "!\n";
}