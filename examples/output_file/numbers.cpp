// compile me with:
// Visual Studio:
//   cl /EHsc numbers.cpp /Femain.exe
//
// GCC g++:
//   g++ numbers.cpp -o main.exe
//
#include <fstream>
int main(int argc, char **argv)
{
   std::ofstream file("sample.dat");
   for (int i = 0; i < std::atoi(argv[1]); ++i)
   {
       file << i << std::endl;
   }
}