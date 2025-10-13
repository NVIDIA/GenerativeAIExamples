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
import { GenerateRequest } from "@/types/chat";
import { APIError, createErrorResponse } from "../utils/api-utils";
import { API_CONFIG } from "@/app/config/api";

const RAG_API_URL = `${API_CONFIG.CHAT.BASE_URL}${API_CONFIG.CHAT.ENDPOINTS.RAG.GENERATE}`;

// POST /generate - Get response for a given query
export async function POST(request: NextRequest) {
  try {
    const body: GenerateRequest = await request.json();

    if (!body.messages || body.messages.length === 0) {
      throw new APIError("messages array is required and cannot be empty", 400);
    }

    // Forward the request to the RAG API and stream the response
    const response = await fetch(RAG_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
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

            // Decode and log the chunk
            const text = new TextDecoder().decode(value);
            console.log("Streaming chunk:", text);

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
    console.error("Error in generate route:", error);
    return createErrorResponse(error);
  }
}
