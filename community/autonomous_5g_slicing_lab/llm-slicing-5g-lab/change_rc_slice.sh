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

# 1 = slice 1 Ratio
# 2 = slice 2 Ratio

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

if [ -n "$1" ] &&  [ -n "$2" ]; then

  sum=$1+$2
  echo $sum
  #if [ "$sum" -gt 100 ]; then
  #  echo "The sum of both ratios must not be greater than 100"
  #  exit()
  #fi

  export SLICE1_RATIO=$1
  export SLICE2_RATIO=$2
else
  echo "You did not specify the slicing ratios, using default 80:20"
fi

./flexric/build/examples/xApp/c/ctrl/xapp_rc_slice_dynamic
