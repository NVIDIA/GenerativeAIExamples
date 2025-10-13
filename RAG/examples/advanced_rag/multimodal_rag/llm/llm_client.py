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

import logging

logger = logging.getLogger(__name__)

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from RAG.examples.advanced_rag.multimodal_rag.llm.llm import create_llm
from RAG.src.chain_server.utils import get_prompts


class LLMClient:
    def __init__(
        self,
        model_name="mixtral_8x7b",
        model_type="NVIDIA",
        is_response_generator=False,
        cb_handler=BaseCallbackHandler,
        **kwargs,
    ):
        self.llm = create_llm(model_name, model_type, is_response_generator, **kwargs)
        self.cb_handler = cb_handler

    def chat_with_prompt(self, system_prompt, prompt):
        langchain_prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{input}")])
        chain = langchain_prompt | self.llm | StrOutputParser()
        logger.info(f"Prompt used for response generation: {langchain_prompt.format(input=prompt)}")
        response = chain.stream({"input": prompt}, config={"callbacks": [self.cb_handler]})
        return response

    def multimodal_invoke(self, b64_string, steer=False, creativity=0, quality=9, complexity=0, verbosity=8):
        message = HumanMessage(
            content=[
                {"type": "text", "text": get_prompts().get("describe_image_prompt", "")},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_string}"},},
            ]
        )
        if steer:
            return self.llm.invoke(
                [message],
                labels={
                    "creativity": creativity,
                    "quality": quality,
                    "complexity": complexity,
                    "verbosity": verbosity,
                },
                callbacks=[self.cb_handler],
            )
        else:
            return self.llm.invoke([message])
