set -x
mkdir examples/build
cd examples/build
cmake ..
cmake --build .
find . -name "*.exe"