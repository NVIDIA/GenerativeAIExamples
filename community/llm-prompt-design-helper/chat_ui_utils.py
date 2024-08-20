# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import gradio as gr
from langchain_nvidia_ai_endpoints import ChatNVIDIA,NVIDIAEmbeddings,NVIDIARerank
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
import os
from api_request_backends.openai_client import API_CATALOG_KEY, OpenAIClient, NIM_INFER_URL
from vector_store.faiss_vector_store import FAISSVS
from api_request_backends.chatnv_client import ChatNVDIAClient
from typing import List
from pathlib import Path
import requests
from time import sleep
import wget
from bs4 import BeautifulSoup
import json
from langchain.docstore.document import Document
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

os.environ["NVIDIA_API_KEY"] = API_CATALOG_KEY

initial_prompt = "Hello! How can I assist you today?"

model_list=[]
embedding_model_list=[]
reranker_model_list=[]
retrieval_db=['None']
LOCAL_DB='local-vector-store'
REMOTE_DB='self-deployed-DB'

STATE_FILE = '/tmp/uploaded_files.txt'
FILES_DIR='/tmp/files/'
REF_OPENNING_STR="Reference files in local path or remote links:"

api_catalog_request = OpenAIClient("./config.yaml")
faiss_fun = FAISSVS(FILES_DIR)

"""
Util functions 
"""

# NOTE: this remote function maybe different depend on your database API. open to modify to fit customized backend. 
async def call_remote_url(json_string, search_url):
    json_object = json.loads(json_string)
    logging.info(f"search url:{search_url}: json:{json_object}")
    response = None
    async with httpx.AsyncClient() as client:
        response = await client.post(url=search_url,json=json_object)
    return response

def get_remote_retrieval_res(json_string,search_url) -> list:
    """
        Retrieval documentations from remote server using httpx call the API.

        Parameters: 
        json_string (string):   string including the reqeuest data. 
        search_url (string):    API endpoint url. 

        Return:
            Retrieved list with item type: Document
    """
    resp = asyncio.run(call_remote_url(json_string,search_url))

    documents_list =[]
    try:
        docs_list = resp.json().get("results",[])
        
        for docs in docs_list:
            documents =[]
            for doc in docs:
                if doc[0].get('type',None) == 'Document':
                    documents.append(
                        Document(
                                page_content=doc[0].get('page_content'), 
                                metadata={"source": doc[0].get('metadata')["source"],
                                          "sdk_category": doc[0].get('metadata')['sdk_category']}
                                )
                    )
            documents_list.append(documents)
        return documents_list[0]
    except Exception as e:
        logging.info(f"Get erro for search with remote {e}")
        return []
    
def get_reranked_results(docs_retrieved,query,reranker_model,number_reranker) -> list:
    """
        Ranking the documents based on query.

        Parameters:
        docs_retrieved (list):  list of Documents retrieved from DB
        query (string):         Query for this retrieval
        reranker_model (string):ranking model used 
        number_reranker (int):  number of docs returned after reranker.

        Return:
            Document list after ranking
    """
    ranker = NVIDIARerank(model=reranker_model,top_n=number_reranker)
    compressed_docs = ranker.compress_documents(docs_retrieved,query)

    return compressed_docs 

def get_docs(query,retrieval_db,number_search,reranker_model,number_reranker,search_url,json_input_temp) -> list:
    """
        Retrieval documents from local or remote db, then run reranker if selected.

        Parameters:
        query (string):          Query used to do similarity search
        retrieval_db (string):   Database selected one of [LOCAL_DB,REMOTE_DB]
        number_search (int):     Used if local db selected to define number of documents retrieval from DB
        reranker_model (string): reranker model used to rank the documents with query. None to skip ranking. 
        number_reranker (int):   Number of documents after reranking
        search_url (string):     Remote search URL endpoint
        json_input_temp (string):String template used to format json data to API.

        Return:
             Retrieved list with item type: Document
    """
    docs_retrieved = []
    query = f"\"{query}\""
    if retrieval_db == LOCAL_DB:
        docs_retrieved = faiss_fun.search(query=query,number_search=number_search)
    elif retrieval_db == REMOTE_DB:
        # double the curly braces around the JSON keys and values to avoid curly braces {} as placeholders for variables.
        json_input_temp = "{" + json_input_temp+"}"
        json_string  = json_input_temp.format(input=query)
        docs_retrieved = get_remote_retrieval_res(json_string,search_url)

    if reranker_model !='None':
        docs_retrieved = get_reranked_results(docs_retrieved,query,reranker_model,number_reranker)
    return docs_retrieved


