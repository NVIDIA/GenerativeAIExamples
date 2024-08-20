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

import requests
import json
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline
import yaml
import os

NVIDIA_API_KEY = yaml.safe_load(open("config.yaml"))['nvidia_api_key']
os.environ['NVIDIA_API_KEY'] = NVIDIA_API_KEY

class NvidiaLLM:
    def __init__(self, model_name):
        self.llm = ChatNVIDIA(model=model_name,  max_tokens = 4000)

class NimLLM:
    def __init__(self, model_name):
        config_yaml_path = 'config.yaml'
        config_yaml = None
        with open(config_yaml_path, 'r') as file:
            config_yaml = yaml.safe_load(file)
        self.llm = ChatNVIDIA(base_url = config_yaml['nim_base_url'],
                        model=config_yaml['nim_model_name'],
                        temperature = config_yaml['temperature'],
                        top_p = config_yaml['top_p'],
                        max_tokens = config_yaml['max_tokens']
                        )

class LocalLLM:
    def __init__(self, model_path):
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            torch_dtype=torch.float16,
            trust_remote_code=True,
            device_map="auto"
            )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=1024,
            temperature=0.6,
            top_p=0.3,
            repetition_penalty=1.0
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)


def create_llm(model_name, model_type="NVIDIA"):
    # Use LLM to generate answer
    if model_type == "NVIDIA":
        model = NvidiaLLM(model_name)
    elif model_type == "NIM":
        model = NimLLM(model_name)
    elif model_type == "LOCAL":
        model = LocalLLM(model_name)
    else:
        print("Error! Need model_name and model_type!")
        exit()

    return model.llm


if __name__ == "__main__":
    llm = create_llm("mistral7b", "NIM")

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain import LLMChain

    system_prompt = "Hello,"
    prompt = "who are you"
    langchain_prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{input}")])
    chain = langchain_prompt | llm | StrOutputParser()

    response = chain.stream({"input": prompt})

    for chunk in response:
        print(chunk)

