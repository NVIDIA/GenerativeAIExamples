# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from abc import ABC
from abc import abstractmethod
from typing import List, Dict, Any

class BaseIngestor(ABC):
    """This class defines the basic structure for building Rag Ingestor."""

    @abstractmethod
    def ingest_docs(self, filepaths: List[str], **kwargs) -> Dict[str, Any]:
        """Defines how documents are ingested for processing by the RAG rag server example.
        It's called when the POST endpoint of`/documents` API is invoked.

        Arguments:
            - filepaths: List[str] - List of absolute filepaths
            - collection_name: str - VectorDB collection name
        """
        pass