def get_example_list_from_str(few_shot_examples_str) -> list:
    """
        Extract few-shot examples from string input from UI

        Parameters:
        few_shot_examples_str (string): String input from UI, with U:... \nA:.... 

        Return:
            List of examples with each with [{"role":"user","content":xxxx}, {"role":"assistant","content":xxxx},...]
    """
    lines = few_shot_examples_str.strip().split('\n')
    few_shot_examples_list =[]
    if len(lines) % 2 != 0: lines.pop()
    for i in range(0, len(lines), 2):
        user_line = lines[i].split(":",1)[1].lstrip() if "u:" in lines[i].lower() else ""
        assistant_line = lines[i+1].split(":",1)[1].lstrip() if "a:" in lines[i+1].lower() else ""
        if user_line =="" or assistant_line == "":
            continue
        few_shot_examples_list.append({"role":"user","content":user_line})
        few_shot_examples_list.append({"role":"assistant","content":assistant_line})
    return few_shot_examples_list

"""
Functions to interact with backend services
"""
def ask_question(message, chat_history) -> list:
    """
        Generate chat history based on chatbot component
    """
    if chat_history is None:
        return "", [[None, initial_prompt]]
    if chat_history[-1][0] == initial_prompt:
        chat_history[-1][1] = message
        return "", chat_history

    # return "", chat_history + [[message, None]]
    return "", [[message, None]]


def stream_response(chat_history,system_prompt,api_model,temperature,top_p,max_tokens,
                    few_shot_examples,base_url,reranker_model,number_search,number_reranker,
                    retrieval_db,search_url,json_input_temp):
    """
        Stream respons to user's query. inputs are from Gradio components
    """
    logging.info("In stream_response")
    to_retrieval = False
    if retrieval_db !='None':
        to_retrieval = True

    if len(chat_history)==1 and chat_history[0][0] =='':
       chat_history[-1][1] = "Hi, I'm here and happy to help, what can I do for you? You can type in the textbox."  
       logging.info(chat_history)
       yield chat_history
       return
    
    few_shot_examples_list =get_example_list_from_str(few_shot_examples)
    
    context =''
    reference_str = ''
    if to_retrieval:
        query = chat_history[-1][0]
        docs_retrieved = get_docs(query,retrieval_db,number_search,reranker_model,number_reranker,search_url,json_input_temp)
        if docs_retrieved:
            context = "\n".join([ document.page_content for document in docs_retrieved])
            reference_list =[document.metadata.get("source") for document in docs_retrieved]
            reference_str = f"\n\n{REF_OPENNING_STR}\n\n"+ "\n".join(list(set(reference_list)))

    completion_token_generator = api_catalog_request.generate_response(api_model,chat_history,system_prompt,initial_prompt,temperature,top_p,max_tokens,few_shot_examples_list,base_url,context)
     
    chat_history[-1][1] = ""
    for next_token in completion_token_generator:
        chat_history[-1][1] += next_token
        yield chat_history
    else:
        pass

    if to_retrieval:
        chat_history[-1][1] += reference_str
        yield chat_history

"""
    Functions to update Gradio component
"""
def get_reranker_models():
    """
        Update reranker models when loading page
        Get available reranker models via NVIDIARerank
    """
    global reranker_model_list
    reranker_model_list=[]
    if API_CATALOG_KEY=="":
        reranker_model_list=["nv-rerank-qa-mistral-4b:1"]
        reranker_model_list.append('None')
        return gr.Dropdown(choices=reranker_model_list, value="None", label="Reranker model, None to skip reranker")
    else:
        available_models = NVIDIARerank.get_available_models()
        # logging.info(embedding_model_list)
        for model in available_models:
            if model.model_type=='ranking':
                reranker_model_list.append(model.id)
        reranker_model_list.append("None")
        return gr.Dropdown(choices=reranker_model_list, value="None", label="Reranker model, None to skip reranker")  
    
def get_embedding_models():
    """
        Update embedding models when loading page
        Get available embedding models via NVIDIAEmbeddings
    """
    global embedding_model_list
    embedding_model_list=[]
    if API_CATALOG_KEY=="":
        embedding_model_list=["nvidia/nv-embed-v1"]
        return gr.Dropdown(choices=embedding_model_list, value="nvidia/nv-embed-v1", label="Embedding model",)
    else:
        available_models = NVIDIAEmbeddings.get_available_models()
        # logging.info(embedding_model_list)
        for model in available_models:
            if model.model_type=='embedding':
                embedding_model_list.append(model.id)
        return gr.Dropdown(choices=embedding_model_list, value="nvidia/nv-embed-v1", label="Embedding model")  

