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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredFileLoader

from vectorstore.custom_powerpoint_parser import process_ppt_file
from vectorstore.custom_pdf_parser import get_pdf_documents
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, Docx2txtLoader, UnstructuredHTMLLoader, TextLoader, UnstructuredPDFLoader
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import NeMoEmbeddings, HuggingFaceEmbeddings
from qdrant_client import QdrantClient
import multiprocessing
import pickle
import re
import pandas as pd
import yaml


CUSTOM_PROCESSING = True
NVIDIA_API_KEY = yaml.safe_load(open("config.yaml"))['nvidia_api_key']
os.environ['NVIDIA_API_KEY'] = NVIDIA_API_KEY
# Initialize the HuggingFaceEmbeddings object
# hf_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
# sample_text = "This is a sample text."
# sample_embedding = hf_embeddings.embed_query(sample_text)
# vector_size = len(sample_embedding)

# model_name = "intfloat/e5-large-v2"
# model_kwargs = {"device": "cuda"}
# encode_kwargs = {"normalize_embeddings": True}
# e5_embeddings = HuggingFaceEmbeddings(
#     model_name=model_name,
#     model_kwargs=model_kwargs,
#     encode_kwargs=encode_kwargs,
# )
nv_embedder = None
if yaml.safe_load(open('config.yaml', 'r'))['NREM']:
    # Embeddings with NeMo Retriever Embeddings Microservice (NREM)
    print("Generating embeddings with NeMo Retriever Text Embedding NIM")
    nv_embedder = NVIDIAEmbeddings(base_url= yaml.safe_load(open('config.yaml', 'r'))['nrem_api_endpoint_url'],
                                   model=yaml.safe_load(open('config.yaml', 'r'))['nrem_model_name'],
                                   truncate = yaml.safe_load(open('config.yaml', 'r'))['nrem_truncate']
                                   )

else:
    # Embeddings with NVIDIA AI Foundation Endpoints
    nv_embedder = NVIDIAEmbeddings(model=yaml.safe_load(open('config.yaml', 'r'))['embedding_model'], truncate="END")

def load_documents(folder, status=None):
    """Load documents from the specified folder."""
    raw_documents = []
    # filelist = [file for root, dirs, files in os.walk(folder) for file in files if file.endswith(".pdf") or file.endswith(".txt") or file.endswith(".docx")]
    filelist = [file for file in os.listdir(folder) if file.endswith(".pdf") or file.endswith(".txt") or file.endswith(".docx")]
    print(filelist)
    with st.spinner():
        for file in filelist:
            st.write("Loading document: ", file)
            file_path = os.path.join(folder, file)

            if file.endswith("pdf") and CUSTOM_PROCESSING:
                # Process each PDF document and add them individually to the list
                # pdf_docs = get_pdf_documents(file_path)
                # for each_page in pdf_docs:
                #     raw_documents.extend(each_page)
                pdf_docs = UnstructuredPDFLoader(file_path).load() #get_pdf_documents(file_path)
                raw_documents.extend(pdf_docs)
            elif file.endswith("ppt") or file.endswith("pptx"):
                pptx_docs = process_ppt_file(file_path)
                raw_documents.extend(pptx_docs)
            elif file.endswith("docx") or file.endswith("docx"):
                docx_docs = Docx2txtLoader(file_path).load()
                raw_documents.extend(docx_docs)
            elif file.endswith("html") or file.endswith("html"):
                html_docs = UnstructuredHTMLLoader(file_path).load()
                raw_documents.extend(html_docs)
            elif file.endswith("txt") or file.endswith("txt"):
                txt_docs = TextLoader(file_path).load()
                raw_documents.extend(txt_docs)
            else:
                # Load unstructured files and add them individually
                loader = UnstructuredFileLoader(file_path)
                unstructured_docs = loader.load()
                raw_documents.extend(unstructured_docs)  # 'extend' is used here to add elements of the list individually
    return raw_documents

def remove_line_break(text):
    text = text.replace("\n", " ").strip()
    text = re.sub("\.\.+", "", text)
    text = re.sub(" +", " ", text)
    return text

def remove_two_points(text):
    text = text.replace("..","")
    return text

def remove_two_slashes(text):
    text = text.replace("__","")
    return text

def just_letters(text):
    return re.sub(r"[^a-z]+", "", text).strip()

def remove_non_english_letters(text):
    return re.sub(r"[^\x00-\x7F]+", "", text)

def langchain_length_function(text):
    return len(just_letters(remove_line_break(text)))

def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

