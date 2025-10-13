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

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore

from config import config

# Load the documents; note that for multipage PDFs, this will load all pages as separate documents
print(f"Loading documents from {config.data_dir}...")
documents = SimpleDirectoryReader(input_dir=config.data_dir).load_data()

print(f"Loaded {len(documents)} documents from {config.data_dir}!")
vector_store = MilvusVectorStore(
    uri=config.milvus_path, dim=config.embedding_model_dim, overwrite=True
)
embed_model = NVIDIAEmbedding(config.embedding_model_name)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Create index with Milvus vector store
# This will also insert the documents into the vector store
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=embed_model,
)

print("Documents have been successfully indexed in Milvus Lite.")
