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
import time
from taipy.gui import notify
import taipy.gui.builder as tgb 

import argparse

from bot_config.utils import get_config
from vectorstore.vectorstore_updater import update_vectorstore
from retriever.embedder import NVIDIAEmbedders, HuggingFaceEmbeders
from retriever.vector import MilvusVectorClient
from retriever.retriever import Retriever

def load_config(cfg_arg):
    try:
        config = get_config(os.path.join("bot_config", cfg_arg + ".config"))
        return config
    except Exception as e:
        print("Error loading config:", e)
        return None


# get the config from the command line, or set a default
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help = "Provide a chatbot config to run the deployment")


args = vars(parser.parse_args())
cfg_arg = args["config"]

# Initialize session state variables if not already present
prompt_value = None

mode = cfg_arg if cfg_arg else "multimodal"

config = load_config(mode)
print(config)

# try:
#     defaultidx = [["multimodal"]].index(config["name"].lower())
# except:
#     defaultidx = 0

document_embedder = NVIDIAEmbedders(name="nvolveqa_40k", type="passage")

try:
    vector_client = MilvusVectorClient(hostname="localhost", port="19530", collection_name=config["core_docs_directory_name"])
except Exception as e:
    vector_client = None
    raise(Exception(f"Failed to connect to Milvus vector DB, exception: {e}. Please follow steps to initialize the vector DB, or upload documents to the knowledge base and add them to the vector DB."))

BASE_DIR = os.path.abspath("vectorstore")
CORE_DIR = os.path.join(BASE_DIR, config["core_docs_directory_name"])
if not os.path.exists(CORE_DIR):
    os.mkdir(CORE_DIR)
DOCS_DIR = os.path.join(CORE_DIR, "uploaded_docs")
os.makedirs(DOCS_DIR, exist_ok=True)

uploaded_files = []
selected_file = None
filelist = [file for root, dirs, files in os.walk(DOCS_DIR) for file in files]


def change_config(state):
    state.config = get_config(os.path.join("bot_config", state.cfg_name+".config"))
    notify(state, "success", "Config successfuly changed!")

    state.vector_client = MilvusVectorClient(hostname="localhost", port="19530", collection_name=state.config["core_docs_directory_name"])
    notify(state, "success", "Vector database changed!")

    state.query_embedder = NVIDIAEmbedders(name="nvolveqa_40k", type="query")
    notify(state, "success", "Query embedder updated!")

    state.retriever = Retriever(embedder=state.query_embedder , vector_client=state.vector_client)
    notify(state, "success", "Retriever updated!")


def on_files_upload(state):
    for uploaded_file in state.uploaded_files:
        notify(state, "i", "Uploading files...")
        with open(uploaded_file, "r") as f_read:
            with open(os.path.join(DOCS_DIR, f_read.name),"wb") as f_write:
                f_write.write(f_read.read())
                notify(state, "s", "{f_read.name} written!")

def retrain(state):
    update_vectorstore(DOCS_DIR,  state.vector_client,  state.document_embedder, state.config["core_docs_directory_name"])

def delete_file(state):
    file_path = os.path.join(DOCS_DIR, state.selected_file)
    os.remove(file_path)
    notify(state, "s", "Deleted Successfully!")



with tgb.Page() as knowledge_base:
    with tgb.layout("3 7"):
        with tgb.part("sidebar"):
            tgb.selector(value="{mode}", lov=["multimodal"], dropdown=True, class_name="fullwidth", on_change=change_config)

        with tgb.part():
            tgb.text("Contribute to the Multimodal Assistant Knowledge Base", class_name="h1")

            tgb.file_selector(content="{uploaded_files}", on_action=on_files_upload, label="Upload a file to Knowledge Base:")

            tgb.text("Re-train model to use the new information you uploaded", class_name="h1")
            tgb.text("This section will rerun the information chunking and vector storage algorithms on all documents again. ONLY run if you have uploaded new documents! Note that this can take a minute or more, depending on the number of documents and the sizes.")

            tgb.button("Re-train", on_action=retrain)

            tgb.text("View/Modify the current Knowledge Base", class_name="h1")
            tgb.selector(value="{selected_file}", lov="{filelist}", label="Files in Knowledge Base")

            with tgb.layout("1 1"):
                tgb.file_download("Download file", active='{len(filelist)>0}')

                tgb.button("Delete", on_action=delete_file, class_name="plain error", active='{len(filelist)>0}')