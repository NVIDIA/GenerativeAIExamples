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

set -e

cwd=$(pwd)

echo "Installing/Building flexric"
cd $cwd/flexric/build && rm -rf *
cd $cwd/flexric && mkdir -p build && cd build \
    && cmake .. -DXAPP_C_INSTALL=TRUE -DE2AP_VERSION="E2AP_V2" \
        -DCMAKE_C_FLAGS="-Wa,--noexecstack" \
    && make -j8 && make install 
cd $cwd

echo "Installing/Building openairinterface5g"
cd ./openairinterface5g/ && source ./oaienv && source ./cmake_targets/tools/build_helper && install_asn1c_from_source
cd $cwd

echo "Starting FlexRIC RIC..."
stdbuf -oL ./flexric/build/examples/ric/nearRT-RIC > logs/RIC.log 2>&1 &
RIC_PID=$!
sleep 2

echo "Starting gNodeB..."
cd ./openairinterface5g/
source ./oaienv
./cmake_targets/ran_build/build/nr-softmodem -O ran-conf/gnb.conf --sa --rfsim -E --gNBs.[0].min_rxtxtime 6 > ../logs/gNodeB.log 2>&1 &
GNB_PID=$!
cd ..

echo "Setting initial bandwidth allocation to 50/50..."
./change_rc_slice.sh 50 50

echo "Starting UE1..."
./multi_ue.sh -c1 -e &
sleep 5
ip netns exec ue1 bash -c 'LD_LIBRARY_PATH=. ./openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem --rfsimulator.serveraddr 10.201.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O ran-conf/ue_1.conf -E' > logs/UE1.log 2>&1 &

echo "Starting UE2..."
./multi_ue.sh -c3 -e &
sleep 5
ip netns exec ue3 bash -c 'LD_LIBRARY_PATH=. ./openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem --rfsimulator.serveraddr 10.203.1.100 -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa -O ran-conf/ue_2.conf -E' > logs/UE2.log 2>&1 &

echo "Starting iperf servers..."
docker exec -t oai-ext-dn iperf3 -s -p 5201 > logs/docker_iperfserver1.log 2>&1 &
docker exec -t oai-ext-dn iperf3 -s -p 5202 > logs/docker_iperfserver2.log 2>&1 &

echo "Starting traffic generators..."
stdbuf -oL ./traffic_generator_ue1.sh > logs/traffic_generator_ue1.log 2>&1 &
stdbuf -oL ./traffic_generator_ue2.sh > logs/traffic_generator_ue2.log 2>&1 &

echo "Starting monitoring processes..."
python3 ./monitor_script_1.py > logs/monitor_script_1.log 2>&1 &
python3 ./monitor_script_2.py > logs/monitor_script_2.log 2>&1 &

echo "5G Lab setup complete. FlexRIC RIC PID: $RIC_PID, gNodeB PID: $GNB_PID"
echo "Press Ctrl+C to terminate the lab."
while true; do sleep 60; done
