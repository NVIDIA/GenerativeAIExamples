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

from langchain_nvidia_ai_endpoints import ChatNVIDIA
import concurrent.futures
import os
from tqdm import tqdm
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import multiprocessing
import csv
import streamlit as st
from utils.preprocessor import extract_triples
# function to process a single document (will run many of these processes in parallel)
def process_document(doc, llm):
    try:
        return extract_triples(doc, llm)
    except Exception as e:
        print(f"Error processing document: {e}")
        return []

def process_documents(directory, llm, update_progress=None,triplets=True, chunk_size=500, chunk_overlap=100):    
    with st.spinner("Loading and splitting documents"):
        loader = DirectoryLoader(directory)
        raw_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        documents = text_splitter.split_documents(raw_docs)
        st.write("Loaded docs, len(docs): " + str(len(documents)))
        # Save documents to CSV
    document_data = [{"id": i, "content": doc.page_content} for i, doc in enumerate(documents)]
    df = pd.DataFrame(document_data)
    #df.to_csv('documents.csv', index=False)
    df = pd.DataFrame(document_data)

    # Define the data directory and ensure it exists
    data_directory = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_directory, exist_ok=True)

    # Define the path for the documents.csv file
    documents_csv_path = os.path.join(data_directory, 'documents.csv')

    # Save the documents to CSV in the data directory
    df.to_csv(documents_csv_path, index=False)
    print(f"Documents saved to {documents_csv_path}")

    if not triplets:
        return documents, []

    multiprocessing.set_start_method('fork', force=True)

    progress_bar = st.progress(0)  # Initialize the progress bar
    progress_text = st.empty()  # Create a placeholder for the progress text

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_document, doc, llm) for doc in documents]
        results = []
        total_futures = len(futures)
        completed_futures = 0

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.extend(result)
            except Exception as e:
                print(f"Error collecting result: {e}")

            completed_futures += 1
            progress = completed_futures / total_futures
            if update_progress:
                update_progress(completed_futures, total_futures)
            progress_bar.progress(progress)  # Update the progress bar
            progress_text.text(f"Processing: {completed_futures}/{total_futures}")  # Update the progress text

    print("Processing complete. Total triples extracted:", len(results))
    return documents, results

import pandas as pd

def save_triples_to_csvs(triples):
    data_directory = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_directory, exist_ok=True)

    # Define paths for the CSV files
    entities_csv_path = os.path.join(data_directory, 'entities.csv')
    relations_csv_path = os.path.join(data_directory, 'relations.csv')
    triples_csv_path = os.path.join(data_directory, 'triples.csv')
    # Create the triples DataFrame
    triples_df = pd.DataFrame(triples, columns=['subject', 'subject_type', 'relation', 'object', 'object_type'])

    # Create the relations DataFrame
    relations_df = pd.DataFrame({'relation_id': range(len(triples_df['relation'].unique())), 'relation_name': triples_df['relation'].unique()})

    # Get unique entities (subjects and objects) from triples_df
    entities = pd.concat([triples_df['subject'], triples_df['object']]).unique()

    entities_df = pd.DataFrame({
    'entity_name': entities,
    'entity_type': [
        triples_df.loc[triples_df['subject'] == entity, 'subject_type'].iloc[0]
        if entity in triples_df['subject'].values
        else triples_df.loc[triples_df['object'] == entity, 'object_type'].dropna().iloc[0]
             if not triples_df.loc[triples_df['object'] == entity, 'object_type'].empty
             else 'Unknown'
        for entity in entities
        ]
    })
    entities_df = entities_df.reset_index().rename(columns={'index': 'entity_id'})

    # Merge triples_df with entities_df for subject
    triples_with_ids = triples_df.merge(entities_df[['entity_id', 'entity_name']], left_on='subject', right_on='entity_name', how='left')
    triples_with_ids = triples_with_ids.rename(columns={'entity_id': 'entity_id_1'}).drop(columns=['entity_name', 'subject', 'subject_type'])

    # Merge triples_with_ids with entities_df for object
    triples_with_ids = triples_with_ids.merge(entities_df[['entity_id', 'entity_name']], left_on='object', right_on='entity_name', how='left')
    triples_with_ids = triples_with_ids.rename(columns={'entity_id': 'entity_id_2'}).drop(columns=['entity_name', 'object', 'object_type'])

    # Merge triples_with_ids with relations_df to get relation IDs
    triples_with_ids = triples_with_ids.merge(relations_df, left_on='relation', right_on='relation_name', how='left').drop(columns=['relation', 'relation_name'])

    # Select necessary columns and ensure correct data types
    result_df = triples_with_ids[['entity_id_1', 'relation_id', 'entity_id_2']].astype({'entity_id_1': int, 'relation_id': int, 'entity_id_2': int})

    # Write DataFrames to CSV files
    # entities_df.to_csv('entities.csv', index=False)
    # relations_df.to_csv('relations.csv', index=False)
    # result_df.to_csv('triples.csv', index=False)
    entities_df.to_csv(entities_csv_path, index=False)
    relations_df.to_csv(relations_csv_path, index=False)
    result_df.to_csv(triples_csv_path, index=False)

