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


"""
LlamaIndex Workflows are event-driven workflows in which we define the event types and the steps that process them.
Some sharp edges around workflows:
- To let multiple events flow into a single event, you need to use the Context.collect_events method. This method takes in the
    number of expected events then will fire. Otherwise, it emits a None value which needs to be handled.
- Versions of LI close to ~0.10.58 are broken. Make sure you are on the latest version.
- Since many of the API calls are async methods, we define simple wrapper functions so we can apply async caching with Redis without much hassle.

The workflow(s) in this file implement conversational workflow with RAG.
"""

import asyncio
import logging
from time import time

import chainlit as cl
import httpx
from llama_index.core import Document, Settings
from llama_index.core.llms import ChatMessage
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.schema import Document, NodeWithScore
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from llama_index.llms.perplexity import Perplexity
from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import BaseModel, Field

import prompts
from config import WorkflowConfig

config = WorkflowConfig()


class RoutingChoice(BaseModel):
    use_search: bool = Field(
        default=True,
        description="Whether to use the search engine to answer the query",
    )


class CustomHTTPClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        kwargs["timeout"] = httpx.Timeout(20.0)
        super().__init__(*args, **kwargs)


httpx.AsyncClient = CustomHTTPClient

logger = logging.getLogger(__name__)

chat_llm = NVIDIA(config.chat_model_name, api_key=config.nvidia_api_key)
routing_llm = NVIDIA(config.routing_model_name, api_key=config.nvidia_api_key)
perplexity_llm = (
    Perplexity(config.perplexity_model_name, api_key=config.perplexity_api_key)
    if config.perplexity_api_key
    else None
)
embed_model = NVIDIAEmbedding(
    config.embedding_model_name, api_key=config.nvidia_api_key
)

routing_program = LLMTextCompletionProgram.from_defaults(
    output_cls=RoutingChoice,
    prompt_template_str=prompts.ROUTING_PROMPT,
    llm=routing_llm,
)

vector_store = vector_store = MilvusVectorStore(
    uri=config.milvus_path, dim=config.embedding_model_dim
)


class ShortcutEvent(Event):
    nodes: list[Document] = (
        []
    )  # should always be empty; this just short-circuits around the RAG


class RawQueryEvent(Event):
    raw_query: str


class TransformedQueryEvent(Event):
    transformed_query: str


class EmbeddedQuery(Event):
    embedding: list[float]


class MilvusQueryEvent(Event):
    nodes: list[Document]


class PerplexityQueryEvent(Event):
    nodes: list[Document]


class NodeCollectEvent(Event):
    nodes: list[Document]


