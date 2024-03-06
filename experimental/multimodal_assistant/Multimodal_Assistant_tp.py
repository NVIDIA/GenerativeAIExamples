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
import pandas as pd
from PIL import Image
from io import BytesIO

# import streamlit as st
# import streamlit_analytics
# from streamlit_feedback import streamlit_feedback
import taipy.gui.builder as tgb
from taipy.gui import Gui, notify, State

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

from pages.Knowledge_Base_tp import *

llm_client = LLMClient("mixtral_8x7b")

# Start the analytics service (using browser.usageStats)
# streamlit_analytics.start_tracking()




image_files = []
messages = [{"role": "assistant", "content": "Ask me a question!"}]
sources = []
image_query = ""
queried = False
current_user_message = ""

try:
    vector_client = MilvusVectorClient(hostname="localhost", port="19530", collection_name=config["core_docs_directory_name"])
except Exception as e:
    vector_client = None
    raise(Exception(f"Failed to connect to Milvus vector DB, exception: {e}. Please follow steps to initialize the vector DB, or upload documents to the knowledge base and add them to the vector DB."))

memory = init_memory(llm_client.llm, config['summary_prompt'])
query_embedder = NVIDIAEmbedders(name="nvolveqa_40k", type="query")

retriever = Retriever(embedder=query_embedder , vector_client=vector_client)

prompt_value = "Hi, what can you help me with?"



def change_config(state):
    state.config = get_config(os.path.join("bot_config", state.cfg_name+".config"))
    notify(state, "success", "Config successfuly changed!")

    state.vector_client = MilvusVectorClient(hostname="localhost", port="19530", collection_name=state.config["core_docs_directory_name"])
    notify(state, "success", "Vector database changed!")

    state.query_embedder = NVIDIAEmbedders(name="nvolveqa_40k", type="query")
    notify(state, "success", "Query embedder updated!")

    state.retriever = Retriever(embedder=state.query_embedder , vector_client=state.vector_client)
    notify(state, "success", "Retriever updated!")


def on_images_upload(state):
    notify(state, "s", "Image loaded for multimodal RAG Q&A.")
    state.image_query = os.path.join("/tmp/", state.image_file.name)
    with open(state.image_query,"wb") as f:
        f.write(state.image_file.read())
        
    neva = LLMClient("neva_22b")
    image = Image.open(state.image_query).convert("RGB")
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=20) # Quality = 20 is a workaround (WAR)
    b64_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    res = neva.multimodal_invoke(b64_string, creativity = 0, quality = 9, complexity = 0, verbosity = 9)
    state.image_query = res.content



def update_context(state: State) -> None:
    """
    Update the context with the user's message and the AI's response.

    Args:
        - state: The current state of the app.
    """
    state.context += f"Human: \n {state.current_user_message}\n\n AI:"
    answer = ...#request(state, state.context).replace("\n", "")
    state.context += answer
    state.selected_row = [len(state.conversation["Conversation"]) + 1]
    return answer


def send_message(state: State) -> None:
    """
    Send the user's message to the API and update the context.

    Args:
        - state: The current state of the app.
    """

    if state.image_query:
        state.current_user_message = f"\nI have uploaded an image with the following description: {state.image_query}" + "Here is the question: " + state.current_user_message
    notify(state, "info", "Sending message...")
    transformed_query = {"text": state.current_user_message}
    state.messages.append({"role": "user", "content": transformed_query["text"]})
    
    BASE_DIR = os.path.abspath("vectorstore")
    CORE_DIR = os.path.join(BASE_DIR, config["core_docs_directory_name"])
    context, state.sources = retriever.get_relevant_docs(transformed_query["text"])
    augmented_prompt = "Relevant documents:" + context + "\n\n[[QUESTION]]\n\n" + transformed_query["text"] #+ "\n" + config["footer"]
    system_prompt = config["header"]

    response = llm_client.chat_with_prompt(system_prompt, augmented_prompt)
    full_response = ""
    for chunk in response:
        full_response += chunk
    add_history_to_memory(memory, transformed_query["text"], full_response)


    full_response += "\n\nFact Check result: " 
    res = fact_check(context, transformed_query["text"], full_response)
    for response in res:
            full_response += response

    messages.append(
                {"role": "assistant", "content": full_response}
        )


    state.summary = get_summary(memory)
    ##
    conv = state.conversation._dict.copy()
    conv["Conversation"] += [state.current_user_message, full_response]
    state.current_user_message = ""
    state.conversation = conv
    notify(state, "success", "Response received!")


def style_conv(state: State, idx: int, row: int) -> str:
    """
    Apply a style to the conversation table depending on the message's author.

    Args:
        - state: The current state of the app.
        - idx: The index of the message in the table.
        - row: The row of the message in the table.

    Returns:
        The style to apply to the message.
    """
    if idx is None:
        return None
    elif idx % 2 == 0:
        return "user_message"
    else:
        return "gpt_message"


with tgb.Page() as multimodal_assistant:
    with tgb.layout("3 7"):
        with tgb.part("sidebar"):
            tgb.selector(value="{mode}", lov=["multimodal"], dropdown=True, class_name="fullwidth", on_change=change_config)
            tgb.text("Image Input Query", class_name="h2")
            tgb.file_selector(content="{image_file}", on_action=on_images_upload, multiple=True, label="Upload an image with a text input:")

        with tgb.part():
            tgb.text("{config['page_title']}")
            tgb.text("{config.instructions}", mode="md")

            with tgb.part(class_name="p2 align-item-bottom table"): # UX concerns
                tgb.table("{conversation}", style=style_conv, show_all=True, rebuild=True)
                with tgb.part("card mt1"): # UX concerns
                    tgb.input("{current_user_message}", label="Write your message:", on_action=send_message, class_name="fullwidth")

            tgb.text("Summary: {summary}")


pages = {
    "/":"<|navbar|>",
    "Multimodal_Assistant": multimodal_assistant,
    "Knowledge_Base": knowledge_base
}

Gui(pages=pages).run()




"""
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

        # feedback_key = f"feedback_{int(n/2)}"

        # if feedback_key not in st.session_state:
        #     st.session_state[feedback_key] = None
        # col1, col2 = st.columns(2)
        # with col1:
        #     st.write("**Please provide feedback by clicking one of these icons:**")
        # with col2:
        #     streamlit_feedback(**feedback_kwargs, args=[messages[-2]["content"].strip(), messages[-1]["content"].strip()], key=feedback_key, align="flex-start")
"""









# streamlit_analytics.stop_tracking()
