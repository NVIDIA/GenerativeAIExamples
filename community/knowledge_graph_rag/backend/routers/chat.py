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
import json
import networkx as nx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.chains import GraphQAChain
from vectorstore.search import SearchHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Define a Pydantic model for the chat request body
class ChatRequest(BaseModel):
    user_input: str
    use_kg: bool
    model_id: str

# # Load the knowledge graph path from environment variables
DATA_DIR = os.getenv("DATA_DIR")
KG_GRAPHML_PATH = os.path.join(DATA_DIR, "knowledge_graph.graphml")

# Define an endpoint to get available models
@router.get("/get-models/")
async def get_models():
    models = ChatNVIDIA.get_available_models()
    available_models = [model.id for model in models if model.model_type == "chat" and "instruct" in model.id]
    return {"models": available_models}

# Define an endpoint for the chat interface
@router.post("/chat/")
async def chat_endpoint(request: ChatRequest):
    response_data = {"user_input": request.user_input, "use_kg": request.use_kg}
    llm = ChatNVIDIA(model=request.model_id)
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", "You are a helpful AI assistant named Envie. You will reply to questions only based on the context that you are provided. If something is out of context, you will refrain from replying and politely decline to respond to the user."), ("user", "{input}")]
    )
    chain = prompt_template | llm | StrOutputParser()


    if request.use_kg:
        DATA_DIR = os.getenv("DATA_DIR")
        KG_GRAPHML_PATH = os.path.join(DATA_DIR, "knowledge_graph.graphml")

        logger.info(f"Entering {KG_GRAPHML_PATH}")
        if os.path.exists(KG_GRAPHML_PATH):
            G = nx.read_graphml(KG_GRAPHML_PATH)
            graph = NetworkxEntityGraph(G)
            graph_available = True
        else:
            logger.error(f"Knowledge graph not found at {KG_GRAPHML_PATH}")
            graph_available = False

        if not graph_available:
            return {"assistant_response": "The knowledge graph is currently unavailable. Please try again later."}
        
        llm = ChatNVIDIA(model=request.model_id)
        graph_chain = GraphQAChain.from_llm(llm=llm, graph=graph, verbose=True)
        
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", "You are a helpful AI assistant named Envie. You will reply to questions only based on the context that you are provided. If something is out of context, you will refrain from replying and politely decline to respond to the user."), ("user", "{input}")]
        )
        chain = prompt_template | llm | StrOutputParser()
        search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)
    
        user_input = request.user_input
        use_kg = request.use_kg
    
        try:
            entity_string = llm.invoke("""Return a JSON with a single key 'entities' and list of entities within this user query. Each element in your list MUST BE part of the user's query. Do not provide any explanation. If the returned list is not parseable in Python, you will be heavily penalized. For example, input: 'What is the difference between Apple and Google?' output: ['Apple', 'Google']. Always follow this output format. Here's the user query: """ + user_input)
            entities = json.loads(entity_string.content)['entities']
            res = search_handler.search_and_rerank(user_input, k=5)
            context = "Here are the relevant passages from the knowledge base: \n\n" + "\n".join(item.text for item in res)
            all_triplets = []
            for entity in entities:
                all_triplets.extend(graph_chain.graph.get_entity_knowledge(entity, depth=2))
            context += "\n\nHere are the relationships from the knowledge graph: " + "\n".join(all_triplets)
            response_data["context"] = context
        except Exception as e:
            response_data["context"] = "No graph triples were available to extract from the knowledge graph. Always provide a disclaimer if you know the answer to the user's question, since it is not grounded in the knowledge you are provided from the graph."
    else:
        response_data["context"] = ""

    full_response = llm.invoke(f"Context: {response_data['context']}\n\nUser query: {request.user_input}" if request.use_kg else request.user_input)
    response_data["assistant_response"] = full_response if isinstance(full_response, str) else full_response.content

    return response_data
