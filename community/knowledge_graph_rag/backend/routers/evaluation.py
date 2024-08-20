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
import asyncio
import random
import pandas as pd
import networkx as nx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.chains import GraphQAChain
from vectorstore.search import SearchHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from utils.preprocessor import generate_qa_pair
from utils.lc_graph import process_documents, save_triples_to_csvs
from llama_index.core import SimpleDirectoryReader
from openai import OpenAI
from langchain.schema import Document
import csv 
import json
import time
import logging
import os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessRequest(BaseModel):
    directory: str
    model_id: str

class QAPairsRequest(BaseModel):
    num_data: int
    model_id: str
    

class QARequest(BaseModel):
    questions_list: list
    answers_list: list
    model_id: str

class ScoreRequest(BaseModel):
    combined_results: list

reward_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)
@router.get("/get-models/")
async def get_models():
    models = ChatNVIDIA.get_available_models()
    available_models = [model.id for model in models if model.model_type == "chat" and "instruct" in model.id]
    return {"models": available_models}

def load_data(input_dir, num_workers):
    reader = SimpleDirectoryReader(input_dir=input_dir)
    documents = reader.load_data(num_workers=num_workers)
    return documents

def get_reward_scores(question, answer):
    completion = reward_client.chat.completions.create(
        model="nvidia/nemotron-4-340b-reward",
        messages=[{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    )
    try:
        content = completion.choices[0].message[0].content
        res = content.split(",")
        content_dict = {}
        for item in res:
            name, val = item.split(":")
            content_dict[name] = float(val)
        return content_dict
    except:
        return None

def process_question(question, answer, llm):
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_text = executor.submit(get_text_RAG_response, question, llm)
        future_graph = executor.submit(get_graph_RAG_response, question, llm)
        future_combined = executor.submit(get_combined_RAG_response, question, llm)

        text_RAG_response = future_text.result()
        graph_RAG_response = future_graph.result()
        combined_RAG_response = future_combined.result()

    return {
        "question": question,
        "gt_answer": answer,
        "textRAG_answer": text_RAG_response,
        "graphRAG_answer": graph_RAG_response,
        "combined_answer": combined_RAG_response
    }

prompt_template = ChatPromptTemplate.from_messages(
    [("system", "You are a helpful AI assistant named Envie. You will reply to questions only based on the context that you are provided. If something is out of context, you will refrain from replying and politely decline to respond to the user."), ("user", "{input}")]
)

DATA_DIR = os.getenv("DATA_DIR") 
KG_GRAPHML_PATH = os.path.join(DATA_DIR, "knowledge_graph.graphml")
logger.info(KG_GRAPHML_PATH)


def get_text_RAG_response(question, llm):
    chain = prompt_template | llm | StrOutputParser()
    search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)
    res = search_handler.search_and_rerank(question, k=5)
    context = "Here are the relevant passages from the knowledge base: \n\n" + "\n".join(item.text for item in res)
    answer = chain.invoke("Context: " + context + "\n\nUser query: " + question)
    return answer

def get_graph_RAG_response(question, llm):
    chain = prompt_template | llm | StrOutputParser()
    entity_string = llm.invoke("""Return a JSON with a single key 'entities' and list of entities within this user query. Each element in your list MUST BE part of the user's query. Do not provide any explanation. If the returned list is not parseable in Python, you will be heavily penalized. For example, input: 'What is the difference between Apple and Google?' output: ['Apple', 'Google']. Always follow this output format. Here's the user query: """ + question)
    graphml_path = KG_GRAPHML_PATH 
    
    G = nx.read_graphml(graphml_path)
    
    graph = NetworkxEntityGraph(G)

    try:
        entities = json.loads(entity_string.content)['entities']
        context = ""
        all_triplets = []
        for entity in entities:
            all_triplets.extend(graph.get_entity_knowledge(entity, depth=2))
        context = "Here are the relationships from the knowledge graph: " + "\n".join(all_triplets)
    except:
        context = "No graph triples were available to extract from the knowledge graph. Always provide a disclaimer if you know the answer to the user's question, since it is not grounded in the knowledge you are provided from the graph."
    answer = chain.invoke("Context: " + context + "\n\nUser query: " + question)
    return answer

def get_combined_RAG_response(question, llm):
    chain = prompt_template | llm | StrOutputParser()
    entity_string = llm.invoke("""Return a JSON with a single key 'entities' and list of entities within this user query. Each element in your list MUST BE part of the user's query. Do not provide any explanation. If the returned list is not parseable in Python, you will be heavily penalized. For example, input: 'What is the difference between Apple and Google?' output: ['Apple', 'Google']. Always follow this output format. Here's the user query: """ + question)
    graphml_path = KG_GRAPHML_PATH 
    G = nx.read_graphml(graphml_path)
    graph = NetworkxEntityGraph(G)

    try:
        entities = json.loads(entity_string.content)['entities']
        search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)
        res = search_handler.search_and_rerank(question, k=5)
        context = "Here are the relevant passages from the knowledge base: \n\n" + "\n".join(item.text for item in res)
        all_triplets = []
        for entity in entities:
            all_triplets.extend(graph.get_entity_knowledge(entity, depth=2))
        context += "\n\nHere are the relationships from the knowledge graph: " + "\n".join(all_triplets)
    except Exception as e:
        context = "No graph triples were available to extract from the knowledge graph. Always provide a disclaimer if you know the answer to the user's question, since it is not grounded in the knowledge you are provided from the graph."
    answer = chain.invoke("Context: " + context + "\n\nUser query: " + question)
    return answer