def get_chatnvidia_models():
    """
        Update LLM models list when loading page
        Get available LLM models via ChatNVIDIA
    """
    global model_list
    failure_model_on_system_prompt=['aisingapore/sea-lion-7b-instruct','snowflake/arctic']
    if NIM_INFER_URL!="https://integrate.api.nvidia.com/v1": # This is self deployed NIM endpoint
        model_list = []
        url = NIM_INFER_URL.strip('/')+'/models'
        headers = {
            "Authorization": f"Bearer {API_CATALOG_KEY}",
            "Accept": "application/json",
        }
        resp = requests.get(url,headers=headers)
        if resp.status_code ==200:
            available_models = resp.json().get('data')
            for model in available_models:
                model_list.append(model.get('id'))
            for model in failure_model_on_system_prompt:
                if model in model_list:
                    model_list.remove(model)
            model_list.sort()
        return gr.Dropdown(choices=model_list, value=model_list[0], label="API Catalog Model",scale = 5)  
    else:
        try:
            available_models = ChatNVIDIA.get_available_models()
            model_list = []
            for model in available_models:
                if model.model_type=='chat':
                    model_list.append(model.id)
            for model in failure_model_on_system_prompt:
                if model in model_list:
                    model_list.remove(model)
            model_list.sort()
            return gr.Dropdown(choices=model_list, value="meta/llama3-70b-instruct", label="API Catalog Model",scale = 5)  
        except Exception as e:
            model_list=[]
            logging.error(f"ERROR: Can not get available model list with {e}")
            return gr.Dropdown(choices=model_list, value=model_list[0], label="API Catalog Model",scale = 5)  
        
def get_api_model_parameters(api_model,few_shot_examples):
    """
        Update few shot examples based on config.yaml for specific api model selected.
    """
    model_config = api_catalog_request.get_model_settings(api_model)
    system_prompt = model_config.get('system_prompt','')
    temperature = float(model_config.get('temperature',0.2))
    top_p = float(model_config.get('top_p',0.7))
    max_tokens = int(model_config.get('max_tokens',1024))
    examples = model_config.get('few_shot_examples',[])
    few_shot_examples = few_shot_examples
    if examples:
        few_shot_examples=""
        for example in examples:
            user_str = "U: "+ example["content"] +"\n" if example["role"]=="user" else ""
            assistant_str = "A: "+ example["content"] +"\n" if example["role"]=="assistant" else ""
            if user_str or assistant_str:
                few_shot_examples = few_shot_examples + user_str + assistant_str
        few_shot_examples ="\n".join(list(filter(None,few_shot_examples.splitlines())))
    else:
        few_shot_examples =""
    # logging.info(few_shot_examples)
    return [system_prompt,temperature,top_p,max_tokens,few_shot_examples]

def show_loader():
    """
        Show working loader
    """
    return gr.HTML("""<div id="loader"></div>""",visible=True)

def update_yaml(api_model,system_prompt,temperature,top_p,max_tokens,few_show_examples):
    """
        Update config.yaml file based on UI setttings. 
    """
    few_show_examples_list = get_example_list_from_str(few_show_examples)
    model_parameters = {
        "system_prompt": system_prompt,
        "temperature":temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "few_shot_examples": few_show_examples_list
    }
    api_catalog_request.update_yaml(api_model,model_parameters)
    return 

def update_insert_button(text):
    """
        Update interactive mode when there is model input to manually insert
    """
    if text!='' and NIM_INFER_URL=="https://integrate.api.nvidia.com/v1":
        return gr.Button(value="Insert the model into list",interactive=True,size="sm")
    else:
        return gr.Button(value="Insert the model into list",interactive=False,size="sm")

def update_reset_button(text):
    """
        Update interactive mode of reset system prompt button when there is input of customized system prompt
    """
    if text !="":
        return gr.Button(value="Reset Defined System Prompt", variant='primary',interactive = True,size="sm")
    else:
        return gr.Button(value="Reset Defined System Prompt", variant='primary',interactive = False,size="sm")  
    
