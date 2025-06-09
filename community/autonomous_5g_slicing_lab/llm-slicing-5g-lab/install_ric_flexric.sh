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

# Save the initial directory
INITIAL_DIR=$(pwd)

# Step 1: Clone and build openairinterface5g
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
make install

