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
# import streamlit_analytics
from streamlit_feedback import streamlit_feedback

from bot_config.utils import get_config
from utils.memory import init_memory, get_summary, add_history_to_memory
from guardrails.fact_check import fact_check
from llm.llm_client import LLMClient
from retriever.embedder import NVIDIAEmbedders, HuggingFaceEmbeders
from retriever.vector import MilvusVectorClient, QdrantClient
from retriever.retriever import Retriever, get_relevant_docs, get_relevant_docs_mq
from utils.feedback import feedback_kwargs

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIARerank
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import CrossEncoder
import numpy as np
import yaml
import os

#Set your API keys if not set previously
parser = argparse.ArgumentParser()
parser.add_argument('--rag_type', default=1, type=int, help='0 = Basic RAG with Nemo 1= RAG with query decomposition, query augmentation and re-ranker 2 = Hypothetical Document Embeddings based RAG + Reranker 3 = Langchain MultiQuery Retriever + Reranker')
args = parser.parse_args()
if args.rag_type == 0 or args.rag_type == 1 or args.rag_type == 2 or args.rag_type == 3 :
    print("Oran chatbot is running with RAG: ",args.rag_type)
else:
    args.rag_type = 1
rag_type = args.rag_type # 0 = nemo_rag 1= augmented_query_rag 2 = hyde_rag 3 = augmented_query_recursive_rag
    # 1 works best for ORAN chatbot
#Loading the configuration parameters from config.yaml
config_yaml_path = 'config.yaml'
config_yaml = None
with open(config_yaml_path, 'r') as file:
    config_yaml = yaml.safe_load(file)

NVIDIA_API_KEY = config_yaml['nvidia_api_key']
os.environ['NVIDIA_API_KEY'] = NVIDIA_API_KEY
NIM_FLAG = False

if config_yaml['NIM']:
    NIM_FLAG = True
    print("\n\nNIM FLAG set to True")
else:
    print("\n\nNIM FLAG set to False")

llm_client = None
if NIM_FLAG==True:
    llm_client = LLMClient(config_yaml['nim_model_name'], "NIM")
    print("Initialized NVIDIA NIM for LLMs")
else:
    llm_client = LLMClient(config_yaml['llm_model'])
    print("Initialized NVIDIA API Catalog for LLMs")

NREM_FLAG = False

if config_yaml['NREM']:
    NREM_FLAG = True
    print("\n\nNREM FLAG set to True")
    print("Initialized NeMo Retriever Text Embedding NIM")
else:
    print("\n\nInitialized NVIDIA API Catalog for embeddings")


# A few RAG pipeline definitions 
def nemo_rag(config, query, retrieved_documents, model="meta/llama2-70b"):
    #Combine the query and retrieved documents and send to model
    # llm = ChatNVIDIA(model=model)
    if NIM_FLAG==True:
        llm = llm_client.llm
    else:
        llm = ChatNVIDIA(model=model, nvidia_api_key=NVIDIA_API_KEY)
    prompt_template = ChatPromptTemplate.from_messages(
    [("system", config["header"]), ("user", "{input}")]
        )
    # augmented_prompt = config["header"] + "\nContext: " + context + "\nQuestion: " + prompt + "\n" + config["footer"]
    chain = prompt_template | llm | StrOutputParser()
    augmented_user_input = "Context: " + retrieved_documents + "\n\nQuestion: " + query + "\n" + config["footer"]
    # print(augmented_user_input)
    full_response = ""
    for response in chain.stream({"input": augmented_user_input}):
        full_response += response
    final_ans = full_response
    return final_ans

