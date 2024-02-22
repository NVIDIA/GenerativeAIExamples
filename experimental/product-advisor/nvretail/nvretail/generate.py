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
from enum import Enum
import json
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import logging
from openai import OpenAI
from openai_function_calling.tool_helpers import ToolHelpers
from pydantic import BaseModel
from typing import Optional

from .cart import (
    Cart,
    view_cart_function,
    add_to_cart_function,
    remove_from_cart_function,
    modify_item_in_cart_function,
)
from .catalog import Catalog, Products, search_function


class Role(str, Enum):
    """Role"""

    ai = "ai"
    assistant = "assistant"
    function = "function"
    human = "human"
    system = "system"
    user = "user"


class Message(BaseModel):
    """Message"""

    role: Role = Role.user
    content: str


Messages = list[Message]


class FunctionMetadata(BaseModel):
    """FunctionMetadata"""

    fn_name: Optional[str]
    fn_args: Optional[dict]


class FunctionResult(BaseModel):
    """FunctionResult"""

    fn_result: str


class ProductAdvisor:
    """Product Advisor"""

    def __init__(self, client: OpenAI, cart: Cart, catalog: Catalog) -> None:
        self.client: OpenAI = client
        self.llm = ChatNVIDIA(model="mixtral_8x7b")
        self.cart: Cart = cart
        self.catalog: Catalog = catalog
        self.tools = [
            view_cart_function,
            add_to_cart_function,
            remove_from_cart_function,
            modify_item_in_cart_function,
            search_function,
        ]

    def execute_tool(
        self, fn_metadata: FunctionMetadata
    ) -> tuple[FunctionResult, Products]:
        """Execute tool"""
        products: Products = []

        if fn_metadata.fn_name == "view_cart":
            fn_result = self.cart.view_cart()
        elif fn_metadata.fn_name == "add_to_cart":
            fn_result = self.cart.add_to_cart(**fn_metadata.fn_args)
        elif fn_metadata.fn_name == "remove_from_cart":
            fn_result = self.cart.remove_from_cart(**fn_metadata.fn_args)
        elif fn_metadata.fn_name == "modify_item_in_cart":
            fn_result = self.cart.modify_item_in_cart(**fn_metadata.fn_args)
        elif fn_metadata.fn_name == "search":
            products = self.catalog.search(**fn_metadata.fn_args)
            fn_result = self.catalog.products_to_context(products)
        fn_result = FunctionResult(fn_result=fn_result)

        return fn_result, products

    def parse_messages(self, messages: Messages) -> list[tuple[str, str]]:
        """Parses messages"""
        roles = set(["ai", "assistant", "human", "system", "user"])
        messages = [(msg.role, msg.content) for msg in messages if msg.role in roles]
        return messages

    def chat(self, messages: Messages) -> tuple[Messages, FunctionMetadata, Products]:
        """Chat"""
        user_input: str = messages[-1].content  # extract user input
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            tools=ToolHelpers.from_functions(self.tools),
            tool_choice="auto",
            temperature=0.0,
        )
        use_tool = (
            completion.choices[0].finish_reason == "tool_calls"
            or completion.choices[0].message.tool_calls
        )

        products: Products = []
        function_metadata = FunctionMetadata(fn_name=None, fn_args=None)
        messages_parsed = messages[:-1]  # pops off last message which should be user
        inputs = {"input": user_input}
        if use_tool:
            # Use a tool and use the output of the tool to inform our response
            logging.info("Tool was called!")
            function_metadata = FunctionMetadata(
                fn_name=completion.choices[0].message.tool_calls[0].function.name,
                fn_args=json.loads(
                    completion.choices[0].message.tool_calls[0].function.arguments
                ),
            )
            fn_result, products = self.execute_tool(function_metadata)

            # Depending on which tool was called, we will construct an LLM chain to respond appropriately.
            system_message = Message(
                role="system",
                content="You are an AI chatbot that helps customers. Respond only using the following context:\n{context}",
            )
            if len(messages_parsed) == 0:
                messages_parsed.insert(0, system_message)
            else:
                messages_parsed[0] = system_message
            inputs["context"] = fn_result.fn_result
        else:
            # If no tool was used, we respond normally.
            logging.info("Responding normally!")

        # convert
        messages_parsed = self.parse_messages(messages_parsed)
        messages_parsed.append(("user", "{input}"))
        prompt = ChatPromptTemplate.from_messages(messages_parsed)
        chain = prompt | self.llm | StrOutputParser()
        response: str = chain.invoke(inputs)
        messages.append(Message(role="assistant", content=response))

        return messages, function_metadata, products
