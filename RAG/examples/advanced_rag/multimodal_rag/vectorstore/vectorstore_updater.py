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

import logging
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredFileLoader

from RAG.examples.advanced_rag.multimodal_rag.vectorstore.custom_img_parser import process_img_file
from RAG.examples.advanced_rag.multimodal_rag.vectorstore.custom_pdf_parser import get_pdf_documents
from RAG.examples.advanced_rag.multimodal_rag.vectorstore.custom_powerpoint_parser import process_ppt_file

logger = logging.getLogger(__name__)

CUSTOM_PROCESSING = True


def load_documents(file):
    """Load documents from the specified folder."""
    raw_documents = []

    logger.info(f"Loading document: {file}")

    if file.endswith("pdf") and CUSTOM_PROCESSING:
        # Process each PDF document and add them individually to the list
        pdf_docs = get_pdf_documents(file)
        for each_page in pdf_docs:
            raw_documents.extend(each_page)
    elif file.endswith("ppt") or file.endswith("pptx"):
        pptx_docs = process_ppt_file(file)
        raw_documents.extend(pptx_docs)
    elif file.endswith("png"):
        img_docs = process_img_file(file)
        raw_documents.extend(img_docs)
    else:
        # Load unstructured files and add them individually
        loader = UnstructuredFileLoader(file)
        unstructured_docs = loader.load()
        raw_documents.extend(unstructured_docs)  # 'extend' is used here to add elements of the list individually
    return raw_documents


def split_text(documents):
    """Split text documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs


def update_vectorstore(file_path, vector_client, embedder, config_name):
    """Generates word embeddings for documents and updates the Milvus collection."""
    # Attempt to create collection, catch exception if it already exists
    logger.info("[Step 1/4] Creating/loading vector store")

    # Create collection if it doesn't exist
    logger.info("Accessing collection...")

    logger.info("[Step 2/4] Processing and splitting documents")
    # load and split documents
    raw_documents = load_documents(file_path)
    documents = split_text(raw_documents)

    # Adding file name to the metadata
    for document in documents:
        document.metadata["filename"] = os.path.basename(file_path)

    logger.info("[Step 3/4] Inserting documents into the vector store...")
    # Batch insert into Milvus collection
    vector_client.add_documents(documents)
    logger.info("[Step 4/4] Saved vector store!")
