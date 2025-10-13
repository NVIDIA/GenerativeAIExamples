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

// API Configuration

export const API_CONFIG = {
  VDB: {
    BASE_URL:
      process.env.NEXT_PUBLIC_VDB_BASE_URL ?? "http://localhost:8082/v1",
    ENDPOINTS: {
      DOCUMENTS: {
        LIST: "/documents",
        UPLOAD: "/documents",
        DELETE: "/documents",
      },
      COLLECTIONS: {
        LIST: "/collections",
        CREATE: "/collections",
        DELETE: "/collections",
      },
    },
    VDB_ENDPOINT: process.env.NEXT_PUBLIC_VDB_ENDPOINT ?? "http://milvus:19530",
  },
  CHAT: {
    BASE_URL:
      process.env.NEXT_PUBLIC_CHAT_BASE_URL ?? "http://localhost:8081/v1",
    ENDPOINTS: {
      RAG: {
        GENERATE: "/generate",
        CHAT_COMPLETIONS: "/chat/completions",
      },
      SEARCH: {
        QUERY: "/search",
      },
    },
  },
};

// Helper function to build a URL with query parameters
export const buildQueryUrl = (
  url: string,
  params: Record<string, string | number>
) => {
  const queryParams = new URLSearchParams();

  queryParams.append("vdb_endpoint", API_CONFIG.VDB.VDB_ENDPOINT);

  // Add other params
  Object.entries(params).forEach(([key, value]) => {
    queryParams.append(key, value.toString());
  });

  return `${url}?${queryParams.toString()}`;
};

// Helper function to create a Message object
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export const createMessage = (
  role: "user" | "assistant" | "system",
  content: string
): ChatMessage => ({
  role,
  content,
});
