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

import streamlit as st
import os
# make sure to export your NVIDIA AI Playground key as NVIDIA_API_KEY!

def check_env_var():
    if "NVIDIA_API_KEY" not in os.environ:
        st.error("Please export your NVIDIA_API_KEY from the NVIDIA AI Playground to continue with LLMs/Embedding Models!", icon="🚨")
        st.stop()   
    