class QueryFlow(Workflow):
    """
    LlamaIndex Workflow for chat with multiple data sources including Milvus and Perplexity
    """

    tokenizer = Settings.tokenizer

    @step()
    async def workflow_start(
        self, ctx: Context, ev: StartEvent
    ) -> ShortcutEvent | RawQueryEvent:
        start_time = time()

        ctx.data["chat_messages"] = ev.chat_messages
        ctx.data["raw_query"] = ev.query

        # Use the structured output model to determine whether to use search
        with cl.Step(name="query router", type="tool") as step:
            start_time = time()
            step.input = {"user_query": ev.query}
            routing_choice = await routing_program.acall(query=ev.query)
            step.output = {
                "use_search": routing_choice.use_search,
                "time_elapsed": round(time() - start_time, 3),
            }

        if routing_choice.use_search:
            return RawQueryEvent(raw_query=ev.query)
        else:
            return ShortcutEvent()

    @step()
    async def rewrite_query(
        self, ctx: Context, rq: RawQueryEvent
    ) -> TransformedQueryEvent:
        with cl.Step(name="query rewrite", type="tool") as step:
            start_time = time()
            step.input = {"raw_query": rq.raw_query}

            # Get previous user query
            history_str = ""
            for msg in ctx.data["chat_messages"][-2:-1]:
                history_str += f"{msg['role']}: {msg['content']}\n"

            prompt = prompts.QUERY_REWRITE_PROMPT.format(
                query=rq.raw_query, history_str=history_str
            )

            response = await chat_llm.acomplete(prompt)
            transformed_query = str(response)

            step.output = {
                "chat_context": history_str,
                "transformed_query": transformed_query,
                "time_elapsed": round(time() - start_time, 3),
            }

            ctx.data["transformed_query"] = transformed_query

        return TransformedQueryEvent(transformed_query=transformed_query)

    @step()
    async def embed_query(self, tq: TransformedQueryEvent) -> EmbeddedQuery:
        with cl.Step(name="vector embedding", type="tool") as step:
            start_time = time()
            step.input = tq.transformed_query
            embedding = await embed_model.aget_query_embedding(tq.transformed_query)
            step.output = {
                "embedding_preview": str(embedding[0:5]) + "..." + str(embedding[-5:]),
                "time_elapsed": round(time() - start_time, 3),
            }
            return EmbeddedQuery(embedding=embedding)

    @step()
    async def milvus_retrieve(
        self, ctx: Context, eq: EmbeddedQuery
    ) -> MilvusQueryEvent:
        start_time = time()

        with cl.Step(name="Milvus search", type="tool") as step:

            vector_query = VectorStoreQuery(
                query_embedding=eq.embedding, similarity_top_k=config.similarity_top_k
            )
            nodes = vector_store.query(vector_query).nodes
            step.output = {
                "retrieved_nodes": [n.text for n in nodes],
                "time_elapsed": round(time() - start_time, 3),
            }

        return MilvusQueryEvent(nodes=nodes)

    @step()
    async def pplx_retrieve(self, tq: TransformedQueryEvent) -> PerplexityQueryEvent:
        # This always returns a list with a single node
        with cl.Step(name="Perplexity search", type="tool") as step:
            start_time = time()

            if not perplexity_llm:
                logger.warning(
                    "No Perplexity API key found. Skipping Perplexity search."
                )
                return PerplexityQueryEvent(nodes=[])

            messages = [
                ChatMessage(role="system", content="Be precise and concise."),
                ChatMessage(role="user", content=tq.transformed_query),
            ]

            try:
                # Use asyncio.wait_for to implement the timeout
                response = await asyncio.wait_for(
                    perplexity_llm.achat(messages), timeout=config.perplexity_timeout
                )

                node = Document(
                    text=response.message.content,
                    metadata={config.source_field_name: "perplexity"},
                )
                nodes = [
                    NodeWithScore(
                        node=node,
                        score=0.5,  # Doesn't really matter, but we just set it here.
                    )
                ]
            except asyncio.TimeoutError:
                logger.error(
                    f"Timeout error retrieving from Perplexity after {config.perplexity_timeout} seconds"
                )
                nodes = []
            except Exception as e:
                logger.error(f"Error retrieving from Perplexity: {str(e)}")
                nodes = []

            logger.info(f"Retrieved {len(nodes)} nodes from Perplexity")
            step.input = {"query": tq.transformed_query}
            step.output = {
                "answer": nodes[0].text if nodes else "",
                "time_elapsed": round(time() - start_time, 3),
            }

            return PerplexityQueryEvent(nodes=nodes)

    @step()
    async def collect_nodes(
        self,
        ctx: Context,
        qe: MilvusQueryEvent | PerplexityQueryEvent,
    ) -> NodeCollectEvent:
        ready = ctx.collect_events(
            qe,
            expected=[
                MilvusQueryEvent,
                PerplexityQueryEvent,
            ],
        )

        if ready is None:
            logger.info("Still waiting for all input events!")

            return None

        else:
            nodes = []
            n_retrievers_used = 0

            for event in ready:
                nodes += event.nodes

                if event.nodes:
                    n_retrievers_used += 1

            logger.info(
                f"Collected {len(nodes)} nodes from {n_retrievers_used} retrievers"
            )

        return NodeCollectEvent(nodes=nodes)

    @step()
    async def synthesize_response(
        self, ctx: Context, ev: NodeCollectEvent | ShortcutEvent
    ) -> StopEvent:
        prompt_without_chunks = prompts.SYSTEM_PROMPT_TEMPLATE.format(
            context_str="", query=ctx.data["raw_query"], history_str=""
        )
        prompt_length_before_chunks = len(Settings.tokenizer(prompt_without_chunks))

        current_length = prompt_length_before_chunks + config.max_tokens_generated

        context_string = ""
        logger.info(
            "Forming final answer with up to {} chunks filling context window of size {}.".format(
                len(ev.nodes), config.context_window
            )
        )

        for node in ev.nodes:
            next_chunk = f"""Source text: {node.text}\n"""

            chunk_length = len(Settings.tokenizer(next_chunk))

            if current_length + chunk_length > config.context_window:
                logger.info(
                    "Chunk of length {} would exceed window size ({} (prompt + chunks so far) + {} (current chunk) + {} (tokens for generation) > {} (total context window)); dropping remaining chunks.".format(
                        chunk_length,
                        current_length,
                        chunk_length,
                        config.max_tokens_generated,
                        config.context_window,
                    )
                )
                break

            context_string += next_chunk
            current_length += chunk_length

        logger.info(
            "After forming RAG context, the length of the context string is {} tokens.".format(
                len(self.tokenizer(context_string))
            )
        )

        # We form the history string by taking the last N messages structured
        # like [{'role':'user', 'content':'Good morning, how are you?'}]
        # and form them into a single string. We assume that the most recent
        # message is the last in the list.
        history_string = ""

        if "chat_messages" in ctx.data:
            for msg in ctx.data["chat_messages"][-config.n_messages_in_history :]:
                history_string += f"{msg['role']}: {msg['content']}\n"

            tokens_in_msg_history = len(self.tokenizer(history_string))
            logger.info(
                "Length of message history is {} tokens across {} messages.".format(
                    tokens_in_msg_history, len(ctx.data["chat_messages"])
                )
            )

        final_prompt = prompts.SYSTEM_PROMPT_TEMPLATE.format(
            context_str=context_string,
            history_str=history_string,
            query=ctx.data["raw_query"],
        )
        final_length = len(self.tokenizer(final_prompt))

        logger.info(
            "Length of final prompt is {} tokens of which {} tokens is system prompt.".format(
                final_length, prompt_length_before_chunks
            )
        )

        with cl.Step(name="response synthesis", type="tool") as step:
            start_time = time()
            step.input = final_prompt

            response = await chat_llm.astream_complete(final_prompt)

            end_time = time()
            step.output = {
                "time_elapsed": round(end_time - start_time, 3),
            }

        return StopEvent(result=(response, ev.nodes))
