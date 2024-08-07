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
from llama_index.core import SimpleDirectoryReader, KnowledgeGraphIndex
from utils.preprocessor import extract_triples
from llama_index.core import ServiceContext
import multiprocessing
import pandas as pd
import networkx as nx
from utils.lc_graph import process_documents, save_triples_to_csvs
from vectorstore.search import SearchHandler
from langchain_nvidia_ai_endpoints import ChatNVIDIA

import nltk
nltk.download('averaged_perceptron_tagger')

def load_data(input_dir, num_workers):
    reader = SimpleDirectoryReader(input_dir=input_dir)
    documents = reader.load_data(num_workers=num_workers)
    return documents

def has_pdf_files(directory):
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            return True
    return False

st.title("Knowledge Graph RAG")

st.subheader("Load Data from Files")

# Variable for documents
if 'documents' not in st.session_state:
    st.session_state['documents'] = None

models = ChatNVIDIA.get_available_models()
available_models = [model.id for model in models if model.model_type=="chat" and "instruct" in model.id]
with st.sidebar:
    llm = st.selectbox("Choose an LLM", available_models, index=available_models.index("mistralai/mixtral-8x7b-instruct-v0.1"))
    st.write("You selected: ", llm)
    llm = ChatNVIDIA(model=llm)

def app():
    # Get the current working directory
    cwd = os.getcwd()

    # Get a list of visible directories in the current working directory
    directories = [d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d)) and not d.startswith('.') and '__' not in d]

    # Create a dropdown menu for directory selection
    selected_dir = st.selectbox("Select a directory:", directories, index=0)

    # Construct the full path of the selected directory
    directory = os.path.join(cwd, selected_dir)

    if st.button("Process Documents"):
        # Check if the selected directory has PDF files
        res = has_pdf_files(directory)
        if not res:
            st.error("No PDF files found in directory! Only PDF files and text extraction are supported for now.")
            st.stop()
        documents, results = process_documents(directory, llm)
        print(documents)
        st.write(documents)
        search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)
        search_handler.insert_data(documents)
        st.write(f"Processing complete. Total triples extracted: {len(results)}")
    
        with st.spinner("Saving triples to CSV files with Pandas..."):
            # write the resulting entities to a CSV, relations to a CSV and all triples with IDs to a CSV
            save_triples_to_csvs(results)

        with st.spinner("Loading the CSVs into dataframes..."):
                # Load the triples from the CSV file
                triples_df = pd.read_csv("triples.csv")
                # Load the entities and relations DataFrames
                entities_df = pd.read_csv("entities.csv")
                relations_df = pd.read_csv("relations.csv")

        # with st.spinner("Creating the knowledge graph from these triples..."):
            # Create a mapping from IDs to entity names and relation names
        entity_name_map = entities_df.set_index("entity_id")["entity_name"].to_dict()
        relation_name_map = relations_df.set_index("relation_id")["relation_name"].to_dict()

        # Create the graph from the triples DataFrame
        G = nx.from_pandas_edgelist(
            triples_df,
            source="entity_id_1",
            target="entity_id_2",
            edge_attr="relation_id",
            create_using=nx.DiGraph,
        )

        with st.spinner("Relabeling node integers to strings for future retrieval..."):        
            # Relabel the nodes with the actual entity names
            G = nx.relabel_nodes(G, entity_name_map)

            # Relabel the edges with the actual relation names
            edge_attributes = nx.get_edge_attributes(G, "relation_id")

            # Update the edges with the new relation names
            new_edge_attributes = {
                (u, v): relation_name_map[edge_attributes[(u, v)]]
                for u, v in G.edges()
                if edge_attributes[(u, v)] in relation_name_map
            }

            nx.set_edge_attributes(G, new_edge_attributes, "relation")

        with st.spinner("Saving the graph to a GraphML file for further visualization and retrieval..."):
            try:
                nx.write_graphml(G, "knowledge_graph.graphml")
                
                # Verify by reading it back
                G_loaded = nx.read_graphml("knowledge_graph.graphml")
                if nx.is_directed(G_loaded):
                    st.success("GraphML file is valid and successfully loaded.")
                else:
                    st.error("GraphML file is invalid.")
            except Exception as e:
                st.error(f"Error saving or loading GraphML file: {e}")
                return

        st.success("Done!")

if __name__ == "__main__":
    app()
