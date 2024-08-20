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
import time
import requests
import pickle
import json
from bot_config.utils import get_config
from vectorstore.vectorstore_updater import update_vectorstore, create_vectorstore
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, Docx2txtLoader, UnstructuredHTMLLoader, TextLoader, UnstructuredPDFLoader
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import NeMoEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from llm.llm import create_llm
import re
import pandas as pd
import sys
from datasets import Dataset
import matplotlib.pyplot as plt
from PIL import Image
import yaml
from langchain_community.vectorstores import FAISS

llm_2 = ChatNVIDIA(model="meta/llama3-70b-instruct")

if yaml.safe_load(open('config.yaml', 'r'))['NREM']:
    # Embeddings with NeMo Retriever Embeddings Microservice (NREM)
    print("Generating embeddings with NREM")
    nv_embedder = NVIDIAEmbeddings(base_url= yaml.safe_load(open('config.yaml', 'r'))['nrem_api_endpoint_url'],
                                   model=yaml.safe_load(open('config.yaml', 'r'))['nrem_model_name'],
                                   truncate = yaml.safe_load(open('config.yaml', 'r'))['nrem_truncate']
                                   )

else:
    # Embeddings with NVIDIA AI Foundation Endpoints
    nv_embedder = NVIDIAEmbeddings(model=yaml.safe_load(open('config.yaml', 'r'))['embedding_model'])

prompt_template = ChatPromptTemplate.from_messages(
    [("system", "You are a helpful and friendly intelligent AI assistant bot named ORAN Chatbot, deployed by the Artificial Intelligence Solutions Architecture and Engineering team at NVIDIA. The context given below will provide some documentation as well as ORAN specifications. Based on this context, answer the following question related to ORAN standards and specifications. If the question is not related to this, please refrain from answering."), ("user", "{input}")]
)
chain = prompt_template | llm_2 | StrOutputParser()

def remove_line_break(text):
    text = text.replace("\n", " ").strip()
    text = re.sub("\.\.+", "", text)
    text = re.sub(" +", " ", text)
    return text
def remove_two_points(text):
    text = text.replace("..","")
    return text
def remove_two_slashes(text):
    text = text.replace("__","")
    return text

def just_letters(text):
    return re.sub(r"[^a-z]+", "", text).strip()

def remove_non_english_letters(text):
    return re.sub(r"[^\x00-\x7F]+", "", text)

def langchain_length_function(text):
    return len(just_letters(remove_line_break(text)))

# @title
plt.rcParams.update({'font.size': 14})
def plot_metrics_with_values(metrics_dict, title='RAG Metrics',figsize=(10, 6)):
    """
    Plots a bar chart for metrics contained in a dictionary and annotates the values on the bars.
    Args:
    metrics_dict (dict): A dictionary with metric names as keys and values as metric scores.
    title (str): The title of the plot.
    """
    names = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    fig = plt.figure(figsize=figsize)
    bars = plt.barh(names, values, color='green')
    # Adding the values on top of the bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width - 0.2,  # x-position
                 bar.get_y() + bar.get_height() / 2,  # y-position
                 f'{width:.4f}',  # value
                 va='center')
    plt.xlabel('Score')
    plt.title(title)
    plt.xlim(0, 1)  # Setting the x-axis limit to be from 0 to 1
    plt.show()
    st.pyplot(fig)

st.set_page_config(
        page_title="Evaluation Metrics",
        page_icon="🔍",
        layout="wide",
)

if "config" not in st.session_state:
    st.session_state.config = ""

with st.sidebar:
    prev_cfg = st.session_state.config
    try:
        defaultidx = ["oran"].index(st.session_state.config["name"].lower())
    except:
        defaultidx = 0
    cfg_name = st.selectbox("Select a configuration/type of bot.", ("multimodal_oran", "oran"), index=defaultidx)
    st.session_state.config = get_config(os.path.join("bot_config", cfg_name+".config"))
    config = get_config(os.path.join("bot_config", cfg_name+".config"))
    if st.session_state.config != prev_cfg:
        st.rerun()

st.sidebar.success("Select an experience above.")
BASE_DIR = os.path.abspath("vectorstore")
CORE_DIR = os.path.join(BASE_DIR, config["core_docs_directory_name"])
vectorstore_folder = os.path.join(CORE_DIR, "vectorstore_nv")

