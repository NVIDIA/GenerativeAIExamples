// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

export interface Citation {
  text: string;
  source: string;
  document_type: "text" | "image" | "table" | "chart";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  citations?: Citation[];
}

export interface StreamState {
  content: string;
  citations: Citation[];
  error: string | null;
  isTyping: boolean;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface GenerateRequest {
  messages: Message[];
  use_knowledge_base?: boolean;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  reranker_top_k?: number;
  vdb_top_k?: number;
  vdb_endpoint?: string;
  collection_name: string;
  enable_query_rewriting?: boolean;
  enable_reranker?: boolean;
  enable_citations?: boolean;
  enable_guardrails?: boolean;
  model?: string;
  llm_endpoint?: string;
  embedding_model?: string;
  embedding_endpoint?: string;
  reranker_model?: string;
  reranker_endpoint?: string;
  stop?: string[];
}
