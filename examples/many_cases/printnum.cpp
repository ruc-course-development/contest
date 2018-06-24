// compile me with:
// Visual Studio:
//   cl /EHsc printnum.cpp /Femain.exe
//
// GCC g++:
//   g++ printnum.cpp -o main.exe
//
#include <iostream>
int main()
{
   int i = 0;
   std::cin >> i;
   std::cout << i << std::endl;
}