#include <iostream>
#include <string>
int main()
{
    std::cout << "Hello! What is your name?\n";
    std::string name;
    std::cin >> name;
    std::cout << "Welcome to the world, " << name << "!\n";
}