def update_reset_fewshot_button(text):
    """
        Update interactive mode of reset few show examples button when there is input of customized system prompt
    """
    if text !="":
        return gr.Button(value="Reset Defined Few-Shot Examples", variant='primary',interactive = True,size="sm")
    else:
        return gr.Button(value="Reset Defined Few-Shot Examples", variant='primary',interactive = False,size="sm")  
    
def insert_model(model_input):
    """
        Update the model list if insert model button click
    """
    global model_list
    model_list.append(model_input)
    return [gr.Dropdown(choices=model_list, value=model_input, label="API Catalog Model",scale = 5),
            gr.Button(value="Insert the model into list",interactive=False,size="sm")]  


def upload_file(files: List[Path]) -> List[str]:
    """
        Download the uploaded files into temporary FILES_DIR folder
    """
    try:
        file_paths = [file.name for file in files]
        # client.upload_documents(file_paths = file_paths)
        if not os.path.exists(FILES_DIR):
            os.makedirs(FILES_DIR)
        # Save the uploaded file names to the state file
        with open(STATE_FILE, 'a') as file:
            for file_path in file_paths:
                file_path = os.path.basename(file_path)
                file.write(file_path + '\n')
                
        for file in files:
            file_path = os.path.join(FILES_DIR, os.path.basename(file.name))
            fileOjb = open(file,'rb')
            content = fileOjb.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            fileOjb.close()

        os.chdir(FILES_DIR)
        file_paths = os.listdir(FILES_DIR)
        return [gr.File(value=file_paths,visible=True),
                gr.HTML("""<div id="loader"></div>""",visible=False)]
    except Exception as e:
        raise gr.Error(f"{e}")

def download_from_source(htmls,pdfs):
    """
        Download the html or pdf files from the input list to FILES_DIR folder
    """
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)

    for pdf_url in pdfs:
        if requests.get(pdf_url).status_code == 200:
            filename = pdf_url.split('/')[-1]
            filepath = os.path.join(FILES_DIR, filename)
            if os.path.exists(filepath):  
                os.remove(filepath)
            file_path = wget.download(pdf_url,filepath,bar=None)
            logging.info(f"Downloaded {pdf_url}")
    for html_url in htmls:
        try:
            response = requests.get(html_url)
        except Exception as e:
            logging.info(f"Request to {html_url} failed")
            continue
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove unwanted elements
                for tag in soup.find_all(["nav", "footer"]):
                        tag.decompose()

                # Remove all <div> elements with role="navigation"
                for nav in soup.find_all("div", role="navigation"):
                        nav.decompose()

                for script in soup(["script", "style"]):
                    script.extract()

                filename = f"{html_url.replace('/', '_')}"
                filename = f"{filename.replace(':', '_')}"
                filepath = os.path.join(FILES_DIR, filename)
                if os.path.exists(filepath):  
                    os.remove(filepath)
                    logging.info(f'-> Delete existing {filepath}')
                with open(filepath, 'w', encoding='utf-8') as output_file:
                    output_file.write(str(soup))
                    sleep(0.1)
                logging.info(f"Downloaded {html_url}")

def embedding_files(url_sources,embedding_model,chunk_size,overlap_size):
    """
        Embedding the uploaded files and downloadable files. 
        1: uploaded files are already stored in FILES_DIR
        2. download the htmls and/or pdfs to FILES_DIR
        4. parse, chunking the files under FILES_DIR 
        5. generate embeddings for the chunks based on chunk strategies defined via UI. 
        6. Insert local_db to retrieval_db as it's available for retrieval.
        7. update relate Gradio components
    """
    url_sources_list = url_sources.split(",")
    html_sources=[]
    pdf_sources=[]
    for source in url_sources_list:
        if not source.startswith(('http://', 'https://')):
            continue
        if source.endswith(".pdf"):
            pdf_sources.append(source)
        else:
            html_sources.append(source)
    download_from_source(html_sources,pdf_sources)
    file_paths = os.listdir(FILES_DIR)
    embedding_model_used = faiss_fun.get_embedding_model_name()
    if embedding_model_used !="None" and embedding_model_used != embedding_model:
        gr.Warning(f"embedding model changed, remove existing vector store and create new.")
    faiss_fun.generate_index(embedding_model,chunk_size,overlap_size)
    os.chdir(FILES_DIR)
    # logging.info(file_paths)
    global retrieval_db
    if LOCAL_DB not in retrieval_db:
        retrieval_db.append(LOCAL_DB)

    return [
        gr.File(value=file_paths,visible=True),
        gr.HTML("""<div id="loader"></div>""",visible=False),
        gr.Textbox(
                        placeholder="Embedding model used to create vector store",
                        label="Embedding model used to create vector store",
                        value = embedding_model,
                        lines=1,
                        interactive=False
                    ),
        gr.Number(label="Number of chunks of searching",value=10,interactive=True),
        gr.Dropdown(
                        choices=retrieval_db, 
                        value="None", 
                        label="Retrieval with below db, None to skip retrieval",
                        interactive=True
                    )
    ]

