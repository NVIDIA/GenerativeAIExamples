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

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA

llm = ChatNVIDIA(model="ai-mixtral-8x7b-instruct")

def fact_check(evidence, query, response):

    system_message = f"""Your task is to conduct a thorough fact-check of a response provided by a large language model. You will be given the context documents as [[CONTEXT]], the original question posed by the user as [[QUESTION]], and the model's response as [[RESPONSE]]. Your primary objective is to meticulously verify each part of the model's response to ensure it aligns accurately and directly with the information presented in the context documents. Please refrain from using any external information or relying on prior knowledge. Focus on determining whether the response is entirely factual based on the provided context and whether it fully addresses the user's question. This process is crucial for maintaining the accuracy and reliability of the information given by the language model. You can provide suggestions to the user for follow-up questions based on the documents, that will provide them more information about the topic they are interested in. If your fact check returns True, start your reply with '**:green[TRUE]**' in your response, and if it returns False, start your reply with '**:red[FALSE]**' in your response."""

    user_message = f"""[[CONTEXT]]\n\n{evidence}\n\n[[QUESTION]]\n\n{query}\n\n[[RESPONSE]]\n\n{response}"""

    langchain_prompt = ChatPromptTemplate.from_messages([("system", system_message), ("user", "{input}")])

    chain = langchain_prompt | llm | StrOutputParser()
    response = chain.stream({"input": user_message})
    return response
