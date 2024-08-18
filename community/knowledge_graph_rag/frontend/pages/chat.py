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
import requests
import json
import time
import os

from dotenv import load_dotenv
load_dotenv()

# Get the backend URL from environment variables
BACKEND_URL = os.getenv("BACKEND_URL")

st.set_page_config(layout="wide")

st.title("Chat with your Knowledge Graph!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# Fetch available models from the backend
response = requests.get(f"{BACKEND_URL}/chat/get-models/")
if response.status_code == 200:
    available_models = response.json()["models"]
else:
    st.error("Error fetching models.")
    available_models = []

with st.sidebar:
    llm = st.selectbox("Choose an LLM", available_models, index=available_models.index("mistralai/mixtral-8x7b-instruct-v0.1") if "mistralai/mixtral-8x7b-instruct-v0.1" in available_models else 0)
    st.write("You selected: ", llm)

with st.sidebar:
    use_kg = st.checkbox("Use knowledge graph")

user_input = st.chat_input("Can you tell me how research helps users to solve problems?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Send the user input to the backend for processing
        response = requests.post(f"{BACKEND_URL}/chat/chat/", json={"user_input": user_input, "use_kg": use_kg, "model_id": llm})
        if response.status_code == 200:
            response_data = response.json()
            context = response_data.get("context", "")
            assistant_response = response_data.get("assistant_response", "")
            if "knowledge graph is currently unavailable" in assistant_response:
                st.error("The knowledge graph is currently unavailable. Please try again later.")
            else:
                for chunk in assistant_response.split(' '):
                    full_response += chunk + ' '
                    message_placeholder.markdown(full_response)
                    time.sleep(0.05)  #
        else:
            st.error("Error processing the chat request.")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