st.subheader("Create synthetic data with the documents")
# Just load documents in a simple way (basic nemo-rag-chatbot) and create Q&A. Make chunks larger to include more context
if st.button("Run synthetic data generation"):
    with st.status("Processing and splitting documents.....", expanded=True) as status:
        raw_documents = []
        filelist = [f for f in os.listdir(CORE_DIR) if f.endswith(".pdf") or f.endswith(".txt") or f.endswith(".docx")]
        print(filelist)
        for file in [f for f in os.listdir(CORE_DIR) if f.endswith(".pdf") or f.endswith(".txt") or f.endswith(".docx")][:]:
            st.write("Loading document: ", file)
            file_path = os.path.join(CORE_DIR, file)
            if file.endswith("pdf"):
                # Process each PDF document and add them individually to the list
                pdf_docs = UnstructuredPDFLoader(file_path).load() #get_pdf_documents(file_path)
                raw_documents.extend(pdf_docs)
            elif file.endswith("docx") or file.endswith("docx"):
                docx_docs = Docx2txtLoader(file_path).load()
                raw_documents.extend(docx_docs)
            elif file.endswith("html") or file.endswith("html"):
                html_docs = UnstructuredHTMLLoader(file_path).load()
                raw_documents.extend(html_docs)
            elif file.endswith("txt") or file.endswith("txt"):
                txt_docs = TextLoader(file_path).load()
                raw_documents.extend(txt_docs)
            else:
                # Load unstructured files and add them individually
                loader = UnstructuredFileLoader(file_path)
                unstructured_docs = loader.load()
                raw_documents.extend(unstructured_docs)  # 'extend' is used here to add elements of the list individually

        text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size = 3000,
            chunk_overlap  = 100,
            length_function = langchain_length_function,
            is_separator_regex = False,
        )


        documents = text_splitter.split_documents(raw_documents)
        #remove short chuncks
        filtered_documents = [item for item in documents if len(item.page_content) >= 200]

        documents = filtered_documents
        pd.DataFrame([doc.metadata for doc in documents])['source'].unique()

        #remove two points
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_two_points(documents[i].page_content)
        #remove non english characters points
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_two_slashes(documents[i].page_content)
        #remove two points
        for i in range(0,len(documents)-1):
            documents[i].page_content=remove_two_points(documents[i].page_content)

        json_list = []
        sample_doc = '''Although BlueField-3 DPUs and SuperNICs share a range of features and capabilities, SuperNICs are uniquely optimized for accelerating Ethernet networks for AI. The following describes the foundation use-cases of BlueField-3 SuperNICs and DPUs:
        BlueField-3 SuperNICs are designed for network-intensive, massively parallel computing, providing up to 400Gb/s RoCE network connectivity between GPU servers on the East-West (E-W) network.
        BlueField-3 DPUs are designed for cloud infrastructure processing, offloading, accelerating, and isolating data center infrastructure services on the North-South (N-S) network.'''

        sample_response = '''{
            "question": "What is the main difference between BlueField-3 DPUs and SuperNICs?",
            "answer": "BlueField-3 DPUs are designed for cloud infrastructure processing, offloading, accelerating, and isolating data center infrastructure services on the North-South (N-S) network, whereas BlueField-3 SuperNICs are designed for network-intensive, massively parallel computing, providing up to 400Gb/s RoCE network connectivity between GPU servers on the East-West (E-W) network."
        }'''
        instruction_prompt = 'Given the previous paragraph, create one high quality question answer pair. The answer should be brief while covering technical depth, and must be restricted to the content provided. Your output should be a JSON formatted string with the question answer pair. Restrict the question to the context information provided.'
        system_prompt="You are an expert ORAN assistant at NVIDIA. You have a deep technical understanding of ORAN's specifications, standards and processes. Your job is to generate FAQs from documents for other colleagues to use in the field while informing about ORAN to customers."
        llm = create_llm("mistralai/mixtral-8x7b-instruct-v0.1", "NVIDIA")
        langchain_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{sample_doc}\n{instruction_prompt}"),
            ("ai", "{sample_response}"),
            ("human", "{input_doc}\n{instruction_prompt}")
            ]).partial(sample_response=sample_response, sample_doc=sample_doc, instruction_prompt=instruction_prompt)
        gen_chain = langchain_prompt | llm | StrOutputParser()
        print("Done processing")

        vectorstore = FAISS.load_local(vectorstore_folder, nv_embedder, allow_dangerous_deserialization=True)

        print("Done loading vectorstore")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3, "score_threshold": 0.5})
        # loop on a few sample chunks
        for chunk in documents[:10:]:
            # create the prompt
            answer = gen_chain.invoke({"input_doc": chunk.page_content})
            # generate the q/A pair
            #retrieve context and generate answers with a different llm
            st.write(json.loads(answer)['question'])
            docs = retriever.invoke(json.loads(answer)["question"])
            context_r = ""
            cons = []
            for doc in docs:
                context_r += doc.page_content + "\n\n"
                cons.append(doc.page_content)

            augmented_user_input = "Context: " + context_r + "\n\nQuestion: " + json.loads(answer)["question"] + "\n"
            full_response = ""
            for response in chain.stream({"input": augmented_user_input}):
                full_response += response

            # json object
            json_list.append(
                {'gt_context': chunk.page_content,
                    'document': chunk.metadata["source"],
                    'gt_answer': json.loads(answer)["answer"],
                    'question': json.loads(answer)["question"],
                    'answer': full_response,
                    'contexts': cons})

        # save the synthetic dataset
        json_list_string=json.dumps(json_list)
        with open('synthetic_data_openai.json', 'w') as f:
            f.write(json_list_string)
        status.update(label="Completed!",state="complete", expanded=False)