if __name__ == "__main__":
    llm = ChatNVIDIA(model="ai-mixtral-8x7b-instruct")
    results = process_documents("papers/", llm)

    # write the resulting entities to a CSV, relations to a CSV and all triples with IDs to a CSV
    save_triples_to_csvs(results)

    # load the CSV triples, entities and relations into pandas objects (accelerated by cuDF/cuGraph)
    import pandas as pd
    import networkx as nx

    # # Load the triples from the CSV file
    # triples_df = pd.read_csv("triples.csv", header=None, names=["Entity1_ID", "relation", "Entity2_ID"])

    # # Load the entities and relations DataFrames
    # entity_df = pd.read_csv("entities.csv", header=None, names=["ID", "Entity"])
    # relations_df = pd.read_csv("relations.csv", header=None, names=["ID", "relation"])
    triples_df = pd.read_csv(os.path.join(data_directory, "triples.csv"), header=None, names=["Entity1_ID", "relation", "Entity2_ID"])
    entity_df = pd.read_csv(os.path.join(data_directory, "entities.csv"), header=None, names=["ID", "Entity"])
    relations_df = pd.read_csv(os.path.join(data_directory, "relations.csv"), header=None, names=["ID", "relation"])

    # Create a mapping from IDs to entity names and relation names
    entity_name_map = entity_df.set_index("ID")["Entity"].to_dict()
    relation_name_map = relations_df.set_index("ID")["relation"].to_dict()

    # Create the graph from the triples DataFrame using accelerated networkX-cuGraph integration
    G = nx.from_pandas_edgelist(
        triples_df,
        source="Entity1_ID",
        target="Entity2_ID",
        edge_attr="relation",
        create_using=nx.DiGraph,
    )

    # Relabel the nodes with the actual entity names
    G = nx.relabel_nodes(G, entity_name_map)

    # Relabel the edges with the actual relation names
    edge_attributes = nx.get_edge_attributes(G, "relation")
    nx.set_edge_attributes(G, {(u, v): relation_name_map[edge_attributes[(u, v)]] for u, v in G.edges()}, "relation")

    # Save the graph to a GraphML file so it can be visualized in Gephi Lite
    graphml_path = os.path.join(data_directory, "knowledge_graph.graphml")

    #nx.write_graphml(G, "knowledge_graph.graphml")
    nx.write_graphml(G, graphml_path)

    # Query the graph using LangChain
    from langchain.chains import GraphQAChain
    from langchain.indexes.graph import NetworkxEntityGraph
    graph = NetworkxEntityGraph(G)
    # print(graph.get_triples())

    # llm.invoke("hello")
    chain = GraphQAChain.from_llm(llm = llm, graph=graph, verbose=True)
    res = chain.run("explain how URDFormer and vision transformer is related")
    print(res)
