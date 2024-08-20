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
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

def app():
    st.title("Visualize the Knowledge Graph!")
    st.subheader("Load a knowledge graph GraphML file from your system.")
    st.write("If you used the previous step, it will be saved on your system as ```knowledge_graph.graphml```")
    
    components.iframe(
        src="https://gephi.org/gephi-lite/",
        height=800,
        scrolling=True,
    )

if __name__ == "__main__":
    app()
