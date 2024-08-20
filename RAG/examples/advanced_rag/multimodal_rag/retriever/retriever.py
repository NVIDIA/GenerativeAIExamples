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

from pydantic import BaseModel
from RAG.examples.advanced_rag.multimodal_rag.retriever.embedder import Embedder
from RAG.examples.advanced_rag.multimodal_rag.retriever.vector import VectorClient


class Retriever(BaseModel):

    embedder: Embedder
    vector_client: VectorClient
    search_limit: int = 4

    def get_relevant_docs(self, text, limit=None):
        if limit is None:
            limit = self.search_limit
        query_vector = self.embedder.embed_query(text)
        concatdocs, sources = self.vector_client.search([query_vector], limit)
        return concatdocs, sources