st.divider()

st.subheader("Run Evaluation Metrics")
# Just load documents in a simple way (basic nemo-rag-chatbot) and create Q&A. Make chunks larger to include more context
if st.button("Generate evaluation metrics"):
    from pathlib import Path
    status = st.status("Generating plots.....")
    time.sleep(5)
    df = pd.read_pickle('./evals/metrics_df.pkl')
    st.dataframe(df)
    with status:
        st.write("Loading evaluation dataset.....")
    # look at evals folder for generating eval plots offline
    image_path = './evals/gen.jpg'
    st.image(image_path)
    st.image(Image.open('./evals/ret.jpg'))
    st.image(Image.open('./evals/end.jpg'))
    with status:
        st.write("Showing evaluation metrics plots.....")
    status.update(label="Completed!",state="complete")

    # Evaluation metrics are computed offline in ./evals/03_eval_ragas.ipynb because:
    # 1. Real-time generation of these metrics involves more compute and a longer than intended waiting time
    # 2. Muliple APIs may break when calculating these metrics through the Streamlit UI

    # However, the following code block is provided if you wish to run this in real-time through the Streamlit UI

    # nvpl_llm = LangchainLLM(llm=llm)
    # with open('/home/jvamaraju/oran-chatbot/evals/eval_syn_QA_E5.json', 'r') as file:
    #     json_data_syn_e5 = json.load(file)
    # # print(json_data_syn_e5[10])
    # eval_questions = []
    # eval_answers = []
    # ground_truths = []
    # vdb_contexts = []
    # gt_contexts = []
    # counter = 0
    # for entry in json_data_syn_e5:
    #     entry["contexts"] = [str(r) for r in entry["contexts"]]
    #     entry["gt_answer"] = str(entry["gt_answer"])
    #     # entry["question"] = str(entry["question"])
    #     eval_questions.append(entry["question"])
    #     eval_answers.append(entry["answer"])
    #     vdb_contexts.append(entry["contexts"][0:3])
    #     ground_truths.append([entry["gt_answer"]])
    #     gt_contexts.append([entry["gt_context"]])

    # data_samples = {
    #     'question': eval_questions,
    #     'answer': eval_answers,
    #     'retrieved_contexts' : vdb_contexts,
    #     'ground_truths': ground_truths,
    #     'ground_truth_contexts':gt_contexts
    # }

    # dataset_syn_E5 = pd.DataFrame.from_dict(data_samples) # Dataset.from_dict(data_samples)
    # # Use continous evals library to generate retriever/generator metrics
    # evaluator = RetrievalEvaluator(
    #     dataset=dataset_syn_E5,
    #     metrics=[
    #         PrecisionRecallF1(),
    #         RankedRetrievalMetrics(),
    #     ],
    # )
    # # Run the eval!
    # r_results = evaluator.run(k=3,batch_size=50)
    # # Peaking at the results
    # print(evaluator.aggregated_results)
    # # Saving the results for future use
    # # evaluator.save("retrieval_evaluator_results.jsonl")

    # evaluator = GenerationEvaluator(
    #     dataset=dataset_syn_E5,
    #     metrics=[
    #         DeterministicAnswerCorrectness(),
    #         DeterministicFaithfulness(),
    #         # DebertaAnswerScores()
    #     ],
    # )
    # # Run the eval!
    # g_results = evaluator.run(batch_size=50)
    # # Peaking at the results
    # print(evaluator.aggregated_results)
    # df_g_results = pd.DataFrame(g_results)

    # # Calculate RAGAS metrics
    # with open('/home/jvamaraju/oran-chatbot/evals/eval_syn_QA_E5.json', 'r') as file:
    #     json_data_ATT_NV = json.load(file)

    # eval_questions = []
    # eval_answers = []
    # ground_truths = []
    # vdb_contexts = []
    # # gt_contexts = []
    # counter = 0
    # for entry in json_data_ATT_NV:
    #     print(entry)
    #     entry["contexts"] = [str(r) for r in entry["contexts"]]
    #     entry["gt_answer"] = str(entry["gt_answer"])
    #     entry["question"] = str(entry["question"])
    #     entry["answer"] = str(entry["answer"])
    #     eval_questions.append(entry["question"])
    #     eval_answers.append(entry["answer"])
    #     vdb_contexts.append(entry["contexts"][0:3])
    #     ground_truths.append([entry["gt_answer"]])
    #     # gt_contexts.append([entry["gt_context"]])

    # data_samples = {
    #     'question': eval_questions,
    #     'answer': eval_answers,
    #     'contexts' : vdb_contexts,
    #     'ground_truths': ground_truths,
    #     # 'ground_truth_contexts':gt_contexts
    # }

    # dataset_syn_e5 = Dataset.from_dict(data_samples)
    # context_relevancy = ContextRelevancy(llm=nvpl_llm)

    # faithfulness = Faithfulness(
    #     batch_size = 15
    # )
    # faithfulness.llm = nvpl_llm

    # answer_correctness = AnswerCorrectness(llm=nvpl_llm,
    #     weights=[0.4,0.6]
    # )
    # answer_correctness.llm = nvpl_llm

    # context_recall = ContextRecall(llm=nvpl_llm)
    # context_recall.llm = nvpl_llm

    # context_precision.llm = nvpl_llm


    # # answer_correctness.embeddings = nv_query_embedder
    # ## using NVIDIA embedding

    # answer_similarity = AnswerSimilarity(llm=nvpl_llm, embeddings=nv_embedder)
    # answer_relevancy = AnswerRelevancy(embeddings=nv_embedder,llm=nvpl_llm) #embeddings=nv_query_embedder,
    # # init_model to load models used
    # answer_relevancy.init_model()
    # answer_correctness.init_model()
    # results_1 = evaluate(dataset_syn_e5,metrics=[faithfulness,answer_similarity,context_precision,answer_relevancy,context_relevancy])
    # results_5 = evaluate(dataset_syn_e5,metrics=[context_recall])
    # df2 = results_5.to_pandas()
    # df = results_1.to_pandas()
    # df_merge = pd.concat([df, df_g_results], axis = 1)
    # results_1.update(evaluator.aggregated_results)
    # del results_1['rouge_faithfulness']
    # del results_1['token_overlap_faithfulness']
    # del results_1['bleu_faithfulness']
    # generator_metrics = ['faithfulness','answer_relevancy']
    # retriever_metrics = ['context_precision','context_relevancy']
    # endtoend = ['answer_similarity','token_overlap_f1','token_overlap_precision','token_overlap_recall','rouge_l_f1','rouge_l_precision','rouge_l_recall','bleu_score']
    # results_generator = {}
    # results_retriever = {}
    # results_endtoend = {}
    # for i in generator_metrics:
    #     results_generator[i] = results_1[i]
    # for i in retriever_metrics:
    #     results_retriever[i] = results_1[i]
    # for i in endtoend:
    #     results_endtoend[i] = results_1[i]
    # print(results_generator)
    # print(results_retriever)
    # print(results_endtoend)
    # plot_metrics_with_values(results_generator, "Base Generator Metrics",figsize=(6, 3))
    # plot_metrics_with_values(results_retriever, "Base Retriever Metrics",figsize=(6, 3))
    # plot_metrics_with_values(results_endtoend, "Base End-to-End Metrics",figsize=(10, 6))
