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

import { useState, useCallback } from "react";
import { SourceResult } from "@/types/api";
import { ChatMessage, StreamState, Citation } from "@/types/chat";

export const useChatStream = () => {
  const [streamState, setStreamState] = useState<StreamState>({
    content: "",
    citations: [],
    error: null,
    isTyping: false,
  });

  const [abortController, setAbortController] = useState<AbortController>(
    new AbortController()
  );

  const resetAbortController = useCallback(() => {
    const controller = new AbortController();
    setAbortController(controller);
    return controller;
  }, []);

  const stopStream = useCallback(() => {
    abortController.abort();
    setStreamState((prev) => ({ ...prev, isTyping: false }));
  }, [abortController]);

  const processStream = useCallback(
    async (
      response: Response,
      assistantMessageId: string,
      setMessages: (fn: (prev: ChatMessage[]) => ChatMessage[]) => void
    ) => {
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";
      let content = "";
      let latestCitations: Citation[] = [];

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          buffer += chunk;

          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.trim() === "" || !line.startsWith("data: ")) continue;

            try {
              const data = JSON.parse(line.slice(5));

              if (
                data.choices[0].message.content.includes(
                  "Error from rag server"
                )
              ) {
                throw new Error("RAG server error");
              }

              // Handle delta content
              const deltaContent = data.choices[0].delta.content;
              if (deltaContent) {
                content += deltaContent;
              }

              // Update citations
              if (data.citations?.results?.length > 0) {
                latestCitations = data.citations.results.map(
                  (source: SourceResult) => ({
                    text: source.content,
                    source: source.document_name,
                    document_type: source.document_type || "text",
                  })
                );
              }

              // Update message state
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        content,
                        citations:
                          latestCitations.length > 0
                            ? latestCitations
                            : msg.citations,
                      }
                    : msg
                )
              );

              // Handle stream completion
              if (data.choices[0].finish_reason === "stop") {
                setStreamState((prev) => ({
                  ...prev,
                  content,
                  citations: latestCitations,
                  isTyping: false,
                }));
                break;
              }
            } catch (parseError) {
              if (!(parseError instanceof SyntaxError)) {
                throw parseError;
              }
            }
          }
        }
      } catch (error) {
        setStreamState((prev) => ({
          ...prev,
          error: "Sorry, there was an error processing your request.",
          isTyping: false,
        }));
        throw error;
      } finally {
        reader.releaseLock();
      }
    },
    []
  );

  const startStream = useCallback(() => {
    const controller = resetAbortController();
    setStreamState((prev) => ({ ...prev, isTyping: true, error: null }));
    return controller;
  }, [resetAbortController]);

  const resetStream = useCallback(() => {
    setStreamState({
      content: "",
      citations: [],
      error: null,
      isTyping: false,
    });
  }, []);

  return {
    streamState,
    processStream,
    startStream,
    resetStream,
    stopStream,
    isStreaming: streamState.isTyping,
  };
};
