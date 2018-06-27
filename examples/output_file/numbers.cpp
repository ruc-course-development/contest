#include <fstream>
int main(int argc, char **argv)
{
   std::ofstream file("sample.dat");
   for (int i = 0; i < std::atoi(argv[1]); ++i)
   {
       file << i << std::endl;
   }
}