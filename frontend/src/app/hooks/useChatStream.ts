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
      setMessages: (fn: (prev: ChatMessage[]) => ChatMessage[]) => void,
      confidenceScoreThreshold?: number
    ) => {
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";
      let content = "";
      let latestCitations: Citation[] = [];

      // Log the threshold we're using for debugging
      console.log(`Starting stream with confidence threshold: ${confidenceScoreThreshold}, type: ${typeof confidenceScoreThreshold}`);

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
              console.log("Stream data type:", typeof data, "structure:", Object.keys(data).join(", "));

              if (
                data.choices?.[0]?.message?.content?.includes(
                  "Error from rag server"
                )
              ) {
                throw new Error("RAG server error");
              }

              // Handle delta content
              const deltaContent = data.choices?.[0]?.delta?.content;
              if (deltaContent) {
                content += deltaContent;
              }

              // Check for citations in different possible locations in the response
              let citationsData = null;
              // Try to find citations data in various possible locations
              if (data.citations?.results) {
                citationsData = data.citations.results;
              } else if (data.sources?.results) {
                citationsData = data.sources.results;
              } else if (Array.isArray(data.citations)) {
                citationsData = data.citations;
              } else if (Array.isArray(data.sources)) {
                citationsData = data.sources;
              } else if (data.choices?.[0]?.message?.citations) {
                citationsData = Array.isArray(data.choices[0].message.citations) 
                  ? data.choices[0].message.citations 
                  : data.choices[0].message.citations.results || [];
              } else if (data.choices?.[0]?.message?.sources) {
                citationsData = Array.isArray(data.choices[0].message.sources) 
                  ? data.choices[0].message.sources 
                  : data.choices[0].message.sources.results || [];
              }

              // Update citations with filtering based on confidence score
              if (citationsData && citationsData.length > 0) {
                // Map the sources to our Citation type, preserving the score
                const sourcesWithScores: Citation[] = citationsData.map(
                  (source: any) => {
                    // Get score from different possible locations
                    const score = 
                      source.score !== undefined ? source.score : 
                      source.confidence_score !== undefined ? source.confidence_score : 
                      source.similarity_score !== undefined ? source.similarity_score : 
                      source.relevance_score !== undefined ? source.relevance_score :
                      undefined;
                    
                    const sourceTitle = source.document_name || source.source || source.title || source.filename || "Unknown source";
                    console.log(`Source "${sourceTitle}" has score: ${score}`);
                    
                    return {
                      text: source.content || source.text || source.snippet || "",
                      source: sourceTitle,
                      document_type: source.document_type || "text",
                      score: score
                    };
                  }
                );
                
                console.log("All citation scores:", sourcesWithScores.map(c => `${c.source}: ${c.score !== undefined ? c.score : 'N/A'}`).join(', '));
                
                // Only apply filtering if threshold is provided and valid
                const validThreshold = confidenceScoreThreshold !== undefined && 
                                      !isNaN(parseFloat(String(confidenceScoreThreshold)));
                
                if (validThreshold) {
                  // Parse the threshold as a number
                  let normalizedThreshold = parseFloat(String(confidenceScoreThreshold));
                  
                  // Ensure threshold is within 0-1 range (UI now uses the same 0-1 scale as the API)
                  normalizedThreshold = Math.max(0, Math.min(1, normalizedThreshold));
                  
                  console.log(`Using threshold: ${normalizedThreshold} (original: ${confidenceScoreThreshold})`);
                  
                  latestCitations = sourcesWithScores.filter(citation => {
                    // If score is undefined, include the citation (don't filter it out)
                    if (citation.score === undefined) {
                      console.log(`Citation "${citation.source}" has no score, including it anyway`);
                      return true;
                    }
                    
                    // Ensure score is a number
                    const score = typeof citation.score === 'string' ? parseFloat(citation.score) : citation.score;
                    
                    // Both citation scores from API and UI threshold are on a 0-1 scale
                    // so we can compare them directly
                    
                    const passesThreshold = score >= normalizedThreshold;
                    console.log(`Citation "${citation.source}" with score ${score} passes threshold ${normalizedThreshold}? ${passesThreshold}`);
                    return passesThreshold;
                  });
                } else {
                  console.log("No valid confidence threshold set, including all citations");
                  latestCitations = sourcesWithScores;
                }
                
                console.log(`Filtered citations: ${latestCitations.length} / ${sourcesWithScores.length} with threshold ${confidenceScoreThreshold}`);
                console.log("Remaining citations:", latestCitations.map(c => c.source).join(', '));
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
              if (data.choices?.[0]?.finish_reason === "stop") {
                setStreamState((prev) => ({
                  ...prev,
                  content,
                  citations: latestCitations,
                  isTyping: false,
                }));
                break;
              }
            } catch (parseError) {
              console.error("Error parsing stream data:", parseError);
              if (!(parseError instanceof SyntaxError)) {
                throw parseError;
              }
            }
          }
        }
      } catch (error) {
        console.error("Stream processing error:", error);
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
