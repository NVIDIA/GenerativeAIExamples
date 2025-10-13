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

"""
This example showcases recursive task decomposition to perform RAG which requires multiple steps.
The agent is a langchain custom LLM agent, which uses 2 tools - search and math.
It uses Llama3 model for sub-answer formation, tool prediction and math operations.
Search tool is a RAG pipeline, whereas the math tool uses an LLM call to perform mathematical calculations.
"""

import base64
import json
import logging
import os
from typing import Any, Dict, Generator, List, Union

import jinja2
from langchain.agents.agent import AgentExecutor, AgentOutputParser, LLMSingleActionAgent
from langchain.chains.llm import LLMChain
from langchain.schema.agent import AgentAction, AgentFinish
from langchain.text_splitter import CharacterTextSplitter
from langchain.tools import Tool
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.messages.human import HumanMessage
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts.chat import BaseChatPromptTemplate, ChatPromptTemplate

from RAG.src.chain_server.base import BaseExample
from RAG.src.chain_server.tracing import langchain_instrumentation_class_wrapper
from RAG.src.chain_server.utils import (
    create_vectorstore_langchain,
    del_docs_vectorstore_langchain,
    get_config,
    get_doc_retriever,
    get_docs_vectorstore_langchain,
    get_embedding_model,
    get_llm,
    get_prompts,
    get_vectorstore,
    set_service_context,
)

logger = logging.getLogger(__name__)

vector_store_path = "vectorstore.pkl"
document_embedder = get_embedding_model()
settings = get_config()
prompts = get_prompts()

try:
    vectorstore = create_vectorstore_langchain(document_embedder=document_embedder)
except Exception as e:
    vectorstore = None
    logger.info(f"Unable to connect to vector store during initialization: {e}")

##### Helper methods and tools #####


class Ledger:  # Stores the state of the recursive decomposition
    def __init__(self):
        self.question_trace = []
        self.answer_trace = []
        self.trace = 0
        self.done = False


##### LLM and Prompt definitions #####
def fetch_context(ledger: Ledger) -> str:
    """
    Create the context for the prompt from the subquestions and answers
    """
    context = ""
    for i in range(len(ledger.question_trace)):
        context += "Sub-Question: " + ledger.question_trace[i]
        context += "\nSub-Answer: " + ledger.answer_trace[i] + "\n"

    return context


template = prompts.get("tool_selector_prompt", "")

math_tool_prompt = prompts.get("math_tool_prompt", "")


class CustomPromptTemplate(BaseChatPromptTemplate):
    template: str
    tools: List[Tool]
    ledger: Ledger

    def format_messages(self, **kwargs) -> str:
        kwargs["context"] = fetch_context(self.ledger).strip("\n")
        env = jinja2.Environment()
        prompt_template = env.from_string(template)
        prompt = prompt_template.render(**kwargs)
        logger.info(prompt)
        return [HumanMessage(content=prompt)]


##### LLM output parser #####


class CustomOutputParser(AgentOutputParser):
    class Config:
        arbitrary_types_allowed = True

    ledger: Ledger

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        """
        Make a decision about the tool to be called based on LLM output.
        """

        logger.info(f"LLM Response: {llm_output}")
        local_state = json.loads(llm_output)
        if len(local_state["Generated Sub Questions"]) == 0:
            local_state["Generated Sub Questions"].append("Nil")
        if (
            local_state["Generated Sub Questions"][0] == "Nil"
            or local_state["Tool_Request"] == "Nil"
            or self.ledger.trace > 3
            or local_state["Generated Sub Questions"][0] in self.ledger.question_trace
        ):
            return AgentFinish(return_values={"output": "success"}, log=llm_output,)

        if local_state["Tool_Request"] == "Search":
            self.ledger.trace += 1

        if local_state["Tool_Request"] in ["Search", "Math"]:
            return AgentAction(
                tool=local_state["Tool_Request"],
                tool_input={"sub_questions": local_state["Generated Sub Questions"]},
                log=llm_output,
            )
        raise ValueError(f"Invalid Tool name: {local_state['Tool_Request']}")


