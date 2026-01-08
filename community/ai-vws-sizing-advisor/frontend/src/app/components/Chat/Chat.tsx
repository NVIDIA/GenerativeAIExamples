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
import WorkloadConfigWizard from "./WorkloadConfigWizard";
import ApplyConfigurationForm from "./ApplyConfigurationForm";
import ChatPanel from "../RightSidebar/ChatPanel";
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
  const [isApplyFormOpen, setIsApplyFormOpen] = useState(false);
  const [applyFormConfig, setApplyFormConfig] = useState<any>(null);
  const [showPassthroughError, setShowPassthroughError] = useState(false);
  const [lastVGPUConfig, setLastVGPUConfig] = useState<any>(null); // Track last vGPU config for context
  const [showChatPanel, setShowChatPanel] = useState(false); // Show inline chat panel
  const [chatPanelHistory, setChatPanelHistory] = useState<Array<{ 
    role: "user" | "assistant"; 
    content: string;
    citations?: Array<{ text: string; source: string; document_type: string }>;
  }>>([]);
  const [isChatPanelLoading, setIsChatPanelLoading] = useState(false);
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
    
    // Update citations in sidebar if panel is already open
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === "assistant" && lastMessage.citations && lastMessage.citations.length > 0) {
      // Only update citations if the panel is already open
      if (activePanel === "citations") {
        setActiveCitations(lastMessage.citations);
      }
    }
  }, [messages, activePanel, setActiveCitations]);

  // Separate effect to extract vGPU config (only depends on messages, not activePanel)
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === "assistant" && lastMessage.content) {
      try {
        const parsed = JSON.parse(lastMessage.content.trim());
        if (parsed.title === "generate_vgpu_config" && parsed.parameters) {
          // Only reset chat history if this is a NEW config (different from last one)
          setLastVGPUConfig((prevConfig: any) => {
            const prevProfileId = prevConfig?.parameters?.vgpu_profile || prevConfig?.parameters?.vGPU_profile;
            const newProfileId = parsed.parameters?.vgpu_profile || parsed.parameters?.vGPU_profile;
            
            // Only reset chat history if this is actually a new config
            if (prevProfileId !== newProfileId || !prevConfig) {
              setChatPanelHistory([]);
            }
            
            return parsed;
          });
        }
      } catch {
        // Not a JSON config, ignore
      }
    }
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

  const renderMessageContent = (content: string, isTyping: boolean, messageId: string) => {
    if (isTyping) {
      return (
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-[#76b900]"></div>
            <span className="text-gray-400">Generating configuration...</span>
          </div>
        </div>
      );
    }
    
    // Check if content is a vGPU configuration JSON
    if (isVGPUConfig(content)) {
      try {
        const vgpuConfig = JSON.parse(content.trim());
        
        // Return a preview card with inline details AND chat panel (always expanded)
        return (
          <div className="w-full flex justify-center">
            <div className="relative w-[80%]">
              <div className="bg-[#252525] border border-[#76b900]/30 rounded-lg p-4 relative">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-[#76b900]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
                <h3 className="text-white font-semibold text-lg">vGPU Configuration Suggestion</h3>
              </div>
            
              <p className="text-sm text-gray-300 mb-2">
                {(() => {
                  // Only highlight the LAST occurrence of (FP8)/(FP16)/(FP4) - the precision indicator
                  const desc = vgpuConfig.description;
                  const precisionMatch = desc.match(/^(.*)\((FP[4816]+)\)(\s*)$/i);
                  if (precisionMatch) {
                    // Split the non-precision part for Inference/RAG highlighting
                    const mainPart = precisionMatch[1];
                    const precision = precisionMatch[2];
                    return (
                      <>
                        {mainPart.split(/(Inference|RAG)/gi).map((part: string, i: number) =>
                          /^(Inference|RAG)$/i.test(part) ? (
                            <span key={i} className="font-bold text-[#76b900]">{part}</span>
                          ) : part
                        )}
                        (<span className="font-semibold text-yellow-400">{precision.toUpperCase()}</span>)
                      </>
                    );
                  }
                  // No precision suffix, just highlight Inference/RAG
                  return desc.split(/(Inference|RAG)/gi).map((part: string, i: number) =>
                    /^(Inference|RAG)$/i.test(part) ? (
                      <span key={i} className="font-bold text-[#76b900]">{part}</span>
                    ) : part
                  );
                })()}
              </p>
              
              {(vgpuConfig.parameters.vgpu_profile || vgpuConfig.parameters.vGPU_profile) && (
                <div className="flex items-center gap-4 text-sm mb-4">
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
              
              {/* Inline Configuration Details with Chat Panel */}
              <div className="mb-2">
                  <div className="flex flex-col lg:flex-row items-start bg-transparent rounded-lg min-w-0 gap-2">
                    {/* Configuration Details - 70% on large screens, 100% on small - NO scrollbar */}
                    <div className="w-full lg:w-[70%] flex-shrink min-w-0 overflow-visible">
                      <VGPUConfigCard config={vgpuConfig} hideAdvancedDetails={true} />
                    </div>
                    
                    {/* Chat Panel - 30% on large screens (right side), 100% on small (below) 
                        Height adjusts based on workload type: RAG configs need more space */}
                    <div className={`w-full lg:w-[30%] flex-shrink-0 min-w-[250px] border border-neutral-700/30 rounded-lg overflow-hidden flex ${
                      vgpuConfig.parameters?.rag_breakdown?.workload_type === 'rag' ? 'h-[680px]' : 'h-[580px]'
                    }`}>
                      <ChatPanel
                        vgpuConfig={vgpuConfig}
                        onSendMessage={handleChatPanelMessage}
                        chatHistory={chatPanelHistory}
                        isLoading={isChatPanelLoading}
                      />
                    </div>
                  </div>
                  
                  {/* Advanced Details - Full width below both panels */}
                  <div className="w-full overflow-visible">
                    <VGPUConfigCard config={vgpuConfig} showOnlyAdvancedDetails={true} />
                  </div>
                </div>
              
              {/* Divider Line */}
              <div className="w-full h-px bg-neutral-700/50 my-4"></div>
              
              {/* Action Buttons - Side by Side */}
              <div className="flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    
                    // Check if this is a GPU passthrough configuration (vgpu_profile is null)
                    const profile = vgpuConfig.parameters?.vgpu_profile || vgpuConfig.parameters?.vGPU_profile;
                    if (!profile) {
                      setShowPassthroughError(true);
                      return;
                    }
                    
                    setApplyFormConfig(vgpuConfig);
                    setIsApplyFormOpen(true);
                  }}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Verify Configuration Locally
                </button>
                
                {/* Size Another Configuration Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsWizardOpen(true);
                  }}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2"
                  title="Open Workload Configuration Wizard"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                  Create Another Sizing Recommendation
                </button>
              </div>
            </div>
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

  const handleChatPanelMessage = async (message: string) => {
    if (!lastVGPUConfig) return;

    setIsChatPanelLoading(true);
    setChatPanelHistory((prev) => [...prev, { role: "user", content: message }]);

    // Extract configuration details for context
    const profileId = lastVGPUConfig.parameters?.vgpu_profile || lastVGPUConfig.parameters?.vGPU_profile || 'GPU Passthrough';
    const gpuMemory = lastVGPUConfig.parameters?.gpu_memory_size || 'N/A';
    const vcpuCount = lastVGPUConfig.parameters?.vcpu_count || lastVGPUConfig.parameters?.vCPU_count || 'N/A';
    const systemRAM = lastVGPUConfig.parameters?.system_RAM || lastVGPUConfig.parameters?.RAM || 'N/A';
    const precision = lastVGPUConfig.parameters?.precision || 'FP8';
    
    // RAG-specific fields
    const ragBreakdown = lastVGPUConfig.parameters?.rag_breakdown || {};
    const ragConfig = lastVGPUConfig.parameters?.rag_config || {};
    const embeddingModel = lastVGPUConfig.parameters?.embedding_model 
      || ragConfig.embedding_model 
      || ragBreakdown.embedding_model 
      || '';
    const vectorDbVectors = lastVGPUConfig.parameters?.vector_db_vectors 
      || ragConfig.total_vectors 
      || ragBreakdown.vector_db_vectors 
      || '';
    const vectorDbDimension = lastVGPUConfig.parameters?.vector_db_dimension 
      || ragConfig.vector_dimension 
      || ragBreakdown.vector_db_dimension 
      || '';
    const embeddingMemory = ragBreakdown.embedding_memory || '';
    const vectorDbMemory = ragBreakdown.vector_db_memory || '';
    const isRagWorkload = lastVGPUConfig.description?.toLowerCase().includes('rag') || !!embeddingModel;
    
    // Get model tag
    let modelTag = lastVGPUConfig.parameters?.model_tag || lastVGPUConfig.parameters?.model_name || '';
    if (!modelTag && lastVGPUConfig.description) {
      const patterns = [/inference of ([^\s(]+)/i, /for RAG \(([^)]+)\)/i, /(Nemotron[^\s(]+)/i, /(Llama[^\s(]+)/i];
      for (const p of patterns) {
        const m = lastVGPUConfig.description.match(p);
        if (m) { modelTag = m[1].trim(); break; }
      }
    }
    modelTag = modelTag || 'N/A';
    
    // Get model parameter count
    const getModelParams = (tag: string): string => {
      const t = tag.toLowerCase();
      if (t.includes('30b')) return '30 billion';
      if (t.includes('70b')) return '70 billion';
      if (t.includes('8b')) return '8 billion';
      if (t.includes('7b')) return '7 billion';
      if (t.includes('3b')) return '3 billion';
      if (t.includes('1b')) return '1 billion';
      if (t.includes('49b')) return '49 billion (Mixture of Experts)';
      return 'unknown';
    };
    const modelParams = getModelParams(modelTag);

    // Build workload context
    let workloadContext = '';
    if (isRagWorkload) {
      workloadContext = `
This is a RAG (Retrieval-Augmented Generation) workload:
- LLM Model: ${modelTag} (${modelParams} parameters, ${precision} precision)
- Embedding Model: ${embeddingModel}${embeddingMemory ? ` (requires ${embeddingMemory})` : ''}
${vectorDbVectors ? `- Vector Database: ${vectorDbVectors} vectors` : ''}
${vectorDbDimension ? `- Vector Dimension: ${vectorDbDimension}D` : ''}
${vectorDbMemory ? `- Vector DB Memory: ${vectorDbMemory}` : ''}`;
    } else {
      workloadContext = `
This is an Inference workload:
- Model: ${modelTag} (${modelParams} parameters, ${precision} precision)`;
    }

    // Create context message for RAG server
    const contextMessage = `You are a helpful AI assistant. Answer the user's question directly and conversationally.

Context - The user is asking about this vGPU configuration:
- Profile: ${profileId} | GPU Memory: ${gpuMemory}GB | vCPUs: ${vcpuCount} | RAM: ${systemRAM}GB
${workloadContext}

CRITICAL INSTRUCTIONS:
- Answer in plain text ONLY. NO JSON. NO structured output.
- Use your general knowledge about LLMs, GPUs, and AI to answer questions
- If asked about the profile: Explain vGPU naming (e.g., BSE-24Q = BSE GPU with 24GB VRAM, Q suffix = time-sliced vGPU)
- For RAG questions: Explain how the embedding model and LLM work together
- Use retrieved documentation to support your answers when relevant
- Be concise and helpful`;

    try {
      const chatTemperature = Math.min(temperature + 0.1, 1.0);

      const requestBody: GenerateRequest = {
        messages: [
          { role: "system", content: contextMessage },
          ...chatPanelHistory.map(msg => ({ role: msg.role, content: msg.content })),
          { role: "user", content: message }
        ],
        collection_name: "vgpu_knowledge_base",
        temperature: chatTemperature,
        top_p: topP,
        reranker_top_k: rerankerTopK,
        vdb_top_k: vdbTopK,
        confidence_threshold: confidenceScoreThreshold,
        use_knowledge_base: true,
        enable_citations: true,
        enable_query_rewriting: true,
        enable_reranker: true,
        enable_guardrails: useGuardrails,
        conversational_mode: true,
      };

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
      });

      if (!response.ok) throw new Error("RAG server error");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      let assistantMsg = "";
      let citations: Array<{ text: string; source: string; document_type: string }> = [];
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.choices?.[0]?.delta?.content) {
                assistantMsg += data.choices[0].delta.content;
              }
              if (data.citations && Array.isArray(data.citations)) {
                citations = data.citations;
              }
            } catch (e) {}
          }
        }
      }

      // Process response - handle JSON structured output and plain text
      let finalMessage = assistantMsg || "No response";
      try {
        const trimmed = assistantMsg.trim();
        if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
          const parsed = JSON.parse(trimmed);
          if (parsed.title && parsed.parameters) {
            if (parsed.description && !parsed.description.includes('generate_vgpu_config')) {
              let desc = parsed.description;
              if (/^(BSE|L40S?|A40|L4)\s+with\s+vGPU\s+profile/i.test(desc)) {
                finalMessage = `The ${profileId} profile provides ${gpuMemory}GB of GPU memory. This configuration is sized for running ${modelTag}. Is there something specific you'd like to know about this setup?`;
              } else {
                finalMessage = desc;
              }
            } else {
              finalMessage = `Based on your configuration (${profileId} with ${gpuMemory}GB), I can help answer questions about the profile, model requirements, or performance expectations. What would you like to know?`;
            }
          } else if (parsed.description) {
            finalMessage = parsed.description;
          }
        }
      } catch (e) {
        // Not JSON - use as is (this is the expected case for chat responses)
      }

      setChatPanelHistory((prev) => [...prev, { 
        role: "assistant", 
        content: finalMessage,
        citations: citations.length > 0 ? citations : undefined
      }]);
    } catch (error) {
      console.error("Chat panel error:", error);
      setChatPanelHistory((prev) => [...prev, { 
        role: "assistant", 
        content: "Error from rag-server. Please check rag-server logs for more details."
      }]);
    } finally {
      setIsChatPanelLoading(false);
    }
  };

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
    <div className="flex h-[calc(100vh-56px)] bg-[#1a1a1a]">
      <div
        className={`flex flex-1 transition-all duration-300 ${
          !!activePanel ? "mr-[400px]" : ""
        }`}
      >
        <div className="relative flex-1">
          <RightSidebar 
            vgpuConfig={lastVGPUConfig}
            onSendChatMessage={handleChatPanelMessage}
            chatHistory={chatPanelHistory}
            isChatLoading={isChatPanelLoading}
          />
          <div className="flex h-full flex-col w-full">
            <div className="flex-1 overflow-y-auto p-4 w-full bg-[#1a1a1a]">
              {/* Show centered button when no messages */}
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <button
                    onClick={() => setIsWizardOpen(true)}
                    className="bg-gradient-to-r from-green-600 to-green-700 text-white px-8 py-5 rounded-lg shadow-lg hover:from-green-700 hover:to-green-800 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center space-x-3"
                    title="Open Workload Configuration Wizard"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                    <span className="text-lg font-semibold">Create vGPU Sizing Recommendation</span>
                  </button>
                </div>
              ) : (
                <div className="min-h-full flex items-center justify-center">
                  <div className="space-y-4 w-full flex flex-col">
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex w-full ${
                          msg.role === "user" ? "justify-end" : "justify-center"
                        }`}
                      >
                        <div
                          className={`${msg.role === "user" ? "w-auto max-w-[80%]" : "w-full"} ${
                            msg.role === "user"
                              ? "text-white"
                              : "text-white"
                          }`}
                        >
                          <div className="text-sm">
                            {msg.content
                              ? renderMessageContent(msg.content, false, msg.id)
                              : msg.role === "assistant" && streamState.isTyping
                                ? renderMessageContent("", true, msg.id)
                                : ""}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                </div>
              )}
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

      {/* Apply Configuration Form Modal */}
      <ApplyConfigurationForm 
        isOpen={isApplyFormOpen}
        onClose={() => setIsApplyFormOpen(false)}
        configuration={applyFormConfig}
      />

      {/* GPU Passthrough Error Modal */}
      {showPassthroughError && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-900 border border-yellow-500/50 rounded-xl shadow-2xl max-w-md w-full animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="bg-gradient-to-r from-yellow-600/20 to-orange-600/20 border-b border-yellow-500/30 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-500/20 rounded-lg">
                  <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-yellow-500">GPU Passthrough Required</h3>
                  <p className="text-sm text-gray-400">Local verification unavailable</p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-5 space-y-4">
              <div className="space-y-3 text-gray-300">
                <p className="leading-relaxed">
                  This workload <span className="font-semibold text-white">requires direct GPU access</span> and cannot be tested with the local vLLM deployment feature.
                </p>
                <div className="bg-neutral-800/50 border border-neutral-700 rounded-lg p-4 space-y-2">
                  <p className="text-sm font-medium text-yellow-400">Why is this happening?</p>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    Your workload exceeds the maximum vGPU profile capacity and requires <span className="font-medium text-white">full GPU passthrough</span> mode. This configuration must be deployed directly on hardware with GPU passthrough enabled.
                  </p>
                </div>
                <p className="text-sm text-gray-400">
                  Please deploy this configuration on your production environment with the recommended GPU passthrough setup.
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-neutral-800/50 border-t border-neutral-700 flex justify-end">
              <button
                onClick={() => setShowPassthroughError(false)}
                className="px-6 py-2.5 bg-[#76b900] hover:bg-[#5a8c00] text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}