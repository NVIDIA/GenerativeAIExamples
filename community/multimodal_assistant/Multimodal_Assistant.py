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

import random
import os
import base64
import datetime
import argparse
import pandas as pd
from PIL import Image
from io import BytesIO

import streamlit as st
import streamlit_analytics
from streamlit_feedback import streamlit_feedback

from bot_config.utils import get_config
from utils.memory import init_memory, get_summary, add_history_to_memory
from guardrails.fact_check import fact_check
from llm.llm_client import LLMClient
from retriever.embedder import NVIDIAEmbedders, HuggingFaceEmbeders
from retriever.vector import MilvusVectorClient, QdrantClient
from retriever.retriever import Retriever
from utils.feedback import feedback_kwargs

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage

llm_client = LLMClient("mistralai/mixtral-8x7b-instruct-v0.1")

# Start the analytics service (using browser.usageStats)
streamlit_analytics.start_tracking()

# get the config from the command line, or set a default
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help = "Provide a chatbot config to run the deployment")

st.set_page_config(
        page_title = "Multimodal RAG Assistant",
        page_icon = ":speech_balloon:",
        layout = "wide",
)

@st.cache_data()
def load_config(cfg_arg):
    try:
        config = get_config(os.path.join("bot_config", cfg_arg + ".config"))
        return config
    except Exception as e:
        print("Error loading config:", e)
        return None

args = vars(parser.parse_args())
cfg_arg = args["config"]

# Initialize session state variables if not already present

if 'prompt_value' not in st.session_state:
    st.session_state['prompt_value'] = None

if cfg_arg and "config" not in st.session_state:
    st.session_state.config = load_config(cfg_arg)

if "config" not in st.session_state:
    st.session_state.config = load_config("multimodal")
    print(st.session_state.config)

if "messages" not in st.session_state:
    st.session_state.messages = [
            {"role": "assistant", "content": "Ask me a question!"}
        ]
if "sources" not in st.session_state:
    st.session_state.sources = []

if "image_query" not in st.session_state:
    st.session_state.image_query = ""

if "queried" not in st.session_state:
    st.session_state.queried = False

if "memory" not in st.session_state:
    st.session_state.memory = init_memory(llm_client.llm, st.session_state.config['summary_prompt'])
memory = st.session_state.memory


with st.sidebar:
    prev_cfg = st.session_state.config
    try:
        defaultidx = [["multimodal"]].index(st.session_state.config["name"].lower())
    except:
        defaultidx = 0
    st.header("Bot Configuration")
    cfg_name = st.selectbox("Select a configuration/type of bot.", (["multimodal"]), index=defaultidx)
    st.session_state.config = get_config(os.path.join("bot_config", cfg_name+".config"))
    config = get_config(os.path.join("bot_config", cfg_name+".config"))
    if st.session_state.config != prev_cfg:
        st.experimental_rerun()

    st.success("Select an experience above.")

    st.header("Image Input Query")

    # with st.form("my-form", clear_on_submit=True):
    uploaded_file = st.file_uploader("Upload an image (JPG/JPEG/PNG) along with a text input:", accept_multiple_files = False)
    #    submitted = st.form_submit_button("UPLOAD!")

    if uploaded_file and st.session_state.image_query == "":
        st.success("Image loaded for multimodal RAG Q&A.")
        st.session_state.image_query = os.path.join("/tmp/", uploaded_file.name)
        with open(st.session_state.image_query,"wb") as f:
            f.write(uploaded_file.read())

        with st.spinner("Getting image description using NeVA"):
            neva = LLMClient("ai-neva-22b")
            image = Image.open(st.session_state.image_query).convert("RGB")
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=20) # Quality = 20 is a workaround (WAR)
            b64_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
            res = neva.multimodal_invoke(b64_string, creativity = 0, quality = 9, complexity = 0, verbosity = 9)
            st.session_state.image_query = res.content

    if not uploaded_file:
        st.session_state.image_query = ""

# Page title
st.header(config["page_title"])
st.markdown(config["instructions"])

# init the vector client
if "vector_client" not in st.session_state or st.session_state.vector_client.collection_name != config["core_docs_directory_name"]:
    try:
        st.session_state.vector_client = MilvusVectorClient(hostname="localhost", port="19530", collection_name=config["core_docs_directory_name"])
    except Exception as e:
        st.write(f"Failed to connect to Milvus vector DB, exception: {e}. Please follow steps to initialize the vector DB, or upload documents to the knowledge base and add them to the vector DB.")
        st.stop()
# init the embedder
if "query_embedder" not in st.session_state:
    st.session_state.query_embedder = NVIDIAEmbedders(name="ai-embed-qa-4", type="query")
# init the retriever
if "retriever" not in st.session_state:
    st.session_state.retriever = Retriever(embedder=st.session_state.query_embedder , vector_client=st.session_state.vector_client)
retriever = st.session_state.retriever

messages = st.session_state.messages

