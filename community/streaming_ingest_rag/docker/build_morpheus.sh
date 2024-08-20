#!/bin/bash

# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Download Morpheus source and build base morpheus container

SCRIPT_HOME=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
MORPHEUS_ROOT=$SCRIPT_HOME/morpheus

# Clone Morpheus github
git clone https://github.com/nv-morpheus/Morpheus.git $MORPHEUS_ROOT
cd $MORPHEUS_ROOT
git checkout -b streaming-ingest-branch aa8d42e79936bc7b2558682ca1197cedca8c7041
# Add tag to name container
git tag 24.03

git lfs install
python3 ./scripts/fetch_data.py fetch models
cp ../extras/all-MiniLM-L6-v2_config.pbtxt ./models/triton-model-repo/all-MiniLM-L6-v2/config.pbtxt

# Build container base image
./docker/build_container_release.sh

cd $SCRIPT_HOME
