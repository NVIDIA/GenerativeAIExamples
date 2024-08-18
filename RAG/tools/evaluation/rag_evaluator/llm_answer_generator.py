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

import json
import logging
import mimetypes
import os
import time
import typing

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_document(file_path, url):
    """
    Upload a document to a URL.
    This function uploads a document from a local file path to a specified URL.
    """
    headers = {"accept": "application/json"}
    mime_type, _ = mimetypes.guess_type(file_path)
    files = {"file": (file_path, open(file_path, "rb"), mime_type)}
    response = requests.post(url, headers=headers, files=files)
    return response.text


def upload_pdf_files(folder_path, upload_url):
    """
    Upload PDF files from a folder to a URL.
    This function iterates through a folder, finds all PDF files, and uploads them to a specified URL.
    """
    i = 1
    for file in os.listdir(folder_path):
        _, ext = os.path.splitext(file)
        if ext.lower() == ".pdf":
            file_path = os.path.join(folder_path, file)
            logger.info(f"{i}/{len(os.listdir(folder_path))}")
            upload_document(file_path, upload_url)
        else:
            logger.info(f"Please ingest PDF file. {file} not uploaded")
        i += 1


def generate_answers(
    base_url,
    dataset_folder_path,
    qa_generation_file_path,
    eval_file_path,
    generate_api_params={"use_knowledge_base": True, "temperature": 0.2, "top_p": 0.7, "max_tokens": 256},
    document_search_api_params={"num_docs": 1},
):
    """
    Function to upload PDF files to evaluation dataset and generate answer using generate API endpoint
    and search for relevant documents using documentSearch API endpoint, saving to 'eval.json' file
    """
    upload_pdf_files(
        dataset_folder_path, f"http://{base_url}/documents",
    )
    with open(qa_generation_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = []
    url_generate = f"http://{base_url}/generate"
    url_doc_search = f"http://{base_url}/search"
    count = 0
    for entry in data:
        count += 1
        logger.info(f"{count}/{len(data)}")
        entry_generate = {
            "messages": [{"role": "user", "content": entry["question"]}],
            "use_knowledge_base": generate_api_params["use_knowledge_base"],
            "temperature": generate_api_params["temperature"],
            "top_p": generate_api_params["top_p"],
            "max_tokens": generate_api_params["max_tokens"],
            "stop": ["string"],
        }
        entry["generated_answer"] = ""

        try:
            with requests.post(url_generate, stream=True, json=entry_generate) as r:
                for chunk in r.iter_lines():
                    raw_resp = chunk.decode("UTF-8")
                    if not raw_resp:
                        continue
                    resp_dict = None
                    try:
                        logger.debug(raw_resp)
                        resp_dict = json.loads(raw_resp[6:])
                        resp_choices = resp_dict.get("choices", [])
                        if len(resp_choices):
                            resp_str = resp_choices[0].get("message", {}).get("content", "")
                            entry["generated_answer"] += resp_str
                    except Exception as e:
                        logger.info(f"Exception Occured: {e}")
        except Exception as e:
            logger.info(f"Exception Occured: {e}")
            entry["generated_answer"] = "Answer couldn't be generated."
        logger.info(entry["generated_answer"])
        entry_doc_search = {"query": entry["question"], "top_k": document_search_api_params["num_docs"]}
        response = requests.post(url_doc_search, json=entry_doc_search).json()
        context_list = typing.cast(typing.List[typing.Dict[str, typing.Union[str, float]]], response)
        contexts = [context.get("content") for context in context_list['chunks']]
        logger.info(contexts)
        try:
            entry["retrieved_context"] = [contexts[0]]
        except Exception as e:
            logger.info(f"Exception Occured: {e}")
            entry["retrieved_context"] = ""
        new_data.append(entry)
        logger.info(len(entry["retrieved_context"]))

    with open(eval_file_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f)
