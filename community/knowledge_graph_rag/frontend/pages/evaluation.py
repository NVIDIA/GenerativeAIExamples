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
import requests
import pandas as pd
import json
from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
DATA_DIR = os.getenv("DATA_DIR") 




# Custom CSS to change heading font sizes
st.markdown("""
    <style>
    h1, h2, h3, h4, h5, h6 {
        font-size: 1.2em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Evaluations")

st.subheader("Create synthetic Q&A pairs from large document chunks")

if 'documents' not in st.session_state:
    st.session_state['documents'] = None
if 'qa_pairs' not in st.session_state:
    st.session_state['qa_pairs'] = []
if 'evaluation_results' not in st.session_state:
    st.session_state['evaluation_results'] = []

response = requests.get(f"{BACKEND_URL}/evaluation/get-models/")
if response.status_code == 200:
    available_models = response.json()["models"]
else:
    st.error("Error fetching models.")
    available_models = []

with st.sidebar:
    llm_selectbox = st.selectbox("Choose an LLM", available_models, index=available_models.index("mistralai/mixtral-8x7b-instruct-v0.1") if "mistralai/mixtral-8x7b-instruct-v0.1" in available_models else 0)
    st.write("You selected: ", llm_selectbox)

    num_data = st.slider("How many Q&A pairs to generate?", 10, 100, 50, step=10)

def has_pdf_files(directory):
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            return True
    return False

def app():
    cwd = os.getcwd()
    directories = [d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d)) and not d.startswith('.') and '__' not in d]
    selected_dir = st.selectbox("Select a directory:", directories, index=0)
    directory = os.path.join(cwd, selected_dir)

    # Process Documents
    with st.container():
        st.markdown("### 1. Process Documents")
        if st.button("Process Documents"):
            res = has_pdf_files(directory)
            if not res:
                st.error("No PDF files found in directory! Only PDF files and text extraction are supported for now.")
                st.stop()
            progress_bar = st.progress(0)

            process_response = requests.post(
                f"{BACKEND_URL}/evaluation/process-documents/",
                json={"directory": directory, "model_id": llm_selectbox}
            )
            if process_response.status_code == 200:
                st.session_state["documents"] = process_response.json().get("documents_processed")
                st.success(f"Finished splitting documents! Number of documents processed: {st.session_state['documents']}")
                progress_bar.progress(100)
            else:
                st.error("Error processing documents.")
                progress_bar.progress(0)

   

    # Create Q&A pairs
    with st.container():
        st.markdown("### 2. Create synthetic Q&A pairs from large document chunks")
        if st.session_state["documents"] is not None:
            if st.button("Create Q&A pairs"):
                qa_placeholder = st.empty()
                json_list = []
                progress_bar = st.progress(0)
                try:
                    qa_response = requests.post(
                        f"{BACKEND_URL}/evaluation/create-qa-pairs/",
                        json={"num_data": num_data, "model_id": llm_selectbox},
                        stream=True
                    )
                    if qa_response.status_code == 200:
                        total_lines = 0 
                        for line in qa_response.iter_lines():
                            if line:
                                try:
                                    pair = json.loads(line.decode('utf-8'))
                                    if 'question' in pair and 'answer' in pair:
                                        res = {
                                            'question': pair['question'],
                                            'answer': pair['answer']
                                        }
                                        st.write(res)
                                        json_list.append(res)
                                        total_lines += 1
                                        progress_bar.progress(min(total_lines / num_data, 1.0))  # Update progress
                                    else:
                                        st.error("Received data in an unexpected format.")
                                        st.write(pair)  # For debugging purposes
                                except json.JSONDecodeError:
                                    st.error("Error decoding JSON response.")
                        st.session_state['qa_pairs'] = json_list
                        st.success("Q&A pair generation completed.")
                        progress_bar.progress(100)
                    else:
                        st.error("Error creating Q&A pairs.")
                        progress_bar.progress(0)
                except requests.exceptions.ChunkedEncodingError as e:
                    st.error(f"Streaming error: {e}")
                    progress_bar.progress(0)
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    progress_bar.progress(0)

    
    # Run Evaluation
    QA_DATA_PATH = os.path.join(DATA_DIR, "qa_data.csv")
   
    if os.path.exists(QA_DATA_PATH):
        with st.container():
            st.markdown("### 3. Load Q&A data and run evaluations of text vs graph vs text+graph RAG")
            if st.button("Run Evaluation"):
                df_csv = pd.read_csv(QA_DATA_PATH)
                questions_list = df_csv["question"].tolist()
                answers_list = df_csv["answer"].tolist()
                eval_placeholder = st.empty()
                results = []
                progress_bar = st.progress(0)
                total_questions = len(questions_list)

                try:
                    eval_response = requests.post(
                        f"{BACKEND_URL}/evaluation/run-evaluation/",
                        json={"questions_list": questions_list, "answers_list": answers_list, "model_id": llm_selectbox},
                        stream=True
                    )
                    if eval_response.status_code == 200:
                        for index, line in enumerate(eval_response.iter_lines()):
                            if line:
                                try:
                                    result = json.loads(line.decode('utf-8'))
                                    if 'question' in result and 'gt_answer' in result:
                                        results.append(result)
                                        st.session_state['evaluation_results'] = results
                                        # Update the displayed DataFrame
                                        results_df = pd.DataFrame(results)
                                        eval_placeholder.dataframe(results_df)
                                        progress_bar.progress(min((index + 1) / total_questions, 1.0))  # Update progress
                                    else:
                                        st.error("Received data in an unexpected format.")
                                        st.write(result)  # For debugging purposes
                                except json.JSONDecodeError:
                                    st.error("Error decoding JSON response.")
                        # Success message displayed after processing all lines
                        st.success("Combined results saved to 'combined_results.csv'")
                        progress_bar.progress(100)
                    else:
                        st.error("Error running evaluations.")
                except requests.exceptions.ChunkedEncodingError as e:
                    st.error(f"Streaming error: {e}")
                    progress_bar.progress(0)

                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    progress_bar.progress(0)
    
        


    # Run Scoring
    COMBINED_RESULTS_PATH = os.path.join(DATA_DIR, "combined_results.csv")
    if os.path.exists(COMBINED_RESULTS_PATH):
        with st.container():
            st.markdown("### 4. Run comparative evals for saved Q&A data")
            if st.button("Run Scoring"):
                combined_results = pd.read_csv(COMBINED_RESULTS_PATH).to_dict(orient="records")
                score_response = None
                score_placeholder = st.empty()
                results = []
                total_items = len(combined_results)
                progress_bar = st.progress(0)


                score_response = requests.post(
                    f"{BACKEND_URL}/evaluation/run-scoring/",
                    json={"combined_results": combined_results}, 
                    stream=True
                )
                if score_response.status_code == 200:
                    for index,line in enumerate(score_response.iter_lines()):
                        if line:
                            try:
                                result = json.loads(line.decode('utf-8'))
                                if 'question' in result and 'gt_answer' in result:
                                    results.append(result)
                                    # Update the displayed DataFrame incrementally
                                    results_df = pd.DataFrame(results)
                                    score_placeholder.dataframe(results_df)
                                    progress_bar.progress(min((index + 1) / total_items, 1.0))  # Update progress
                                else:
                                    st.error("Received data in an unexpected format.")
                                    st.write(result)  # For debugging purposes
                            except json.JSONDecodeError:
                                st.error("Error decoding JSON response.")
                    # Success message displayed after processing all lines
                    st.success("Scoring completed and results saved to 'combined_results_with_scores.csv.")
                    # Save the final results to a CSV file
                    COMBINED_RESULTS_PATH_WITH_SCORES=os.path.join(DATA_DIR, "combined_results_with_scores.csv")
                    pd.DataFrame(results).to_csv(COMBINED_RESULTS_PATH_WITH_SCORES, index=False)
                    progress_bar.progress(100)
                else:
                    st.error("Error running scoring.")
                    progress_bar.progress(0)

if __name__ == "__main__":
    app()
