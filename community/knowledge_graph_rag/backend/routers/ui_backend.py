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
import pandas as pd
import networkx as nx
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.lc_graph import process_documents, save_triples_to_csvs
from vectorstore.search import SearchHandler
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
load_dotenv()

# Get the data directory path from environment variables
DATA_DIR = os.getenv("DATA_DIR") 


# Initialize a FastAPI router
router = APIRouter()

# Define a Pydantic model for the request body
class DirectoryRequest(BaseModel):
    directory: str
    model_id: str
# Define an endpoint to get available models
@router.get("/get-models/")
async def get_models():
    models = ChatNVIDIA.get_available_models()
    available_models = [model.id for model in models if model.model_type == "chat" and "instruct" in model.id]
    return {"models": available_models}

# Define an endpoint to process documents
@router.post("/process-documents/")
async def process_documents_endpoint(request: DirectoryRequest, background_tasks: BackgroundTasks):
    directory = request.directory
    model_id = request.model_id
    llm = ChatNVIDIA(model=model_id)

    # Save progress updates in a temporary file
    progress_file = "progress.txt"
    with open(progress_file, "w") as f:
        f.write("0")

    def update_progress(completed_futures, total_futures):
        progress = completed_futures / total_futures
        with open(progress_file, "w") as f:
            f.write(str(progress))
    # Define a background task for processing documents
    def background_task():
        documents, results = process_documents(directory, llm, update_progress=update_progress)
        search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)
        search_handler.insert_data(documents)
        save_triples_to_csvs(results)
        
        # Load data from CSV files
        triples_csv_path = os.path.join(DATA_DIR, "triples.csv")
        entities_csv_path = os.path.join(DATA_DIR, "entities.csv")
        relations_csv_path = os.path.join(DATA_DIR, "relations.csv")
        triples_df = pd.read_csv(triples_csv_path)
        entities_df = pd.read_csv(entities_csv_path)
        relations_df = pd.read_csv(relations_csv_path)

        entity_name_map = entities_df.set_index("entity_id")["entity_name"].to_dict()
        relation_name_map = relations_df.set_index("relation_id")["relation_name"].to_dict()
        
        # Create a graph from the triples data
        G = nx.from_pandas_edgelist(
            triples_df,
            source="entity_id_1",
            target="entity_id_2",
            edge_attr="relation_id",
            create_using=nx.DiGraph,
        )

        G = nx.relabel_nodes(G, entity_name_map)
        edge_attributes = nx.get_edge_attributes(G, "relation_id")

        new_edge_attributes = {
            (u, v): relation_name_map[edge_attributes[(u, v)]]
            for u, v in G.edges()
            if edge_attributes[(u, v)] in relation_name_map
        }
        nx.set_edge_attributes(G, new_edge_attributes, "relation")

       # Save the graph to a GraphML file
        graphml_path = os.path.join(DATA_DIR, "knowledge_graph.graphml")
        nx.write_graphml(G, graphml_path)

    background_tasks.add_task(background_task)
    return {"message": "Processing started"}
# Define an endpoint to get the progress of the background task
@router.get("/progress/")
async def get_progress():
    try:
        with open("progress.txt", "r") as f:
            progress = f.read()
        return {"progress": progress}
    except FileNotFoundError:
        return {"progress": "0"}

# Define an endpoint to check if the GraphML file exists
@router.get("/check-file-exists/")
async def check_file_exists():
    graphml_path = os.path.join(DATA_DIR, "knowledge_graph.graphml")
    if os.path.exists(graphml_path):
        return JSONResponse(content={"file_exists": True})
    else:
        return JSONResponse(content={"file_exists": False})