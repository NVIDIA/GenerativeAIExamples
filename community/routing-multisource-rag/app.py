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
import time

import chainlit as cl
from dotenv import load_dotenv
from llama_index.core import Settings

from workflow import QueryFlow

load_dotenv()

workflow = QueryFlow(timeout=45, verbose=False)


@cl.on_chat_start
async def on_chat_start():

    cl.user_session.set("message_history", [])

    workflow = QueryFlow(timeout=90, verbose=False)

    cl.user_session.set("workflow", workflow)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Write a haiku about CPUs",
            message="Write a haiku about CPUs.",
            icon="/avatars/servers",
        ),
        cl.Starter(
            label="Write Docker Compose",
            message="Write a Docker Compose file for deploying a web app with a Redis cache and Postgres database",
            icon="/avatars/screen",
        ),
        cl.Starter(
            label="What NIMs are available?",
            message="Summarize the different large language models that have NVIDIA inference microservices (NIMs) available for them. List as many as you can.",
            icon="/avatars/container",
        ),
        cl.Starter(
            label="Summarize BioNemo use cases",
            message="Write a table summarizing how customers are using bionemo. Use one sentence per customer and include columns for customer, industry, and use case. Make the table between 5 to 10 rows and relatively narrow.",
            icon="/avatars/dna",
        ),
    ]


@cl.on_chat_end
def end():
    logging.info("Chat ended.")


@cl.on_message
async def main(user_message: cl.Message, count_tokens: bool = True):
    """
    Executes when a user sends a message. We send the message off to the LlamaIndex chat engine
    for a streaming answer. When the answer is done streaming, we go back over the response
    to identify the sources used, and then add a block of text about the sources.
    """

    msg_start_time = time.time()
    logging.info(f"Received message: <{user_message.content[0:50]}...> ")
    message_history = cl.user_session.get("message_history", [])

    # In case the chat workflow needs extra time to start up,
    # we block until it's ready.

    assistant_message = cl.Message(content="")

    token_count = 0
    with cl.Step(name="Mistral Large 2", type="tool"):

        response, source_nodes = await workflow.run(
            query=user_message.content,
            chat_messages=message_history,
        )

        async for chunk in response:
            token_count += 1
            chars = chunk.delta
            await assistant_message.stream_token(chars)

        assistant_message.content += (
            "\n<small style='font-size: 30%; opacity: 0.5'> </small> "
        )

        msg_time = time.time() - msg_start_time
        logging.info(f"Message generated in {msg_time:.1f} seconds.")

    message_history += [
        {"role": "user", "content": user_message.content},
        {"role": "assistant", "content": assistant_message.content},
    ]

    cl.user_session.set("message_history", message_history)

    await assistant_message.send()
