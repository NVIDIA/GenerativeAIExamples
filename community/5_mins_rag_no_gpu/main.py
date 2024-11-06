# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# This is a simple standalone implementation showing rag pipeline using Nvidia AI Foundational Models.
# It uses a simple Streamlit UI and one file implementation of a minimalistic RAG pipeline.


############################################
# Component #0.5 - UI / Header
############################################

import streamlit as st
import os

# Page settings 
st.set_page_config(
    layout="wide",
    page_title="RAG Chatbot", 
    page_icon = "🤖",
    initial_sidebar_state="expanded")

# Page title 
st.header('Generic RAG Chatbot Demo 🤖📝', divider='rainbow')

# Custom CSS
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("style.css")

# Page description 
st.markdown('''Manually looking through vast amounts of data can be tedious and time-consuming. This chatbot can expedite that process by providing a platform to query your documents.''')
st.warning("This is a proof of concept, and any output from the AI agent should be used in conjunction with the original data.", icon="⚠️")

############################################
# Component #1 - Document Loader
############################################

with st.sidebar:
    st.subheader("Upload Your Documents")

    DOCS_DIR = os.path.abspath("./uploaded_docs")

    # Make dir to store uploaded documents
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    # Define form on Streamlit page for uploading files to KB
    st.subheader("Add to the Knowledge Base")
    with st.form("my-form", clear_on_submit=True):
        uploaded_files = st.file_uploader("Upload a file to the Knowledge Base:", accept_multiple_files=True)
        submitted = st.form_submit_button("Upload!")

    # Acknowledge successful file uploads
    if uploaded_files and submitted:
        for uploaded_file in uploaded_files:
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            with open(os.path.join(DOCS_DIR, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.read())

############################################
# Component #2 - Initalizing Embedding Model and LLM
############################################

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
 
#Make sure to export your NGC NV-Developer API key as NVIDIA_API_KEY! 
API_KEY = os.environ['NVIDIA_API_KEY']

# Select embedding model and LLM
document_embedder = NVIDIAEmbeddings(model="NV-Embed-QA", api_key=API_KEY, model_type="passage", truncate="END")
llm = ChatNVIDIA(model="meta/llama3-70b-instruct", api_key=API_KEY, temperature=0)

############################################
# Component #3 - Vector Database Store
############################################

import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever

# Option for using an existing vector store
with st.sidebar:
    use_existing_vector_store = st.radio("Use existing vector store if available", ["Yes", "No"], horizontal=True)

# Load raw documents from the directory
DOCS_DIR = os.path.abspath("./uploaded_docs")
raw_documents = DirectoryLoader(DOCS_DIR).load()

# Check for existing vector store file
vector_store_path = "vectorstore.pkl"
vector_store_exists = os.path.exists(vector_store_path)
vectorstore = None

if use_existing_vector_store == "Yes" and vector_store_exists:
    # Load existing vector store
    with open(vector_store_path, "rb") as f:
        vectorstore = pickle.load(f)
    with st.sidebar:
        st.info("Existing vector store loaded successfully.")
else:
    with st.sidebar:
        if raw_documents and use_existing_vector_store == "Yes":
            # Chunk documents
            with st.spinner("Splitting documents into chunks..."):
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)
                documents = text_splitter.split_documents(raw_documents)

            # Convert document chunks to embeddings, and save in a vector store
            with st.spinner("Adding document chunks to vector database..."):
                vectorstore = FAISS.from_documents(documents, document_embedder)

            # Save vector store
            with st.spinner("Saving vector store"):
                with open(vector_store_path, "wb") as f:
                    pickle.dump(vectorstore, f)
            st.success("Vector store created and saved.")
        else:
            st.warning("No documents available to process!", icon="⚠️")

############################################
# Component #4 - LLM Response Generation and Chat
############################################

st.subheader("Query your data")

# Save chat history for this user session
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Define prompt for LLM
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use the provided context to inform your responses. If no context is available, please state that."),
    ("human", "{input}")
])

# Define simple prompt chain 
chain = prompt_template | llm | StrOutputParser()

# Display an example query for user 
user_query = st.chat_input("Please summarize these documents.")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        if vectorstore is not None and use_existing_vector_store == "Yes":
            # Retrieve relevant chunks for the given user query from the vector store
            retriever = vectorstore.as_retriever()
            retrieved_docs = retriever.invoke(user_query)

            # Concatenate retrieved chunks together as context for LLM
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            augmented_user_input = f"Context: {context}\n\nQuestion: {user_query}\n"
        else:
            augmented_user_input = f"Question: {user_query}\n"

        # Get output from LLM
        for response in chain.stream({"input": augmented_user_input}):
            full_response += response
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})