@router.post("/process-documents/")
async def process_documents_endpoint(request: ProcessRequest, background_tasks: BackgroundTasks):
    logger.info("Check")
    directory = request.directory
    model_id = request.model_id
    llm = ChatNVIDIA(model=model_id)
    logger.info(f"Processing documents in directory: {directory} with model: {model_id}")
    try:
        documents, results = process_documents(directory, llm, triplets=False, chunk_size=2000, chunk_overlap=200)
        logger.info(f"Processed {len(documents)} documents.")
        data_directory = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_directory, exist_ok=True)

    # Define the path for the documents.csv file
        documents_csv_path = os.path.join(data_directory, 'documents.csv')
        logger.info(f"Path to documents.csv: {documents_csv_path}")
        return {"message": "Document processing started", "documents_processed": len(documents)}
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        raise HTTPException(status_code=500, detail="Error processing documents")
@router.post("/create-qa-pairs/")
async def create_qa_pairs(request: QAPairsRequest):
    logger.info("Entered create_qa_pairs endpoint")
    
    num_data = request.num_data
    model_id = request.model_id
    llm = ChatNVIDIA(model=model_id)

    current_directory = os.getcwd()
    data_directory = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_directory, exist_ok=True)

    # Define the path for the documents.csv file
    documents_csv_path = os.path.join(data_directory, 'documents.csv')
    logger.info(f"Path to documents.csv in QA: {documents_csv_path}")
    
    logger.info(f"Current working directory: {current_directory}")
    logger.info(f"Path to documents.csv: {documents_csv_path}")
    
    if not os.path.exists(documents_csv_path):
        logger.error("Documents not found. Please process documents first.")
        raise HTTPException(status_code=404, detail="Documents not found. Please process documents first.")
    
    df = pd.read_csv(documents_csv_path)
    documents = [Document(page_content=row['content']) for index, row in df.iterrows()]
    logger.info(f"Total documents available: {len(documents)}")
    
    async def event_generator():
        json_list = []
        qa_docs = random.sample(documents, num_data)
        for doc in qa_docs:
            try:
                res = generate_qa_pair(doc, llm)
                if res:
                    # Append to list and write to file incrementally if needed
                    json_list.append(res)
                    yield json.dumps(res) + "\n"
                    await asyncio.sleep(1)  # Simulate processing time
            except Exception as e:
                logger.error(f"Error generating Q&A pair: {e}")
                yield json.dumps({"error": str(e)}) + "\n"

        # Save the list to a file after processing all documents
        if json_list:

            qa_df = pd.DataFrame(json_list)
            data_directory = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_directory, exist_ok=True)
            qa_df_path = os.path.join(data_directory, 'qa_data.csv')
            qa_df.to_csv(qa_df_path, index=False)
            logger.info("qa_data.csv created successfully.")
        else:
            logger.error("No Q&A pairs generated")
            raise HTTPException(status_code=500, detail="No Q&A pairs generated")
        

    return StreamingResponse(event_generator(), media_type="text/event-stream")
@router.post("/run-evaluation/")
async def run_evaluation(request: QARequest):
    questions_list = request.questions_list
    answers_list = request.answers_list
    model_id = request.model_id
    llm = ChatNVIDIA(model=model_id)  # or any other default model

    
    async def evaluate():
        results = []
        for question, answer in zip(questions_list, answers_list):
            result = process_question(question, answer, llm)
            results.append(result)

            # Save the result to the CSV file incrementally
            data_directory = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_directory, exist_ok=True)

            combined_results_path = os.path.join(DATA_DIR, "combined_results.csv")
            with open(combined_results_path, "a", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=result.keys())
                if csvfile.tell() == 0:
                    writer.writeheader()
                writer.writerow(result)

            yield json.dumps(result) + "\n"
            await asyncio.sleep(0.1) 
    
    return StreamingResponse(evaluate(), media_type="text/event-stream")

@router.post("/run-scoring/")
async def run_scoring(request: ScoreRequest):
    combined_results = request.combined_results

    score_columns = ['gt', 'textRAG', 'graphRAG', 'combinedRAG']
    metrics = ['helpfulness', 'correctness', 'coherence', 'complexity', 'verbosity']
    
    async def score_generator():
        for row in combined_results:
            try:
                res_gt = get_reward_scores(row["question"], row["gt_answer"])
                res_textRAG = get_reward_scores(row["question"], row["textRAG_answer"])
                res_graphRAG = get_reward_scores(row["question"], row["graphRAG_answer"])
                res_combinedRAG = get_reward_scores(row["question"], row["combined_answer"])

                for score_type, res in zip(score_columns, [res_gt, res_textRAG, res_graphRAG, res_combinedRAG]):
                     if res:
                        for metric in metrics:
                            row[f'{score_type}_{metric}'] = res.get(metric,None)
                yield json.dumps(row) + "\n"
                await asyncio.sleep(0.1)  # Simulate processing delay
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(score_generator(), media_type="text/event-stream")

    