@langchain_instrumentation_class_wrapper
class QueryDecompositionChatbot(BaseExample):
    def ingest_docs(self, filepath: str, filename: str):
        """Ingest documents to the VectorDB."""
        if not filename.endswith((".txt", ".pdf", ".md")):
            raise ValueError(f"{filename} is not a valid Text, PDF or Markdown file")
        try:
            # Load raw documents from the directory
            _path = filepath
            raw_documents = UnstructuredFileLoader(_path).load()

            if raw_documents:
                text_splitter = CharacterTextSplitter(
                    chunk_size=settings.text_splitter.chunk_size, chunk_overlap=settings.text_splitter.chunk_overlap
                )
                documents = text_splitter.split_documents(raw_documents)
                vs = get_vectorstore(vectorstore, document_embedder)
                vs.add_documents(documents)
                logger.info("Vector store created and saved.")
            else:
                logger.warning("No documents available to process!")
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            raise ValueError("Failed to upload document. Please upload an unstructured text document.")

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""

        logger.info("Using llm to generate response directly without knowledge base.")
        # WAR: Disable chat history (UI consistency).
        chat_history = []
        system_message = [("system", prompts.get("chat_template", ""))]
        conversation_history = [(msg.role, msg.content) for msg in chat_history]
        user_input = [("user", "{input}")]

        # Checking if conversation_history is not None and not empty
        prompt_template = (
            ChatPromptTemplate.from_messages(system_message + conversation_history + user_input)
            if conversation_history
            else ChatPromptTemplate.from_messages(system_message + user_input)
        )
        llm = get_llm(**kwargs)
        chain = prompt_template | llm | StrOutputParser()
        augmented_user_input = "\n\nQuestion: " + query + "\n"
        logger.info(f"Prompt used for response generation: {prompt_template.format(input=augmented_user_input)}")
        return chain.stream({"input": augmented_user_input}, config={"callbacks": [self.cb_handler]})

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")
        set_service_context()
        try:
            final_context = self.run_agent(query, **kwargs)
            if not final_context:
                logger.warning("Retrieval failed to get any relevant context")
                return iter(
                    ["No response generated from LLM, make sure your query is relavent to the ingested document."]
                )

            logger.info(f"Final Answer from agent: {final_context}")
            # TODO Add chat_history
            final_prompt_template = ChatPromptTemplate.from_messages([("human", final_context)])
            llm = get_llm(**kwargs)
            chain = final_prompt_template | llm | StrOutputParser()
            logger.info(f"Prompt used for final response generation: {final_prompt_template}")
            return chain.stream({}, config={"callbacks": [self.cb_handler]})
        except ValueError as e:
            logger.warning(f"Failed to get response because {e}")
            return iter(["I can't find an answer for that."])

    def create_agent(self, **kwargs) -> AgentExecutor:
        """
        Creates the tools, chain, output parser and agent used to fetch the full context.
        """

        self.ledger = Ledger()
        self.kwargs = kwargs

        tools = [
            Tool(
                name="Search",
                func=self.search,
                description="The Search Tool is a powerful querying system that quickly finds and retrieves relevant answers from a given context, providing accurate and precise information to meet your search needs.",
            ),
            Tool(
                name="Math",
                func=self.math,
                description="The Math Tool is a versatile calculator that performs essential mathematical operations, including multiplication, addition, subtraction, division, and greater than or less than comparisons, providing accurate results with ease.",
            ),
        ]
        tool_names = [tool.name for tool in tools]

        prompt = CustomPromptTemplate(template=template, tools=tools, input_variables=["question"], ledger=self.ledger)
        output_parser = CustomOutputParser(ledger=self.ledger)
        llm = get_llm(**kwargs)
        llm_chain = LLMChain(llm=llm, prompt=prompt, callbacks=[self.cb_handler])

        recursive_decomposition_agent = LLMSingleActionAgent(
            llm_chain=llm_chain, output_parser=output_parser, stop=["\n\n"], allowed_tools=tool_names
        )

        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=recursive_decomposition_agent, tools=tools, verbose=True, callbacks=[self.cb_handler]
        )
        return agent_executor

    def run_agent(self, question: str, **kwargs):
        """
        Run question on the agent
        """

        agent_executor = self.create_agent(**kwargs)
        agent_executor.invoke({"question": question}, config={"callbacks": [self.cb_handler]})

        ##### LLM call to get final answer ######

        prompt = "Question: " + question + "\n\n"
        prompt += "Sub Questions and Answers\n"
        for i in range(len(self.ledger.question_trace)):
            prompt += "Sub Question: " + str(self.ledger.question_trace[i]) + "\n"
            prompt += "Sub Answer: " + str(self.ledger.answer_trace[i]) + "\n"
        prompt += "\nFinal Answer: "

        return prompt

    def retriever(self, query: str) -> List[str]:
        """
        Searches for the answer from a given context.
        """

        vs = get_vectorstore(vectorstore, document_embedder)
        if vs is None:
            return []

        logger.info(f"Skipping top k and confidence threshold for query decomposition rag")
        # TODO: Use similarity score threshold and top k provided in config
        # Currently it's raising an error during invoke.
        retriever = vs.as_retriever()
        result = retriever.get_relevant_documents(query, callbacks=[self.cb_handler])
        logger.debug(result)
        return [hit.page_content for hit in result]

    def extract_answer(self, chunks: List[str], question: str) -> str:
        """
        Find the answer to the query from the retrieved chunks
        """

        prompt = "Below is a Question and set of Passages that may or may not be relevant. Your task is to Extract the answer for question using only the information available in the passages. Be as concise as possible and only include the answer if present. Do not infer or process the passage in any other way\n\n"
        prompt += "Question: " + question + "\n\n"
        for idx, chunk in enumerate(chunks):
            prompt += f"Passage {idx + 1}:\n"
            prompt += chunk + "\n"
        llm = get_llm(**self.kwargs)
        answer = llm([HumanMessage(content=prompt)])
        return answer.content

    def search(self, sub_questions: List[str]):
        """
        Search for the answer for each subquestion and add them to the ledger.
        """

        logger.info(f"Entering search with subquestions: {sub_questions}")
        for sub_question in sub_questions:
            chunk = self.retriever(sub_question)
            sub_answer = self.extract_answer(chunk, sub_question)

            self.ledger.question_trace.append(sub_question)
            self.ledger.answer_trace.append(sub_answer)

    def math(self, sub_questions: List[str]):
        """
        Places an LLM call to answer mathematical subquestions which do not require search
        """
        try:
            prompt = f"{math_tool_prompt}\nQuestion: {sub_questions[0]}"
            prompt += f"Context:\n{fetch_context(self.ledger)}\n"
            logger.info(f"Performing Math LLM call with prompt: {prompt}")
            llm = get_llm(**self.kwargs)
            sub_answer = llm([HumanMessage(content=prompt)])
            sub_answer = json.loads(sub_answer.content)
            final_sub_answer = str(sub_answer['variable1']) + sub_answer['operation'] + str(sub_answer['variable2'])
            final_sub_answer = final_sub_answer + '=' + str(eval(final_sub_answer))
        except:
            prompt = "Solve this mathematical question:\nQuestion: " + sub_questions[0]
            prompt += f"Context:\n{fetch_context(self.ledger)}\n"
            prompt += "Be concise and only return the answer."

            logger.info(f"Performing Math LLM call with prompt: {prompt}")
            llm = get_llm(**self.kwargs)
            sub_answer = llm([HumanMessage(content=prompt)])
            final_sub_answer = sub_answer.content

        self.ledger.question_trace.append(sub_questions[0])
        self.ledger.answer_trace.append(final_sub_answer)

        self.ledger.done = True

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters."""

        try:
            vs = get_vectorstore(vectorstore, document_embedder)
            if vs != None:
                logger.info(f"Skipping top k and confidence threshold for query decomposition rag")

                # TODO: Use top k and confidence threshold once retriever issue is resolved
                retriever = vs.as_retriever()
                docs = retriever.get_relevant_documents(content, callbacks=[self.cb_handler])

                result = []
                for doc in docs:
                    result.append(
                        {"source": os.path.basename(doc.metadata.get('source', '')), "content": doc.page_content}
                    )
                return result
            return []
        except Exception as e:
            logger.error(f"Error from POST /search endpoint. Error details: {e}")
        return []

    def get_documents(self) -> List[str]:
        """Retrieves filenames stored in the vector store."""
        try:
            vs = get_vectorstore(vectorstore, document_embedder)
            if vs:
                return get_docs_vectorstore_langchain(vs)
        except Exception as e:
            logger.error(f"Vectorstore not initialized. Error details: {e}")
        return []

    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        try:
            vs = get_vectorstore(vectorstore, document_embedder)
            if vs:
                return del_docs_vectorstore_langchain(vs, filenames)
        except Exception as e:
            logger.error(f"Vectorstore not initialized. Error details: {e}")