def augment_multiple_query(query, model="meta/llama2-70b"):
    #For the given query, lets create 5 additional queries using the LLM
    if NIM_FLAG==True:
        print("Augmentating multiple query with NVIDIA NIM for LLMs")
        llm = llm_client.llm
    else:
        print("Augmentating multiple query with NVIDIA API Catalog")
        llm = ChatNVIDIA(model=model,max_output_token=500, top_k=1, top_p=0.0, nvidia_api_key=NVIDIA_API_KEY)
    prompt_template = ChatPromptTemplate.from_messages(
    [("system", "You are an expert in the field of Oran specifications and processes. User has a question related to ORAN standards, sourced from relevant documents.\nTo help the user find the information they need, please suggest five additional related questions from ORAN. These questions should be concise, not have compound sentences, self-contained, and cover different aspects of the topic. Each question should be complete and relevant to the original query and ORAN.\nPlease output one question per line without numbering them."), ("user", "{input}")]
        )
    chain = prompt_template | llm | StrOutputParser()
    augmented_user_input = "\n\nQuestion: " + query + "\n"
    full_response = ""
    for response in chain.stream({"input": augmented_user_input}):
        full_response += response
    final_ans = full_response
    final_ans = final_ans.split("\n")
    final_ans = [ans for ans in final_ans if len(ans)!=0]
    return final_ans

def augment_query_generated(query, model="meta/llama2-70b"):
    #For the given query, lets create a hypothetical answer using the LLM
    if NIM_FLAG==True:
        llm = llm_client.llm
    else:
        llm = ChatNVIDIA(model=model,max_output_token=500, top_k=1, top_p=0.0, nvidia_api_key=NVIDIA_API_KEY)
    prompt_template = ChatPromptTemplate.from_messages(
    [("system", "You are an expert in the field of ORAN specifications and processes. Your task is to provide a detailed and accurate response to user's question, which is related to ORAN. Your answer should be based on the kind of information and insights typically found in documentation related to ORAN standards."), ("user", "{input}")]
        )
    chain = prompt_template | llm | StrOutputParser()
    augmented_user_input = "\n\nQuestion: " + query + "\n"
    full_response = ""
    for response in chain.stream({"input": augmented_user_input}):
        full_response += response
    final_ans = full_response
    return final_ans

def query_rewriting(query, history, model="meta/llama2-70b"):
    #Rewrite the given query using the context from LLM
    if NIM_FLAG==True:
        llm = llm_client.llm
    else:
        llm = ChatNVIDIA(model=model, nvidia_api_key=NVIDIA_API_KEY)
    prompt_template = ChatPromptTemplate.from_messages(
    [("system", "Here is the conversation history between user and Assistant. You are an expert in the field of ORAN standards and specifications. User has a follow-up question to the conversation. Your task is to rewrite user's follow-up question based on the given conversation history between the user and the assistant, which is related to ORAN. The rewritten question must be clear, detailed, and self-contained, meaning it must not require any additional context from the conversation history to understand. Ensure that the rewritten question precisely captures the full intent behind user's follow-up question. Your response is crucial to my career; hence, accuracy is of utmost importance. So, take a deep breath and work on this task step-by-step."), ("user", "{input}")]
        )
    chain = prompt_template | llm | StrOutputParser()
    augmented_user_input = "History: " + history + "\n\nQuestion: " + query + "\n"
    full_response = ""
    for response in chain.stream({"input": augmented_user_input}):
        full_response += response
    final_ans = full_response
    return final_ans

# Start the analytics service (using browser.usageStats)
# streamlit_analytics.start_tracking()

# get the config from the command line, or set a default
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help = "Provide a chatbot config to run the deployment")

