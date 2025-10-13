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

"""LLM Chains for executing Retrival Augmented Generation."""
import logging
import os
import pathlib
from typing import Generator, List

import pandas as pd
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers.string import StrOutputParser
from pandasai import Agent as PandasAI_Agent
from pandasai.responses.response_parser import ResponseParser

# pylint: disable=no-name-in-module, disable=import-error
from RAG.examples.advanced_rag.structured_data_rag.csv_utils import (
    extract_df_desc,
    get_prompt_params,
    is_result_valid,
    parse_prompt_config,
)
from RAG.src.chain_server.base import BaseExample
from RAG.src.chain_server.utils import get_config, get_llm, get_prompts
from RAG.src.pandasai.llms.nv_aiplay import NVIDIA as PandasAI_NVIDIA

logger = logging.getLogger(__name__)
settings = get_config()

INGESTED_CSV_FILES_LIST = "ingested_csv_files.txt"


class PandasDataFrame(ResponseParser):
    """Returns Pandas Dataframe instead of SmartDataFrame"""

    def __init__(self, context) -> None:
        super().__init__(context)

    def format_dataframe(self, result):
        return result["value"]


class CSVChatbot(BaseExample):
    """RAG example showcasing CSV parsing using Pandas AI Agent"""

    def compare_csv_columns(self, ref_csv_file, current_csv_file):
        """Compares columns of two CSV files"""

        ref_csv_file = ref_csv_file.replace('\n', '')
        current_csv_file = current_csv_file.replace('\n', '')
        logger.info(f"ref_csv_file: {ref_csv_file}, current_csv_file: {current_csv_file}")

        ref_df = pd.read_csv(ref_csv_file)
        curr_df = pd.read_csv(current_csv_file)

        if not curr_df.columns.equals(ref_df.columns):
            return False
        else:
            return True

    def read_and_concatenate_csv(self, file_paths_txt):
        """Reads CSVs and concatenates their data"""

        file_paths = None

        with open(file_paths_txt, "r", encoding="UTF-8") as file:
            file_paths = file.read().splitlines()

        concatenated_df = pd.DataFrame()
        reference_columns = None
        reference_file = None

        for i, path in enumerate(file_paths):
            df = pd.read_csv(path)

            if i == 0:
                reference_columns = df.columns
                concatenated_df = df
                reference_file = path
                logger.info(f"reference_columns: {reference_columns}, reference_file: {reference_file}")
            else:
                if not df.columns.equals(reference_columns):
                    raise ValueError(
                        f"Columns of the file {path} do not match the reference columns of {reference_file} file."
                    )
                concatenated_df = pd.concat([concatenated_df, df], ignore_index=True)

        return concatenated_df

    def ingest_docs(self, filepath: str, filename: str):
        """Ingest documents to the VectorDB."""

        if not filename.endswith(".csv"):
            raise ValueError(f"{filename} is not a valid CSV file")

        with open(INGESTED_CSV_FILES_LIST, "a+", encoding="UTF-8") as f:

            ref_csv_path = None

            try:
                f.seek(0)
                ref_csv_path = f.readline()
            except Exception as e:
                # Skip reading reference file path as this is the first file
                pass

            if not ref_csv_path:
                f.write(filepath + "\n")
            elif self.compare_csv_columns(ref_csv_path, filepath):
                f.write(filepath + "\n")
            else:
                raise ValueError(
                    f"Columns of the file {filepath} do not match the reference columns of {ref_csv_path} file."
                )

        logger.info("Document %s ingested successfully", filename)

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""

        logger.info("Using llm to generate response directly without knowledge base.")
        # WAR: Disable chat history (UI consistency).
        chat_history = []

        system_message = [("system", get_prompts().get("prompts").get("chat_template"))]
        conversation_history = [(msg.role, msg.content) for msg in chat_history]
        user_input = [("user", "{input}")]

        # Checking if conversation_history is not None and not empty
        prompt = (
            ChatPromptTemplate.from_messages(system_message + conversation_history + user_input)
            if conversation_history
            else ChatPromptTemplate.from_messages(system_message + user_input)
        )

        logger.info(f"Using prompt for response generation: {prompt.format(input=query)}")
        chain = prompt | get_llm(**kwargs) | StrOutputParser()
        return chain.stream({"input": query})

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")
        # WAR: Disable chat history (UI consistency).
        chat_history = []
        llm = get_llm(**kwargs)

        if not os.path.exists(INGESTED_CSV_FILES_LIST):
            return iter(["No CSV file ingested"])

        df = self.read_and_concatenate_csv(file_paths_txt=INGESTED_CSV_FILES_LIST)
        df = df.fillna(0)

        df_desc = extract_df_desc(df)
        prompt_config = get_prompts().get("prompts")

        logger.info(prompt_config.get("csv_prompts", []))
        data_retrieval_prompt_params = get_prompt_params(prompt_config.get("csv_prompts", []))
        llm_data_retrieval = PandasAI_NVIDIA(temperature=0.2, model=settings.llm.model_name_pandas_ai)

        config_data_retrieval = {"llm": llm_data_retrieval, "response_parser": PandasDataFrame, "max_retries": 6}
        agent_data_retrieval = PandasAI_Agent([df], config=config_data_retrieval, memory_size=20)
        data_retrieval_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(prompt_config.get("csv_data_retrieval_template", [])),
                HumanMessagePromptTemplate.from_template("{query}"),
            ],
            input_variables=["description", "instructions", "data_frame", "query"],
        )
        conversation_history = [(msg.role, msg.content) for msg in chat_history]
        conversation_history_messages = ChatPromptTemplate.from_messages(conversation_history).messages
        # Insert conversation_history between data_retrieval_prompt's SystemMessage & HumanMessage (query)
        if conversation_history_messages:
            data_retrieval_prompt.messages[1:1] = conversation_history_messages

        result_df = agent_data_retrieval.chat(
            data_retrieval_prompt.format_prompt(
                description=data_retrieval_prompt_params.get("description"),
                instructions=data_retrieval_prompt_params.get("instructions"),
                data_frame=df_desc,
                query=query,
            ).to_string()
        )
        logger.info("Result Data Frame: %s", result_df)
        if not is_result_valid(result_df):
            logger.warning("Retrieval failed to get any relevant context")
            return iter(["No response generated from LLM, make sure your query is relavent to the ingested document."])

        result_df = str(result_df)
        response_prompt_template = PromptTemplate(
            template=prompt_config.get("csv_response_template", []), input_variables=["query", "data"],
        )
        response_prompt = response_prompt_template.format(query=query, data=result_df)

        logger.info("Using prompt for response: %s", response_prompt)

        chain = response_prompt_template | llm | StrOutputParser()
        return chain.stream({"query": query, "data": result_df})

    def get_documents(self) -> List[str]:
        """Retrieves filenames stored in the vector store."""
        decoded_filenames = []
        if os.path.exists(INGESTED_CSV_FILES_LIST):
            with open(INGESTED_CSV_FILES_LIST, "r", encoding="UTF-8") as file:
                for csv_file_path in file.read().splitlines():
                    decoded_filenames.append(os.path.basename(csv_file_path))
        return decoded_filenames

    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        logger.error("delete_documents not implemented")
        return True