for n, msg in enumerate(messages):
    st.chat_message(msg["role"]).write(msg["content"])
    if msg["role"] == "assistant" and n > 1:
        with st.chat_message("assistant"):
            ctr = 0
            for key in st.session_state.sources.keys():
                ctr += 1
                with st.expander(os.path.basename(key)):
                    source = st.session_state.sources[key]
                    if "source" in source["doc_metadata"]:
                        source_str = source["doc_metadata"]["source"]
                        if "page" in source_str and "block" in source_str:
                            download_path = source_str.split("page")[0].strip("-")+".pdf"
                            file_name = os.path.basename(download_path)
                            try:
                                f = open(download_path, 'rb').read()
                                st.download_button("Download now", f, key=download_path+str(n)+str(ctr), file_name=file_name)
                            except:
                                st.write("failed to provide download for this file: ", file_name)
                        elif "ppt" in source_str:
                            ppt_path = os.path.basename(source_str).replace('.pptx', '.pdf').replace('.ppt', '.pdf')
                            download_path = os.path.join("vectorstore/ppt_references", ppt_path)
                            file_name = os.path.basename(download_path)
                            f = open(download_path, "rb").read()
                            st.download_button("Download now", f, key=download_path+str(n)+str(ctr), file_name=file_name)
                        else:
                            download_path = source["doc_metadata"]["image"]
                            file_name = os.path.basename(download_path)
                            try:
                                f = open(download_path, 'rb').read()
                                st.download_button("Download now", f, key=download_path+str(n)+str(ctr), file_name=file_name)
                            except Exception as e:
                                print("failed to provide download for ", file_name)
                                print(f"Exception: {e}")
                    if "type" in source["doc_metadata"]:
                        if source["doc_metadata"]["type"] == "table":
                            # get the pandas table and show in Streamlit
                            df = pd.read_excel(source["doc_metadata"]["dataframe"])
                            st.write(df)
                            image = Image.open(source["doc_metadata"]["image"])
                            st.image(image, caption = os.path.basename(source["doc_metadata"]["source"]))
                        elif source["doc_metadata"]["type"] == "image":
                            image = Image.open(source["doc_metadata"]["image"])
                            st.image(image, caption = os.path.basename(source["doc_metadata"]["source"]))
                        else:
                            st.write(source["doc_content"])
                    else:
                        st.write(source["doc_content"])

        feedback_key = f"feedback_{int(n/2)}"

        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = None
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Please provide feedback by clicking one of these icons:**")
        with col2:
            streamlit_feedback(**feedback_kwargs, args=[messages[-2]["content"].strip(), messages[-1]["content"].strip()], key=feedback_key, align="flex-start")

# Check if the topic has changed
if st.session_state['prompt_value'] == None:
    prompt_value = "Hi, what can you help me with?"
    st.session_state["prompt_value"] = prompt_value

colx, coly = st.columns([1,20])

placeholder = st.empty()
with placeholder:
    with st.form("chat-form", clear_on_submit=True):
        instr = 'Hi there! Enter what you want to let me know here.'
        col1, col2 = st.columns([20,2])
        with col1:
            prompt_value = st.session_state["prompt_value"]
            prompt = st.text_input(
                    instr,
                    value=prompt_value,
                    placeholder=instr,
                    label_visibility='collapsed'
                )
        with col2:
            submitted = st.form_submit_button("Chat")
    if submitted and len(prompt) > 0:
        placeholder.empty()
        st.session_state['prompt_value'] = None

if len(prompt) > 0 and submitted == True:
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.image_query:
        prompt = f"\nI have uploaded an image with the following description: {st.session_state.image_query}" + "Here is the question: " + prompt
    transformed_query = {"text": prompt}
    messages.append({"role": "user", "content": transformed_query["text"]})

    with st.spinner("Obtaining references from documents..."):
        BASE_DIR = os.path.abspath("vectorstore")
        CORE_DIR = os.path.join(BASE_DIR, config["core_docs_directory_name"])
        context, sources = retriever.get_relevant_docs(transformed_query["text"])
        st.session_state.sources = sources
        augmented_prompt = "Relevant documents:" + context + "\n\n[[QUESTION]]\n\n" + transformed_query["text"] #+ "\n" + config["footer"]
        system_prompt = config["header"]
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = llm_client.chat_with_prompt(system_prompt, augmented_prompt)
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response:
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    print(response)
    add_history_to_memory(memory, transformed_query["text"], full_response)
    with st.spinner("Running fact checking/guardrails..."):
        full_response += "\n\nFact Check result: "
        res = fact_check(context, transformed_query["text"], full_response)
        for response in res:
            full_response += response
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    with st.chat_message("assistant"):
        messages.append(
                {"role": "assistant", "content": full_response}
        )
        st.write(full_response)
        st.experimental_rerun()
elif len(messages) > 1:
    summary_placeholder = st.empty()
    summary_button = summary_placeholder.button("Click to see summary")
    if summary_button:
        with st.chat_message("assistant"):
            summary_placeholder.empty()
            st.markdown(get_summary(memory))

streamlit_analytics.stop_tracking()