def get_vs_embedding_model():
    """
        The embedding model avaiale for retrieval for local db 
        can not be updated shall be the same as local db creation
    """
    return faiss_fun.get_embedding_model_name()

def update_rerank_size(reranker_model):
    """
        Update reranker size based on reranker selected.
    """
    if reranker_model == "None":
        return gr.Number(label="Number of chunks after reranker",interactive=False)
    else:
        return gr.Number(label="Number of chunks after reranker",value=3,interactive=True)
    
def update_search_size(embedding_model):
    """
        Update search size based on embedding selected.
    """
    if embedding_model == "None":
        return gr.Number(label="Number of chunks of searching",interactive=False)
    else:
        return gr.Number(label="Number of chunks of searching",value=10,interactive=True)

def update_retrieval_db(source_url):
    """
        Update retrieval db when remote search url is defined 
    """
    global retrieval_db
    if source_url!="" and REMOTE_DB not in retrieval_db:
        retrieval_db.append(REMOTE_DB)

    return gr.Dropdown(
                        choices=retrieval_db, 
                        value="None", 
                        label="Retrieval with below db, None to skip retrieval",
                        interactive=True
                    )

def update_reranker_settings(retrieval_tool):
    """
        Enable to select reranker model if not none db selected
    """
    global reranker_model_list
    if retrieval_tool !='None':
        return gr.Dropdown(choices=reranker_model_list, value="None", label="Reranker model, None to skip reranker",interactive=True)
    else:
        return gr.Dropdown(choices=reranker_model_list, value="None", label="Reranker model, None to skip reranker",interactive=False)

def clear_files():
    logging.info("in clear: remove all files")

    files = os.listdir(FILES_DIR)
    for file in files:
        file_path = os.path.join(FILES_DIR, file)
        # Check if it's a file and remove it
        if os.path.isfile(file_path):
            os.remove(file_path)
    faiss_fun.remove_index()
    global retrieval_db
    if LOCAL_DB in retrieval_db:
        retrieval_db.remove(LOCAL_DB)
    logging.info("All files deleted successfully.")
    return [
            load_local_files(),
            gr.Dropdown(
                        choices=retrieval_db, 
                        value="None", 
                        label="Retrieval with below db, None to skip retrieval",
                        interactive=True
                    ),
            gr.Textbox(
                        placeholder="Embedding model used to create vector store",
                        label="Embedding model used to create vector store",
                        value = "None",
                        lines=1,
                        interactive=False
                        ),
            gr.Number(label="Number of chunks of searching",value=0,interactive=False)
        ]
    # logging.info(evt.value)

def delete_file_from_local(file_data: gr.DeletedFileData):
    """
        Delete the files from local folder
    """
    logging.info("in delete")

    file_name = os.path.basename(file_data.file.path)
    file_path = os.path.join(FILES_DIR, file_name)
    logging.info(f"delete path is {file_path}")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logging.info(f"remove {file_path} done")
        except OSError as e:
            logging.info(f"remove {file_path} error")
    faiss_fun.remove_source_ids(file_name=file_name)
    return load_local_files()

def load_local_files():
    if not os.path.exists(FILES_DIR):
        return gr.File(value=[],visible=False,interactive=True)
    
    file_paths = os.listdir(FILES_DIR)
    os.chdir(FILES_DIR)
    if file_paths:
        return gr.File(value=file_paths,visible=True,interactive=True)
    else:
        return gr.File(value=[],visible=False,interactive=True)

def load_default_retrieval_db():
    """
    Check the available retrieval sources
    """
    global retrieval_db
    retrieval_db =["None"]
    if faiss_fun.get_reteriever_engine():
        retrieval_db.append(LOCAL_DB)
    return gr.Dropdown(
                        choices=retrieval_db, 
                        value="None", 
                        label="Retrieval with below db, None to skip retrieval",
                        interactive=True
                    )

