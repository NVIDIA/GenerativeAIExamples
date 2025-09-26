#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Script to build OpenAirInterface5G and FlexRIC

# Exit on any error
set -e

# Define base directory
BASE_DIR="$(pwd)"

# Function to check if a command succeeded
check_status() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed. Exiting."
        exit 1
    fi
}

echo "Starting OpenAirInterface5G build process..."

# Navigate to openairinterface5g directory
cd "$BASE_DIR/openairinterface5g" || {
    echo "Error: Cannot find openairinterface5g directory"
    exit 1
}

# Navigate to cmake_targets
cd cmake_targets || {
    echo "Error: Cannot find cmake_targets directory"
    exit 1
}

# Install dependencies
echo "Installing dependencies..."
./build_oai -I
check_status "Dependency installation"

# Build OAI with specified options
echo "Building OAI with SIMU, gNB, nrUE, and E2 support..."
./build_oai -c -C -w SIMU --gNB --nrUE --build-e2 --ninja
check_status "OAI build"

echo "OpenAirInterface5G build completed."

# Build FlexRIC
echo "Starting FlexRIC build process..."
cd "$BASE_DIR/flexric" || {
    echo "Error: Cannot find flexric directory"
    exit 1
}

# Create and enter build directory
mkdir -p build
cd build || {
    echo "Error: Cannot create or enter build directory"
    exit 1
}

# Configure with CMake
echo "Configuring FlexRIC with CMake..."
cmake -DXAPP_MULTILANGUAGE=OFF ..
check_status "CMake configuration"

# Compile with make
echo "Compiling FlexRIC..."
make -j8
check_status "FlexRIC compilation"

# Install
echo "Installing FlexRIC..."
make install
check_status "FlexRIC installation"

echo "Build and installation completed successfully!"