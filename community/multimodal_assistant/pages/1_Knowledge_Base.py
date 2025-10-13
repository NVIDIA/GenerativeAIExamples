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

import os
import streamlit as st
import time

from bot_config.utils import get_config
from vectorstore.vectorstore_updater import update_vectorstore
from retriever.embedder import NVIDIAEmbedders, HuggingFaceEmbeders
from retriever.vector import MilvusVectorClient

st.set_page_config(
        page_title="Knowledge Base",
        page_icon=":books:",
        layout="wide",
)

if "config" not in st.session_state:
    st.session_state.config = ""

with st.sidebar:
    prev_cfg = st.session_state.config
    try:
        defaultidx = [["multimodal"]].index(st.session_state.config["name"].lower())
    except:
        defaultidx = 0
    cfg_name = st.selectbox("Select a configuration/type of bot.", (["multimodal"]), index=defaultidx)
    st.session_state.config = get_config(os.path.join("bot_config", cfg_name+".config"))
    config = get_config(os.path.join("bot_config", cfg_name+".config"))
    if st.session_state.config != prev_cfg:
        st.experimental_rerun()

st.sidebar.success("Select an experience above.")

# init the embedder
if "document_embedder" not in st.session_state:
    st.session_state.document_embedder = NVIDIAEmbedders(name="ai-embed-qa-4", type="passage")
document_embedder = st.session_state.document_embedder
# init the vector client
if "vector_client" not in st.session_state or st.session_state.vector_client.collection_name != config["core_docs_directory_name"]:
    st.session_state.vector_client =  MilvusVectorClient(hostname="localhost", port="19530", collection_name=config["core_docs_directory_name"])
vector_client = st.session_state.vector_client

BASE_DIR = os.path.abspath("vectorstore")
CORE_DIR = os.path.join(BASE_DIR, config["core_docs_directory_name"])
if not os.path.exists(CORE_DIR):
    os.mkdir(CORE_DIR)
DOCS_DIR = os.path.join(CORE_DIR, "uploaded_docs")
os.makedirs(DOCS_DIR, exist_ok=True)

# File upload
st.subheader("Contribute to the {} Knowledge Base".format(config["name"]))
with st.form("my-form", clear_on_submit=True):
    uploaded_files = st.file_uploader("Upload a file to {}'s Knowledge Base:".format(config["name"]), accept_multiple_files = True)
    submitted = st.form_submit_button("UPLOAD!")

if uploaded_files and submitted:
    for uploaded_file in uploaded_files:
        st.success("File uploaded successfully!")
        with open(os.path.join(DOCS_DIR, uploaded_file.name),"wb") as f:
            f.write(uploaded_file.read())
            st.write("filename: ", uploaded_file.name)

st.divider()

# Retraining/vector DB creation

st.subheader("Re-train {} to use the new information you uploaded".format(config["name"]))
st.write("This section will rerun the information chunking and vector storage algorithms on all documents again. ONLY run if you have uploaded new documents! Note that this can take a minute or more, depending on the number of documents and the sizes.")
if st.button("Re-train {}".format(config["name"])):
    with st.status("[Step 1/4] Loading documents. Expand to see current status", expanded=False) as status:
        update_vectorstore(DOCS_DIR, vector_client, document_embedder, config["core_docs_directory_name"], status)
    st.success("Completed re-training. Now {} will use the updated documentation to answer questions!".format(config["name"]))
    st.rerun()
st.divider()

filelist = [file for root, dirs, files in os.walk(DOCS_DIR) for file in files]

st.subheader("View/Modify the current Knowledge Base")
# Create a dropdown for the file list
if len(filelist) > 0:
    selected_file = st.selectbox("The following files/documents are ingested and used as part of {}'s knowledge base. Select to download if you wish".format(config["name"]), filelist)

    file_path = os.path.join(DOCS_DIR, selected_file)
    with open(file_path, "rb") as file:
        col1, col2 = st.columns([1,1])
        file_bytes = file.read()
        with col2:
            st.download_button(
                label="Download File",
                data=file_bytes,
                file_name=selected_file,
                mime="application/octet-stream",
            )
        with col1:
            if st.button("Delete File"):
                st.session_state.delete_clicked = True

        if st.session_state.get("delete_clicked"):
            password = st.text_input('Are you sure? Please confirm the password to delete this file.', key='password_field')
            if password == "avfleetengineering":
                with st.spinner("Marking file for deletion"):
                    time.sleep(5)
                    os.remove(file_path)
                    st.success("File has been deleted!")
                    st.session_state.delete_clicked = False  # Reset delete_clicked for next time
else:
    st.warning("There are no documents avaible for retrieval. Please upload some documents for the chatbot to use!", icon="⚠️")
