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

import { NextRequest } from "next/server";
import { API_CONFIG } from "@/app/config/api";
import { APIError, createErrorResponse } from "../../utils/api-utils";

const EXPLAIN_API_URL = process.env.NEXT_PUBLIC_RAG_API_URL 
  ? `${process.env.NEXT_PUBLIC_RAG_API_URL}/configuration/explain`
  : "http://localhost:8081/v1/configuration/explain";

interface ConfigurationExplanationRequest {
  configuration: any;
  context_documents?: any[];
  model?: string;
  embedding_model?: string;
}

// POST /configuration/explain - Get explanation for a vGPU configuration
export async function POST(request: NextRequest) {
  try {
    const body: ConfigurationExplanationRequest = await request.json();

    if (!body.configuration) {
      throw new APIError("configuration is required", 400);
    }

    // Forward the request to the RAG API and stream the response
    const response = await fetch(EXPLAIN_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        configuration: body.configuration,
        context_documents: body.context_documents,
        model: body.model || process.env.NEXT_PUBLIC_MODEL_NAME,
        embedding_model: body.embedding_model || process.env.NEXT_PUBLIC_EMBEDDING_MODEL,
      }),
    });

    if (!response.ok) {
      throw new APIError(
        `RAG API error: ${response.statusText}`,
        response.status,
        await response.text()
      );
    }

    // Set up SSE response
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // Forward the chunks as they come
            controller.enqueue(value);
          }
        } finally {
          reader.releaseLock();
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("Error in configuration explain route:", error);
    return createErrorResponse(error);
  }
} 