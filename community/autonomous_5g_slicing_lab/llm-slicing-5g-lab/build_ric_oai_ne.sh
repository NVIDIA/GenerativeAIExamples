#!/bin/bash

set -e  # Exit immediately if any command fails

# Save the initial directory
INITIAL_DIR=$(pwd)

# Step 0: Install necessary compilers (gcc-12, g++-12)
echo ">>> Updating apt and installing gcc-12, g++-12..."
sudo apt update
sudo apt install -y gcc-12 g++-12
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 100

# Step 1: Clone and build openairinterface5g
echo ">>> Cloning and building openairinterface5g..."
git clone https://gitlab.eurecom.fr/oai/openairinterface5g
cd openairinterface5g || { echo "Failed to enter openairinterface5g directory"; exit 1; }
git checkout slicing-spring-of-code
cd cmake_targets || { echo "Failed to enter cmake_targets"; exit 1; }

# Build openairinterface5g
./build_oai -I
./build_oai -c -C -w SIMU --gNB --nrUE --build-e2 --ninja

# Step 2: Go back to the initial directory
cd "$INITIAL_DIR" || { echo "Failed to return to initial directory"; exit 1; }

# Step 3: Clone and build flexric
echo ">>> Cloning and building flexric..."
git clone https://gitlab.eurecom.fr/mosaic5g/flexric
cd flexric || { echo "Failed to enter flexric directory"; exit 1; }
git checkout slicing-spring-of-code

# Step 4: Copy necessary files
cp "$INITIAL_DIR/xapp_rc_slice_dynamic.c" examples/xApp/c/ctrl/ || { echo "Failed to copy xapp_rc_slice_dynamic.c"; exit 1; }
cp "$INITIAL_DIR/CMakeLists.txt" examples/xApp/c/ctrl/ || { echo "Failed to copy CMakeLists.txt"; exit 1; }

# Step 5: Build flexric
mkdir -p build && cd build
cmake -DXAPP_MULTILANGUAGE=OFF ..
make -j8
sudo make install

echo ">>> All steps completed successfully!"