def split_text(documents):
    """Split text documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size = 500,
        chunk_overlap  = 100,
        length_function = langchain_length_function,
        is_separator_regex = False,
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs

# def update_vectorstore(folder, vector_client, embedder, config_name, status=None):
#     """Generates word embeddings for documents and updates the Milvus collection."""
#     # Attempt to create collection, catch exception if it already exists
#     status.update(label="[Step 1/4] Creating/loading vector store")

#     # Create collection if it doesn't exist
#     st.write("Creating collection...")
#     # get embedding size
#     embedding_size = embedder.get_embedding_size()
#     vector_client.create_collection(config_name, embedding_size)

#     status.update(label="[Step 2/4] Processing and splitting documents")
#     # load and split documents
#     raw_documents = load_documents(folder, status)
#     documents = split_text(raw_documents)

#     print("Loading data to the vector index store...")
#     status.update(label="[Step 3/4] Inserting documents into the vector store...")
#     # Extracting the page content from each document
#     document_contents = [doc.page_content for doc in documents]

#     # Embedding the documents using the updated embedding function
#     document_embeddings = embedder.embed_documents(document_contents, batch_size=10)

#     # Batch insert into Milvus collection
#     vector_client.update(documents, document_embeddings, config_name)
#     status.update(label="[Step 4/4] Saved vector store!", state="complete", expanded=False)

def update_vectorstore(folder, config_name, status=None):
    """Generates word embeddings for documents and updates the Qdrant collection."""
    # client = QdrantClient(host="localhost", port=6333)
    # collection_name = config_name

    # Create collection if it doesn't exist
    # Attempt to create collection, catch exception if it already exists
    # status(label="[Step 1/4] Creating/loading vector store", state="complete", expanded=False)

    # with open(os.path.join(folder, "vectorstore_nv.pkl"), "rb") as f:
    #     vectorstore = pickle.load(f)
    if not os.path.exists(os.path.join(folder, "vectorstore_nv")):
        st.write("Vector DB not found. Please create a vector DB.")
        return 1
    vectorstore = FAISS.load_local(os.path.join(folder, "vectorstore_nv"), nv_embedder, allow_dangerous_deserialization=True)
    # status("[Step 2/4] Processing and splitting documents", state="complete", expanded=False)
    prev_folder = folder
    folder = os.path.join(folder, "new_files")
    if not os.path.exists(folder):
        os.mkdir(folder)
    raw_documents = load_documents(folder, status)

    documents = split_text(raw_documents)

    #remove short chuncks
    filtered_documents = [item for item in documents if len(item.page_content) >= 200]
    [(len(item.page_content),item.page_content) for item in documents]
    documents = filtered_documents
    pd.DataFrame([doc.metadata for doc in documents])['source'].unique()
    #remove line break
    for i in range(0,len(documents)-1):
        documents[i].page_content=remove_line_break(documents[i].page_content)
    #remove two points
    for i in range(0,len(documents)-1):
        documents[i].page_content=remove_two_points(documents[i].page_content)
    #remove non english characters points
    for i in range(0,len(documents)-1):
        documents[i].page_content=remove_two_slashes(documents[i].page_content)
    #remove two points
    for i in range(0,len(documents)-1):
        documents[i].page_content=remove_two_points(documents[i].page_content)
    [(len(item.page_content),item.page_content) for item in documents]

    print("Loading data to the vector index store...")
    # status("[Step 3/4] Inserting documents into the vector store...", state="complete", expanded=False)
    db1 = FAISS.from_documents(documents, nv_embedder)
    vectorstore.merge_from(db1)
    # with open(os.path.join(prev_folder, "vectorstore_nv.pkl"), "wb") as f:
    #     pickle.dump(vectorstore, f)
    # vectorstore.save_local("vectorstore_nv")
    vectorstore.save_local(os.path.join(folder, "vectorstore_nv"))
    return 0

# Function to process documents in chunks of 20
def process_documents_nvolve(documents):
    batch_insert_data = []
    for i in range(0, len(documents), 20):
        # Selecting a chunk of 20 documents
        doc_chunk = documents[i:i+20]

        for doc in doc_chunk:
            print(len(doc.page_content))

        # Extracting the page content from each document
        chunk_content = [doc.page_content for doc in doc_chunk]

        # Embedding the chunk of documents using the updated embedding function
        chunk_embeddings = nvolve_embedding(chunk_content)["embeddings"]

        # Processing each document in the chunk
        for j, doc in enumerate(doc_chunk):
            st.write(f"Processing: {doc.metadata['source']}")

            # Prepare data for batch insertion
            insert_data = {
                "id": i + j,
                "content": doc.page_content,
                "embedding": chunk_embeddings[j],
                "metadata": doc.metadata
            }
            batch_insert_data.append(insert_data)

    return batch_insert_data

def create_vectorstore(folder, config_name, status=None):
    """Generates word embeddings for documents and updates the Qdrant collection."""
    # Create vectorstore if it doesn't exist
    # Attempt to create collection, catch exception if it already exists
    # status(label="[Step 1/4] Creating/loading vector store", state="complete", expanded=False)
    # if os.path.isfile(os.path.join(folder, "vectorstore_nv/index.pkl")) == True:
    if os.path.exists(os.path.join(folder, "vectorstore_nv")) == True:
        # st.write("To add more documents to the exising DB, please use the Re-Train Multimodal Assistant button.")
        return 1
    else:
        # status("[Step 2/4] Processing and splitting documents", state="complete", expanded=False)
        raw_documents = load_documents(folder, status)
        print(raw_documents)
        documents = split_text(raw_documents)

        #remove short chuncks
        filtered_documents = [item for item in documents if len(item.page_content) >= 200]
        [(len(item.page_content),item.page_content) for item in documents]
        documents = filtered_documents
        pd.DataFrame([doc.metadata for doc in documents])['source'].unique()
        #remove line break
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_line_break(documents[i].page_content)
        #remove two points
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_two_points(documents[i].page_content)
        #remove non english characters points
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_two_slashes(documents[i].page_content)
        #remove two points
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_two_points(documents[i].page_content)
        [(len(item.page_content),item.page_content) for item in documents]

        print("Loading data to the vector index store...")
        # status("[Step 3/4] Inserting documents into the vector store...", state="complete", expanded=False)
        vectorstore = FAISS.from_documents(documents, nv_embedder)
        # vectorstore.merge_from(db1)
        # with open(os.path.join(folder, "vectorstore_nv.pkl"), "wb") as f:
        #     pickle.dump(vectorstore, f)
        # vectorstore.save_local("vectorstore_nv")
        vectorstore.save_local(os.path.join(folder, "vectorstore_nv"))
    return 0
