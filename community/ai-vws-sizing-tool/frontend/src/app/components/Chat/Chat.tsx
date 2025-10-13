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
import RightSidebar from "../RightSidebar/RightSidebar";
import VGPUConfigCard from "./VGPUConfigCard";
import VGPUConfigDrawer from "./VGPUConfigDrawer";
import WorkloadConfigWizard from "./WorkloadConfigWizard";
import ApplyConfigurationForm from "./ApplyConfigurationForm";
import { v4 as uuidv4 } from "uuid";
import { API_CONFIG } from "@/app/config/api";
import { marked } from "marked";
import { useChatStream } from "../../hooks/useChatStream";
import { ChatMessage, GenerateRequest } from "@/types/chat";
import { useSettings } from "../../context/SettingsContext";
import { useSidebar } from "../../context/SidebarContext";

export default function Chat() {
  const { activePanel, toggleSidebar, setActiveCitations } = useSidebar();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [drawerConfig, setDrawerConfig] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isApplyFormOpen, setIsApplyFormOpen] = useState(false);
  const [applyFormConfig, setApplyFormConfig] = useState<any>(null);
  const { streamState, processStream, startStream, resetStream, stopStream } =
    useChatStream();

  const {
    temperature,
    topP,
    vdbTopK,
    rerankerTopK,
    confidenceScoreThreshold,
    useGuardrails,
    includeCitations,
  } = useSettings();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleToggleSidebar = (
    panel: "citations",
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

  const handleSubmit = async (message: string) => {
    if (!message.trim()) return;

    resetStream();
    const controller = startStream();

    const userMessage = createUserMessage(message);
    const assistantMessage = createAssistantMessage();

    setMessages((prev) => [...prev, userMessage, assistantMessage]);

    // Debug confidence score threshold being used
    console.log(`Submitting with confidence threshold: ${confidenceScoreThreshold} (value type: ${typeof confidenceScoreThreshold})`);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(createRequestBody(userMessage)),
        signal: controller.signal,
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      await processStream(response, assistantMessage.id, setMessages, confidenceScoreThreshold);
    } catch (error: unknown) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Stream aborted");
        return;
      }
      console.error("Error generating response:", error);
      handleError(assistantMessage.id);
    }
  };

  const isVGPUConfig = (content: string): boolean => {
    try {
      const parsed = JSON.parse(content.trim());
      return parsed.title === "generate_vgpu_config" && parsed.parameters;
    } catch {
      return false;
    }
  };

  const renderMessageContent = (content: string, isTyping: boolean) => {
    if (isTyping) {
      return (
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-[#76b900]"></div>
          <span className="text-gray-400">Generating configuration...</span>
        </div>
      );
    }
    
    // Check if content is a vGPU configuration JSON
    if (isVGPUConfig(content)) {
      try {
        const vgpuConfig = JSON.parse(content.trim());
        // Return a preview card that opens the drawer
        return (
          <div className="bg-neutral-800 border border-[#76b900]/30 rounded-lg p-4">
            <div 
              className="cursor-pointer hover:bg-neutral-750 transition-all duration-200 rounded-lg -m-4 p-4 mb-0"
              onClick={() => {
                setDrawerConfig(vgpuConfig);
                setIsDrawerOpen(true);
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-[#76b900]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                  <h3 className="text-white font-semibold">vGPU Configuration Ready</h3>
                </div>
                <span className="text-xs text-gray-400">Click to view details →</span>
              </div>
              <p className="text-sm text-gray-300 mb-3">{vgpuConfig.description}</p>
              {(vgpuConfig.parameters.vgpu_profile || vgpuConfig.parameters.vGPU_profile) && (
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-400">Profile:</span>
                  <span className="text-[#76b900] font-medium">{vgpuConfig.parameters.vgpu_profile || vgpuConfig.parameters.vGPU_profile}</span>
                  {vgpuConfig.parameters.gpu_memory_size && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span className="text-gray-400">Memory:</span>
                      <span className="text-[#76b900] font-medium">{vgpuConfig.parameters.gpu_memory_size} GB</span>
                    </>
                  )}
                </div>
              )}
            </div>
            
            {/* Verify Configuration Button */}
            <div className="mt-4 pt-4 border-t border-neutral-700">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setApplyFormConfig(vgpuConfig);
                  setIsApplyFormOpen(true);
                }}
                className="w-full px-4 py-2 bg-[#76b900] hover:bg-[#5a8c00] text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Verify Configuration
              </button>
            </div>
          </div>
        );
      } catch (error) {
        console.error("Error parsing vGPU config:", error);
        // Fall back to regular markdown rendering
      }
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
    // Create base request body - always use the vGPU knowledge base
    const requestBody: GenerateRequest = {
      messages: messages.concat(userMessage).map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
      collection_name: "vgpu_knowledge_base",  // Always use the pre-loaded collection
      temperature,
      top_p: topP,
      reranker_top_k: rerankerTopK,
      vdb_top_k: vdbTopK,
      confidence_threshold: confidenceScoreThreshold,
      use_knowledge_base: true,  // Always use knowledge base
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

  const handleWizardSubmit = async (generatedQuery: string) => {
    // Process query silently without showing it as a user message
    if (!generatedQuery.trim()) return;

    resetStream();
    const controller = startStream();

    // Clear previous messages and only show the new configuration
    setMessages([]);
    
    // Only create assistant message (no user message shown)
    const assistantMessage = createAssistantMessage();
    setMessages([assistantMessage]);

    // Debug confidence score threshold being used
    console.log(`Submitting wizard query with confidence threshold: ${confidenceScoreThreshold}`);

    try {
      // Create the request with the query but don't show it in chat
      const silentUserMessage = createUserMessage(generatedQuery);
      const requestBody: GenerateRequest = {
        messages: [silentUserMessage].map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
        collection_name: "vgpu_knowledge_base",
        temperature,
        top_p: topP,
        reranker_top_k: rerankerTopK,
        vdb_top_k: vdbTopK,
        confidence_threshold: confidenceScoreThreshold,
        use_knowledge_base: true,
        enable_citations: includeCitations,
        enable_guardrails: useGuardrails,
      };

      // Include model parameters if set
      if (process.env.NEXT_PUBLIC_MODEL_NAME) {
        requestBody.model = process.env.NEXT_PUBLIC_MODEL_NAME;
      }
      if (process.env.NEXT_PUBLIC_EMBEDDING_MODEL) {
        requestBody.embedding_model = process.env.NEXT_PUBLIC_EMBEDDING_MODEL;
      }
      if (process.env.NEXT_PUBLIC_RERANKER_MODEL) {
        requestBody.reranker_model = process.env.NEXT_PUBLIC_RERANKER_MODEL;
      }

      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      await processStream(response, assistantMessage.id, setMessages, confidenceScoreThreshold);
    } catch (error: unknown) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Stream aborted");
        return;
      }
      console.error("Error generating response:", error);
      handleError(assistantMessage.id);
    }
  };

  return (
    <div className="flex h-[calc(100vh-56px)] bg-[#121212]">
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
              <div className="p-4">
                <button
                  onClick={() => setIsWizardOpen(true)}
                  className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white p-4 rounded-lg shadow-lg hover:from-green-700 hover:to-green-800 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center space-x-3"
                  title="Open Workload Configuration Wizard"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                  <span className="text-lg font-bold">vGPU</span>
                  <span className="font-medium">Initialize Sizing Job</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Workload Configuration Wizard */}
      <WorkloadConfigWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onSubmit={handleWizardSubmit}
      />

      {/* vGPU Configuration Drawer */}
      <VGPUConfigDrawer
        config={drawerConfig}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />

      {/* Apply Configuration Form Modal */}
      <ApplyConfigurationForm 
        isOpen={isApplyFormOpen}
        onClose={() => setIsApplyFormOpen(false)}
        configuration={applyFormConfig}
      />
    </div>
  );
}