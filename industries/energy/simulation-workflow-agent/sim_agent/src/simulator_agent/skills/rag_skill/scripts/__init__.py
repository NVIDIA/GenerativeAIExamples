# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
Scripts for OPM RAG Skill

Support modules for retrieval-augmented generation. RAG tools (simulator_manual, simulator_examples)
are invoked via rag_chain.build_chain() in graph/nodes.py;
they are not implemented as standalone tool modules here.

Modules:
- rag_chain: LCEL chain for query → retrieval → LLM response
- query_milvus_with_filters: Milvus query with metadata filters
- nvidia_embedding: Embedding for queries and documents
- nvidia_reranker: Reranking of retrieval results
- extract_capitalized_words: Keyword extraction for metadata filters
- extract_keyword: RAG + LLM keyword extraction (summary metrics, input keywords)
"""

from .extract_keyword import AmbiguousQueryError, extract_keyword

__all__ = ["AmbiguousQueryError", "extract_keyword"]
