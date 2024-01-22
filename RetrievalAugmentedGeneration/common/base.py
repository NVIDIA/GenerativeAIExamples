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
from typing import Generator

class BaseExample(ABC):

    @abstractmethod
    def llm_chain(self, context: str, question: str, num_tokens: int) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def rag_chain(self, prompt: str, num_tokens: int) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def ingest_docs(self, data_dir: str, filename: str) -> None:
        pass