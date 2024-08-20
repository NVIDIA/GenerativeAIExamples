# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Base interface that all RAG examples should implement."""

from abc import ABC, abstractmethod
from typing import Generator, List


class BaseExample(ABC):
    """This class defines the basic structure for building RAG chain server examples.
    All RAG chain server example classes should inherit from this base class and implement the
    abstract methods to define their specific functionality.
    """

    @abstractmethod
    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Implements the LLM chain logic specific to the example.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `False`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.

        Returns:
            Generator[str, None, None]: A generator that yields strings, representing the tokens of the LLM chain.
        """

        pass

    @abstractmethod
    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Implements the RAG chain logic specific to the example.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `True`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.

        Returns:
            Generator[str, None, None]: A generator that yields strings, representing the steps or outputs of the RAG chain.
        """

        pass

    @abstractmethod
    def ingest_docs(self, data_dir: str, filename: str) -> None:
        """Defines how documents are ingested for processing by the RAG chain server example.
        It's called when the POST endpoint of`/documents` API is invoked.

        Args:
            filepath (str): The path to the document file.
            filename (str): The name of the document file.
        """

        pass