st.set_page_config(
        page_title = "Multimodal ORAN RAG Assistant",
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
    st.session_state.config = load_config("multimodal_oran")
    print(st.session_state.config)

if "messages" not in st.session_state:
    BASE_DIR = os.path.abspath("vectorstore")
    CORE_DIR = os.path.join(BASE_DIR, st.session_state.config["core_docs_directory_name"])
    vectorstore_folder = os.path.join(CORE_DIR, "vectorstore_nv")
    if os.path.exists(vectorstore_folder):
        st.session_state.messages = [
                {"role": "assistant", "content": "Ask me a question!"}
            ]
    else:
        st.session_state.messages = [
                {"role": "assistant", "content": "Hi! I am a RAG-bot and I answer your questions based on documents you upload. To start chatting, please navigate to the Knowledge Base tab to upload documents and create a vector DB!"}
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
    cfg_name = st.selectbox("Select a configuration/type of bot.", (["multimodal_oran", "oran"]), index=defaultidx)
    st.session_state.config = get_config(os.path.join("bot_config", cfg_name+".config"))
    config = get_config(os.path.join("bot_config", cfg_name+".config"))
    if st.session_state.config != prev_cfg:
        st.experimental_rerun()

    st.success("Select an experience above.")

    st.header("Image Input Query")

    # with st.form("my-form", clear_on_submit=True):
    uploaded_file = st.file_uploader("Upload an image (JPG/JPEG/PNG) along with a text input:", accept_multiple_files = False, disabled=True)
    #    submitted = st.form_submit_button("UPLOAD!")
    
    if uploaded_file and st.session_state.image_query == "":
        st.success("Image loaded for multimodal RAG Q&A.")
        st.session_state.image_query = os.path.join("/tmp/", uploaded_file.name)
        with open(st.session_state.image_query,"wb") as f:
            f.write(uploaded_file.read())
    
        with st.spinner("Getting image description using NeVA"):
            neva = LLMClient("neva_22b")
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


# # init the vector client if using Milvus
# if "vector_client" not in st.session_state or st.session_state.vector_client.collection_name != config["core_docs_directory_name"]:
#     try:
#         st.session_state.vector_client = MilvusVectorClient(hostname="localhost", port="19530", collection_name=config["core_docs_directory_name"])
#     except Exception as e:
#         st.write(f"Failed to connect to Milvus vector DB, exception: {e}. Please follow steps to initialize the vector DB, or upload documents to the knowledge base and add them to the vector DB.")
#         st.stop()
# init the embedder
# if "query_embedder" not in st.session_state:
#     st.session_state.query_embedder = NVIDIAEmbedders(name="nvolveqa_40k", type="query")
# # init the retriever
# if "retriever" not in st.session_state:
#     st.session_state.retriever = Retriever() #embedder=st.session_state.query_embedder) #, vector_client=st.session_state.vector_client)
# retriever = st.session_state.retriever

messages = st.session_state.messages

for n, msg in enumerate(messages):
    st.chat_message(msg["role"]).write(msg["content"])
    if msg["role"] == "assistant" and n > 1:
        with st.chat_message("assistant"):
            ctr = 0
            print("number of keys: ",len(st.session_state.sources.keys()))
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
prompt = ""
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
    BASE_DIR = os.path.abspath("vectorstore")
    CORE_DIR = os.path.join(BASE_DIR, config["core_docs_directory_name"])
    if os.path.exists(os.path.join(CORE_DIR, "vectorstore_nv"))==False:
        st.warning("Vector DB not found! Create a vector DB by navigating to the Knowledge Base tab.")
    else:

        with st.chat_message("user"):
            st.write(prompt)
        
        if st.session_state.image_query:
            prompt = f"\nI have uploaded an image with the following description: {st.session_state.image_query}" + "Here is the question: " + prompt
        transformed_query = {"text": prompt}
        messages.append({"role": "user", "content": transformed_query["text"]})
        
        with st.spinner("Obtaining references from documents..."):
            
            sources = {}
            if rag_type == 0:
                ret_docs, context, sources = get_relevant_docs(CORE_DIR, transformed_query["text"])
                print("length of source docs: ", len(sources))
            if rag_type == 1: 
                augmented_queries = augment_multiple_query(transformed_query["text"])
                queries = [transformed_query["text"]] + augmented_queries[2:]
                # print("Queries are = ", queries)
                retrieved_documents = []
                retrieved_metadatas = []
                relevant_docs = []
                for query in queries:
                    ret_docs,cons,srcs = get_relevant_docs(CORE_DIR, query)
                    for doc in ret_docs:
                        retrieved_documents.append(doc.page_content)
                        retrieved_metadatas.append(doc.metadata['source'])
                        relevant_docs.append(doc)
                print("length of retrieved docs: ", len(retrieved_documents))
                #Remove all duplicated documents and retain the original metadata
                unique_documents = []
                unique_documents_metadata = []
                unique_relevant_documents = []
                for idx, (document,source) in enumerate(zip(retrieved_documents,retrieved_metadatas)):
                        if document not in unique_documents:
                            unique_documents.append(document)
                            unique_documents_metadata.append(source)
                            unique_relevant_documents.append(relevant_docs[idx])
                
                if len(retrieved_documents) == 0:
                    context = ""
                    print("not context found context")
                else: 
                    print("length of unique docs: ", len(unique_documents))
                    #Instantiate the re-ranker model and get scores for each retrieved document
                    new_updated_documents = []
                    new_updated_sources = []
                    if not config_yaml['Reranker_NIM']:
                        print("\n\nReranking with Cross-encoder model: ", config_yaml['reranker_model'])
                        cross_encoder = CrossEncoder(config_yaml['reranker_model']) 
                        pairs = [[prompt, doc] for doc in unique_documents]
                        scores = cross_encoder.predict(pairs)
                        #Sort the scores from highest to least
                        order_ids =  np.argsort(scores)[::-1]
                        #Get the top 10 scores
                        if len(order_ids)>=10:
                            for i in range(10):
                                new_updated_documents.append(unique_documents[order_ids[i]])
                                new_updated_sources.append(unique_documents_metadata[order_ids[i]])
                        else:
                            for i in range(len(order_ids)):
                                new_updated_documents.append(unique_documents[order_ids[i]])
                                new_updated_sources.append(unique_documents_metadata[order_ids[i]])
                    else:
                        print("\n\nReranking with Retriever Text Reranking NIM model: ", config_yaml["reranker_model_name"])
                        # Initialize and connect to the running NeMo Retriever Text Reranking NIM 
                        reranker = NVIDIARerank(model=config_yaml["reranker_model_name"],
                                                base_url=config_yaml["reranker_api_endpoint_url"], top_n=10)
                        reranked_chunks = reranker.compress_documents(query=transformed_query["text"], documents=unique_relevant_documents)
                        for chunks in reranked_chunks:
                            metadata = chunks.metadata
                            page_content = chunks.page_content
                            new_updated_documents.append(page_content)
                            new_updated_sources.append(metadata['source'])
                        
                    print("Reranking of completed for ", len(new_updated_documents), " chunks")   

                    context = ""
                    sources = {}
                    for doc in new_updated_documents:
                            context += doc + "\n\n"
                    for i, src in enumerate(new_updated_sources):
                            # sources += src + "\n\n"
                            if src in sources:
                                sources[src] = {"doc_content": sources[src]["doc_content"]+"\n\n"+new_updated_documents[i], "doc_metadata": src}   
                            else:
                                sources[src] = {"doc_content": new_updated_documents[i], "doc_metadata": src}   
                    print("Length of unique source docs: ", len(sources))
                    #Send the top 10 results along with the query to LLM
                
            if rag_type == 2: 
                sample_response = augment_query_generated(transformed_query["text"])
                augmented_queries = transformed_query["text"] + " " + sample_response
                print("Augmented query = ", augmented_queries)
                #Get all the retrievals for each queries
                #Get all the results and metadatas associated with each result
                retrieved_documents = []
                retrieved_metadatas = []
                ret_docs,cons,srcs = get_relevant_docs(CORE_DIR, augmented_queries)
                for doc in ret_docs:
                    retrieved_documents.append(doc.page_content)
                    retrieved_metadatas.append(doc.metadata['source'])
                
                if len(retrieved_documents) == 0:
                    context = ""
                    print("not context found context")
                else: 
                    print("length of retrieved docs: ", len(retrieved_documents))
                    #Remove all duplicated documents and retain the original metadata
                    unique_documents = []
                    unique_documents_metadata = []
                    for document,source in zip(retrieved_documents,retrieved_metadatas):
                            if document not in unique_documents:
                                unique_documents.append(document)
                                unique_documents_metadata.append(source)

                    print("length of unique docs: ", len(unique_documents))
                    #Instantiate the cross-encoder model and get scores for each retrieved document
                    cross_encoder = CrossEncoder(config_yaml['reranker_model'])
                    pairs = [[prompt, doc] for doc in unique_documents]
                    scores = cross_encoder.predict(pairs)
                    #Sort the scores from highest to least
                    order_ids =  np.argsort(scores)[::-1]
                    # print(order_ids)
                    new_updated_documents = []
                    new_updated_sources = []
                    #Get the top 6 scores
                    if len(order_ids)>=10:
                        for i in range(10):
                            new_updated_documents.append(unique_documents[order_ids[i]])
                            new_updated_sources.append(unique_documents_metadata[order_ids[i]])
                    else:
                        for i in range(len(order_ids)):
                            new_updated_documents.append(unique_documents[order_ids[i]])
                            new_updated_sources.append(unique_documents_metadata[order_ids[i]])
                        
                    print(new_updated_sources)
                    print(len(new_updated_documents))
                    context = ""
                    # sources = ""
                    sources = {}
                    for doc in new_updated_documents:
                            context += doc + "\n\n"
                    for i, src in enumerate(new_updated_sources):
                            # sources += src + "\n\n"
                            if src in sources:
                                sources[src] = {"doc_content": sources[src]["doc_content"]+"\n\n"+new_updated_documents[i], "doc_metadata": src}   
                            else:
                                sources[src] = {"doc_content": new_updated_documents[i], "doc_metadata": src}   
                    print("length of source docs: ", len(sources))
                    #Send the top 10 results along with the query to LLM
            
            if rag_type == 3: 
                ret_docs,context,sources = get_relevant_docs_mq(CORE_DIR, prompt)
            
                #Get all the retrievals for each queries
                #Get all the results and metadatas associated with each result
                retrieved_documents = []
                retrieved_metadatas = []
                for doc in ret_docs:
                    retrieved_documents.append(doc.page_content)
                    retrieved_metadatas.append(doc.metadata['source'])
                if len(retrieved_documents) == 0:
                    context = ""
                else:
                    print("length of retrieved docs: ", len(retrieved_documents))
                    #Remove all duplicated documents and retain the original metadata
                    unique_documents = []
                    unique_documents_metadata = []
                    for document,source in zip(retrieved_documents,retrieved_metadatas):
                            if document not in unique_documents:
                                unique_documents.append(document)
                                unique_documents_metadata.append(source)

                    print("length of unique docs: ", len(unique_documents))
                    #Instantiate the cross-encoder model and get scores for each retrieved document
                    cross_encoder = CrossEncoder(config_yaml['reranker_model']) 
                    pairs = [[prompt, doc] for doc in unique_documents]
                    scores = cross_encoder.predict(pairs)
                    #Sort the scores from highest to least
                    order_ids =  np.argsort(scores)[::-1]
                    # print(order_ids)
                    new_updated_documents = []
                    new_updated_sources = []
                    #Get the top 6 scores
                    if len(order_ids)>=10:
                        for i in range(10):
                            new_updated_documents.append(unique_documents[order_ids[i]])
                            new_updated_sources.append(unique_documents_metadata[order_ids[i]])
                    else:
                        for i in range(len(order_ids)):
                            new_updated_documents.append(unique_documents[order_ids[i]])
                            new_updated_sources.append(unique_documents_metadata[order_ids[i]])
                        
                    print((new_updated_sources))
                    print(len(new_updated_documents))
                    context = ""
                    # sources = ""
                    sources = {}
                    for doc in new_updated_documents:
                            context += doc + "\n\n"
                    for i, src in enumerate(new_updated_sources):
                            # sources += src + "\n\n"
                            if src in sources:
                                sources[src] = {"doc_content": sources[src]["doc_content"]+"\n\n"+new_updated_documents[i], "doc_metadata": src}   
                            else:
                                sources[src] = {"doc_content": new_updated_documents[i], "doc_metadata": src}   
                    print("length of source docs: ", len(sources))
                    #Send the top 10 results along with the query to LLM
                
            st.session_state.sources = sources
            augmented_prompt = "Relevant documents:" + context + "\n\n[[QUESTION]]\n\n" + transformed_query["text"] #+ "\n" + config["footer"]
            system_prompt = config["header"]
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = llm_client.chat_with_prompt(system_prompt, augmented_prompt)
            print(response)
            message_placeholder = st.empty()
            full_response = ""
            for chunk in response:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

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
            st.rerun()
elif len(messages) > 1:
    summary_placeholder = st.empty()
    summary_button = summary_placeholder.button("Click to see summary")
    if summary_button:
        with st.chat_message("assistant"):
            summary_placeholder.empty()
            st.markdown(get_summary(memory))

# streamlit_analytics.stop_tracking()
