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


# Import necessary libraries
import os
import gradio as gr
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings

# Configure settings for the application
# os.environ["NVIDIA_API_KEY"] = 'nvapi-XXXXXXX' # Alternatively, set the environment variable
Settings.text_splitter = SentenceSplitter(chunk_size=500)
Settings.embed_model = NVIDIAEmbedding(model="NV-Embed-QA", truncate="END")
Settings.llm = NVIDIA(model="meta/llama3-70b-instruct")


# Check if NVIDIA API key is set as an environment variable
if os.getenv('NVIDIA_API_KEY') is None:
    raise ValueError("NVIDIA_API_KEY environment variable is not set")

# Initialize global variables for the index and query engine
index = None
query_engine = None

# Function to get file names from file objects
def get_files_from_input(file_objs):
    if not file_objs:
        return []
    return [file_obj.name for file_obj in file_objs]

# Function to load documents and create the index
def load_documents(file_objs, progress=gr.Progress()):
    global index, query_engine
    try:
        if not file_objs:
            return "Error: No files selected."
        
        file_paths = get_files_from_input(file_objs)
        documents = []
        for file_path in file_paths:
            directory = os.path.dirname(file_path)
            documents.extend(SimpleDirectoryReader(input_files=[file_path]).load_data())
        
        if not documents:
            return f"No documents found in the selected files."
        
        # Create a Milvus vector store and storage context
        vector_store = MilvusVectorStore(uri="./milvus_demo.db", dim=1024, overwrite=True)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create the index from the documents
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        
        # Create the query engine
        query_engine = index.as_query_engine(similarity_top_k=5, streaming=True)
        return f"Successfully loaded {len(documents)} documents from {len(file_paths)} files."
    except Exception as e:
        return f"Error loading documents: {str(e)}"

# Function to handle chat interactions
def chat(message, history):
    global query_engine
    if query_engine is None:
        return history + [("Please load documents first.", None)]
    try:
        response = query_engine.query(message)
        return history + [(message, response)]
    except Exception as e:
        return history + [(message, f"Error processing query: {str(e)}")]

# Function to stream responses
def stream_response(message, history):
    global query_engine
    if query_engine is None:
        yield history + [("Please load documents first.", None)]
        return
    
    try:
        response = query_engine.query(message)
        partial_response = ""
        for text in response.response_gen:
            partial_response += text
            yield history + [(message, partial_response)]
    except Exception as e:
        yield history + [(message, f"Error processing query: {str(e)}")]

# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# RAG Q&A Chat Application")
    
    with gr.Row():
        file_input = gr.File(label="Select files to load", file_count="multiple")
        load_btn = gr.Button("Load Documents")
    
    load_output = gr.Textbox(label="Load Status")
    
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Enter your question", interactive=True)
    clear = gr.Button("Clear")
    
    # Set up event handlers
    load_btn.click(load_documents, inputs=[file_input], outputs=[load_output], show_progress="hidden")
    msg.submit(stream_response, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(lambda: "", outputs=[msg])  # Clear input box after submission
    clear.click(lambda: None, None, chatbot, queue=False)

# Launch the Gradio interface
if __name__ == "__main__":
    demo.launch()