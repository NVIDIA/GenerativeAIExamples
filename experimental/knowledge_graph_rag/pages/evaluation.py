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
from utils.preprocessor import generate_qa_pair
from llama_index.core import ServiceContext
import multiprocessing
import pandas as pd
import networkx as nx
from utils.lc_graph import process_documents, save_triples_to_csvs
from vectorstore.search import SearchHandler
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import random
import pandas as pd
import time
import json
from langchain_core.output_parsers import StrOutputParser
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph, get_entities
from langchain_core.prompts import ChatPromptTemplate

from vectorstore.search import SearchHandler

from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
reward_client = OpenAI(
    base_url = "https://integrate.api.nvidia.com/v1",
    api_key = os.environ["NVIDIA_API_KEY"]
)

def get_reward_scores(question, answer):
    completion = reward_client.chat.completions.create(
        model="nvidia/nemotron-4-340b-reward",
        messages=[{"role": "user", "content":question}, {"role":"assistant", "content":answer}]
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

def process_question(question, answer):
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_text = executor.submit(get_text_RAG_response, question)
        future_graph = executor.submit(get_graph_RAG_response, question)
        future_combined = executor.submit(get_combined_RAG_response, question)

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

def load_data(input_dir, num_workers):
    reader = SimpleDirectoryReader(input_dir=input_dir)
    documents = reader.load_data(num_workers=num_workers)
    return documents

def has_pdf_files(directory):
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            return True
    return False

def get_text_RAG_response(question):
    chain = prompt_template | llm | StrOutputParser()

    search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)
    res = search_handler.search_and_rerank(question, k=5)
    context = "Here are the relevant passages from the knowledge base: \n\n" + "\n".join(item.text for item in res)
    answer = chain.invoke("Context: " + context + "\n\nUser query: " + question)
    return answer

def get_graph_RAG_response(question):
    chain = prompt_template | llm | StrOutputParser()
    entity_string = llm.invoke("""Return a JSON with a single key 'entities' and list of entities within this user query. Each element in your list MUST BE part of the user's query. Do not provide any explanation. If the returned list is not parseable in Python, you will be heavily penalized. For example, input: 'What is the difference between Apple and Google?' output: ['Apple', 'Google']. Always follow this output format. Here's the user query: """ + question)
    G =  nx.read_graphml("knowledge_graph.graphml")
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

def get_combined_RAG_response(question):
    chain = prompt_template | llm | StrOutputParser()
    entity_string = llm.invoke("""Return a JSON with a single key 'entities' and list of entities within this user query. Each element in your list MUST BE part of the user's query. Do not provide any explanation. If the returned list is not parseable in Python, you will be heavily penalized. For example, input: 'What is the difference between Apple and Google?' output: ['Apple', 'Google']. Always follow this output format. Here's the user query: """ + question)
    G =  nx.read_graphml("knowledge_graph.graphml")
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

st.title("Evaluations")

st.subheader("Create synthetic Q&A pairs from large document chunks")

# Variable for documents
if 'documents' not in st.session_state:
    st.session_state['documents'] = None

with st.sidebar:
    llm_selectbox = st.selectbox("Choose an LLM", ["nvidia/nemotron-4-340b-instruct", "mistralai/mixtral-8x7b-instruct-v0.1", "meta/llama3-70b-instruct"], index=0)
    st.write("You selected: ", llm_selectbox)
    llm = ChatNVIDIA(model=llm_selectbox)

    num_data = st.slider("How many Q&A pairs to generate?", 10, 100, 50, step=10)

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
        documents, results = process_documents(directory, llm, triplets=False, chunk_size=2000, chunk_overlap=200)
        st.session_state["documents"] = documents
        st.success("Finished splitting documents!")

    json_list = []
    if st.session_state["documents"] is not None:
        if st.button("Create Q&A pairs"):
            qa_docs = random.sample(st.session_state["documents"], num_data)
            for doc in qa_docs:
                res = generate_qa_pair(doc, llm)
                st.write(res)
                if res:
                    json_list.append(res)

    if len(json_list) > 0:
        df = pd.DataFrame(json_list)
        df.to_csv('qa_data.csv', index=False)    
    
    if os.path.exists("qa_data.csv"):
        with st.expander("Load Q&A data and run evaluations of text vs graph vs text+graph RAG"):
            if st.button("Run"):
                df_csv = pd.read_csv("qa_data.csv")
                questions_list = df_csv["question"].tolist()
                answers_list = df_csv["answer"].tolist()
                
                # Create an empty DataFrame to store results
                results_df = pd.DataFrame(columns=[
                    "question", "gt_answer", "textRAG_answer", 
                    "graphRAG_answer", "combined_answer"
                ])
                
                # Create a placeholder for the DataFrame
                df_placeholder = st.empty()
                
                # Create a progress bar
                progress_bar = st.progress(0)
                
                # Process questions
                for i, (question, answer) in enumerate(zip(questions_list, answers_list)):
                    result = process_question(question, answer)
                    
                    # Add new row to results_df
                    new_row = pd.DataFrame([result])
                    results_df = pd.concat([results_df, new_row], ignore_index=True)
                    
                    # Update the displayed DataFrame
                    df_placeholder.dataframe(results_df)
                    
                    # Update progress bar
                    progress_bar.progress((i + 1) / len(questions_list))
                
                # Optionally, save the combined results to a new CSV file
                results_df.to_csv("combined_results.csv", index=False)
                st.success("Combined results saved to 'combined_results.csv'")

    if os.path.exists("combined_results.csv"):
        with st.expander("Run comparative evals for saved Q&A data"):
            if st.button("Run scoring"):
                combined_results = pd.read_csv("combined_results.csv")

                # Initialize new columns for scores
                score_columns = ['gt', 'textRAG', 'graphRAG', 'combinedRAG']
                metrics = ['helpfulness', 'correctness', 'coherence', 'complexity', 'verbosity']
                
                for row in range(len(combined_results)):
                    res_gt = get_reward_scores(combined_results["question"][row], combined_results["gt_answer"][row])

                    res_textRAG = get_reward_scores(combined_results["question"][row], combined_results["textRAG_answer"][row])

                    res_graphRAG = get_reward_scores(combined_results["question"][row], combined_results["graphRAG_answer"][row])

                    res_combinedRAG = get_reward_scores(combined_results["question"][row], combined_results["combined_answer"][row])

                     # Add scores to the DataFrame
                    for score_type, res in zip(score_columns, [res_gt, res_textRAG, res_graphRAG, res_combinedRAG]):
                        for metric in metrics:
                            combined_results.at[row, f'{score_type}_{metric}'] = res[metric]

                    # Display progress
                    if row % 10 == 0:  # Update every 10 rows
                        st.write(f"Processed {row + 1} out of {len(combined_results)} rows")

                    # Save the updated DataFrame
                combined_results.to_csv("combined_results_with_scores.csv", index=False)
                st.success("Evaluation complete. Results saved to 'combined_results_with_scores.csv'")

                # Display the first few rows of the updated DataFrame
                st.write("First few rows of the updated data:")
                st.dataframe(combined_results.head())

if __name__ == "__main__":
    app()