set -x
mkdir examples/build
cd examples/build
cmake ..
cmake --build .
cd ../..
find . -name "*.exe"
