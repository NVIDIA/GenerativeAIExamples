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

"use client";

import { useState, useRef, useEffect } from "react";
import Collections from "../Collections/Collections";
import RightSidebar from "../RightSidebar/RightSidebar";
import MessageInput from "./MessageInput";
import { v4 as uuidv4 } from "uuid";
import { useApp } from "../../context/AppContext";
import { API_CONFIG } from "@/app/config/api";
import { marked } from "marked";
import { useChatStream } from "../../hooks/useChatStream";
import { ChatMessage, GenerateRequest } from "@/types/chat";
import { useSettings } from "../../context/SettingsContext";
import { useSidebar } from "../../context/SidebarContext";

export default function Chat() {
  const { activePanel, toggleSidebar, setActiveCitations } = useSidebar();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { streamState, processStream, startStream, resetStream, stopStream } =
    useChatStream();

  const { selectedCollection } = useApp();
  const {
    temperature,
    topP,
    vdbTopK,
    rerankerTopK,
    useGuardrails,
    includeCitations,
  } = useSettings();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleToggleSidebar = (
    panel: "citations" | "settings",
    citations?: {
      text: string;
      source: string;
      document_type: "text" | "image" | "table" | "chart";
    }[]
  ) => {
    if (panel === "citations" && citations) {
      setActiveCitations(citations);
      if (!activePanel || activePanel !== "citations") {
        toggleSidebar(panel);
      }
    } else {
      toggleSidebar(panel);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async () => {
    if (!message.trim()) return;

    resetStream();
    const controller = startStream();

    const userMessage = createUserMessage(message);
    const assistantMessage = createAssistantMessage();

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setMessage("");

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(createRequestBody(userMessage)),
        signal: controller.signal,
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      await processStream(response, assistantMessage.id, setMessages);
    } catch (error: unknown) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Stream aborted");
        return;
      }
      console.error("Error generating response:", error);
      handleError(assistantMessage.id);
    }
  };

  const renderMessageContent = (content: string, isTyping: boolean) => {
    if (isTyping) {
      return <span className="typing-dots">Thinking</span>;
    }
    return (
      <div
        className="prose prose-invert max-w-none text-sm"
        dangerouslySetInnerHTML={{
          __html: marked.parse(content, {
            async: false,
            breaks: true,
            gfm: true,
          }),
        }}
      />
    );
  };

  const createUserMessage = (content: string): ChatMessage => ({
    id: uuidv4(),
    role: "user",
    content,
    timestamp: new Date().toISOString(),
  });

  const createAssistantMessage = (): ChatMessage => ({
    id: uuidv4(),
    role: "assistant",
    content: "",
    timestamp: new Date().toISOString(),
  });

  const createRequestBody = (userMessage: ChatMessage) => {
    // Create base request body
    const requestBody: GenerateRequest = {
      messages: messages.concat(userMessage).map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
      collection_name: selectedCollection || "",
      temperature,
      top_p: topP,
      reranker_top_k: rerankerTopK,
      vdb_top_k: vdbTopK,
      use_knowledge_base: !!selectedCollection,
      enable_citations: includeCitations,
      enable_guardrails: useGuardrails,
    };

    // Only include model parameters if the environment variables are set
    if (process.env.NEXT_PUBLIC_MODEL_NAME) {
      requestBody.model = process.env.NEXT_PUBLIC_MODEL_NAME;
    }

    if (process.env.NEXT_PUBLIC_EMBEDDING_MODEL) {
      requestBody.embedding_model = process.env.NEXT_PUBLIC_EMBEDDING_MODEL;
    }

    if (process.env.NEXT_PUBLIC_RERANKER_MODEL) {
      requestBody.reranker_model = process.env.NEXT_PUBLIC_RERANKER_MODEL;
    }

    return requestBody;
  };

  const handleError = (messageId: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? {
              ...msg,
              content: "Sorry, there was an error processing your request.",
            }
          : msg
      )
    );
  };

  const handleReset = () => {
    setMessages([]);
    resetStream();
    setMessage("");
  };

  return (
    <div className="flex h-[calc(100vh-56px)] bg-[#121212]">
      <Collections />
      <div
        className={`flex flex-1 transition-all duration-300 ${
          !!activePanel ? "mr-[400px]" : ""
        }`}
      >
        <div className="relative flex-1">
          <RightSidebar />
          <div className="flex h-full flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mx-auto max-w-3xl space-y-6">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-2xl rounded-lg p-4 ${
                        msg.role === "user"
                          ? "bg-neutral-800 text-white"
                          : "bg-neutral-800 text-white"
                      }`}
                    >
                      <div className="text-sm">
                        {msg.content
                          ? renderMessageContent(msg.content, false)
                          : msg.role === "assistant" && streamState.isTyping
                            ? renderMessageContent("", true)
                            : ""}
                      </div>
                      {msg.citations && (
                        <div className="mt-2 text-xs text-gray-400">
                          <button
                            onClick={() =>
                              handleToggleSidebar("citations", msg.citations)
                            }
                            className="text-[var(--nv-green)] hover:underline"
                          >
                            {msg.citations.length} Citations
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <div className="flex-shrink-0 border-t border-neutral-800">
              <MessageInput
                message={message}
                setMessage={setMessage}
                onSubmit={handleSubmit}
                onAbort={stopStream}
                isStreaming={streamState.isTyping}
                onReset={handleReset}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
