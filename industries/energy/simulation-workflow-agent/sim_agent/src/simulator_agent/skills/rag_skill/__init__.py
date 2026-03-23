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
OPM RAG Skill for OPM Flow

This skill provides retrieval tools for accessing OPM Flow documentation and example files.
Follows the Agent Skills specification: https://agentskills.io/specification

Structure:
- SKILL.md: Skill metadata and instructions
- test.py: Test suite
- scripts/: Support modules (rag_chain, query_milvus_with_filters, nvidia_embedding, nvidia_reranker, extract_capitalized_words)
- references/: Additional documentation
- assets/: Static resources

Note: RAG tools (simulator_manual, simulator_examples) are invoked directly via rag_chain.build_chain()
in graph/nodes.py. They are not implemented as standalone tool modules in
scripts/, but executed through the rag_chain LCEL pipeline at runtime.

Based on TOOL_DECISION_TREE.md Section 2.5 (Keyword Q&A flow) and Section 2.4 (Scenario test chain).

Tools:
- simulator_manual: Retrieve information from OPM Flow manual and documentation
- simulator_examples: Retrieve example OPM DATA files and case studies
"""

# RAG tools are invoked via rag_chain.build_chain() in graph/nodes.py.
# They are not imported here as they require vector store configuration.
# This __init__.py exists for skill structure consistency.

__all__ = []
