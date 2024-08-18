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
import os
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_nvidia_ai_endpoints import ChatNVIDIA

LLM_PROMPT_TEMPLATE = (
    "<s>[INST] <<SYS>>"
    "{system_prompt}"
    "<</SYS>>"
    " "
    "[The Start of the Reference Context]"
    "{ctx_ref}"
    "[The End of Reference Context][/INST]"
)
SYS_PROMPT = """
    Given the context paragraph, create two very good question answer pairs.
    Your output should be strictly in a json format of individual question answer pairs with keys from ["question","answer"]. 
    Restrict the question to the context information provided.
    """
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_data(
    dataset_folder_path,
    qa_generation_file_path,
    text_splitter_params={"chunk_size": 3000, "chunk_overlap": 100},
    llm_params={"model": "ai-mixtral-8x7b-instruct", "temperature": 0.2, "max_tokens": 300,},
):
    """
    Generate synthetic data i.e. QnA pairs on the basis of textual context from Unstructured file.
    This function loads a dataset from a zip file, extracts text from a Unstructured file, splits
    the text into chunks, and uses a language model to generate question-answer pairs.
    """

    files = [f for f in os.listdir(dataset_folder_path) if os.path.isfile(os.path.join(dataset_folder_path, f))]
    nvidia_api_key = os.environ["NVIDIA_API_KEY"]
    llm_params["nvidia_api_key"] = nvidia_api_key
    llm = ChatNVIDIA(**llm_params)
    json_data = []
    i = 0
    for pdf_file in files:
        i += 1
        try:
            logger.info(f"{i}/{len(files)}")
            pdf_file = dataset_folder_path + '/' + pdf_file
            loader = UnstructuredFileLoader(pdf_file)
            data = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(**text_splitter_params)
            all_splits = text_splitter.split_documents(data)
            for split in all_splits:
                context = LLM_PROMPT_TEMPLATE.format(system_prompt=SYS_PROMPT, ctx_ref=split.page_content,)
                try:
                    answer = llm.invoke(context).content
                    question_pattern = r'"question":\s*"([^"]*)"'
                    answer_pattern = r'"answer":\s*"([^"]*)"'
                    question_match = re.findall(question_pattern, answer)
                    answer_match = re.findall(answer_pattern, answer)
                    if len(question_match) == len(answer_match):
                        for j, _ in enumerate(question_match):
                            my_data = {
                                'question': question_match[j],
                                'ground_truth_answer': answer_match[j],
                                'ground_truth_context': split.page_content,
                                'document': pdf_file,
                            }
                            json_data.append(my_data)

                except Exception as e:
                    logger.info(f"\n PDF: {pdf_file} \n \t Context: {context} \n Exception Occured: {e}")

        except Exception as e:
            logger.info(f"\n PDF: {pdf_file} \n Exception Occured: {e}")

    with open(qa_generation_file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f)
