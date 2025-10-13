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

import json

import requests
import torch
from langchain_community.llms import HuggingFacePipeline
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from RAG.src.chain_server.utils import get_config, get_llm


class NvidiaLLM:
    def __init__(self, model_name, is_response_generator: bool = False, **kwargs):

        # LLM is used for response generation as well as for generating description
        # of images, only use llm from configuration for response generator
        if is_response_generator:
            self.llm = get_llm(**kwargs)
        else:
            self.llm = ChatNVIDIA(
                model=model_name,
                temperature=kwargs.get('temperature', None),
                top_p=kwargs.get('top_p', None),
                max_tokens=kwargs.get('max_tokens', None),
            )


class LocalLLM:
    def __init__(self, model_path, **kwargs):
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=torch.float16, trust_remote_code=True, device_map="auto"
        )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=kwargs.get('max_tokens', 1024),
            temperature=kwargs.get('temperature', 0.6),
            top_p=kwargs.get('top_p', 0.3),
            repetition_penalty=1.0,
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)


def create_llm(model_name, model_type="NVIDIA", is_response_generator=False, **kwargs):
    # Use LLM to generate answer
    if model_type == "NVIDIA":
        model = NvidiaLLM(model_name, is_response_generator, **kwargs)
    elif model_type == "LOCAL":
        model = LocalLLM(model_name, **kwargs)
    else:
        print("Error! Need model_name and model_type!")
        exit()

    return model.llm


if __name__ == "__main__":
    llm = create_llm("gpt2", "LOCAL")

    from langchain import LLMChain
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    system_prompt = ""
    prompt = "who are you"
    langchain_prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{input}")])
    chain = langchain_prompt | llm | StrOutputParser()

    response = chain.stream({"input": prompt})

    for chunk in response:
        print(chunk)
