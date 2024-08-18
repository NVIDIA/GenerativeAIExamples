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


# Download attu source to build container

SCRIPT_HOME=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ATTU_ROOT=$SCRIPT_HOME/attu

git clone https://github.com/zilliztech/attu.git $ATTU_ROOT
cd $ATTU_ROOT
git checkout -b streaming-ingest-branch c42d59716a72c10033822358dbdd622c69b156fd
