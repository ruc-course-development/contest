set -x
mkdir examples/build
cd examples/build
cmake ..
cmake --build . --target install
cd ../..
pwd
find . -name "*.exe"
