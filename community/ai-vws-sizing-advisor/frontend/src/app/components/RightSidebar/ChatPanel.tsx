// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useState, useEffect, useRef } from "react";

interface ChatPanelProps {
  vgpuConfig: any;
  onSendMessage: (message: string) => void;
  chatHistory: Array<{ 
    role: "user" | "assistant"; 
    content: string;
    citations?: Array<{ text: string; source: string; document_type: string }>;
  }>;
  isLoading?: boolean;
  onCloseChat?: () => void;
}

export default function ChatPanel({
  vgpuConfig,
  onSendMessage,
  chatHistory,
  isLoading = false,
  onCloseChat,
}: ChatPanelProps) {
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage.trim());
      setInputMessage("");
    }
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, isLoading]);

  return (
    <div className="flex flex-col w-full h-full min-w-0">
      {/* Chat Header */}
      <div className="p-3 bg-[#252525] border-b border-neutral-700/30 flex-shrink-0">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
            Ask Questions About Your Configuration
          </h3>
          {onCloseChat && (
            <button
              onClick={onCloseChat}
              className="text-gray-400 hover:text-white transition-colors"
              title="Close chat"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Chat Messages - Scrollable */}
      <div 
        className="flex-1 p-3 space-y-3 bg-[#252525] min-h-0 overflow-y-auto chat-scrollbar"
      >
        {chatHistory.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm mb-4 text-gray-400">Examples</p>
            <div className="text-xs space-y-2">
              <div className="text-left space-y-1.5 text-gray-400 max-w-[200px] mx-auto">
                <p>- What does this profile mean?</p>
                <p>- Can it support 10 concurrent users?</p>
                <p>- Should I use the next larger profile?</p>
                <p>- What are the RAM requirements?</p>
              </div>
            </div>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 ${
                  msg.role === "user"
                    ? "bg-[#76b900] text-white"
                    : "bg-neutral-800/70 text-gray-200"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
              
              {/* Display citations if available */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 max-w-[85%] text-xs">
                  <div className="bg-neutral-900/50 border border-neutral-700/50 rounded-lg p-2">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <svg className="w-3.5 h-3.5 text-[#76b900]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="text-gray-400 font-medium">Referenced Documents:</span>
                    </div>
                    <div className="space-y-1">
                      {[...new Set(msg.citations.map(c => c.source))].map((source, i) => (
                        <div key={i} className="text-gray-400 pl-5">
                          • {source.split('/').pop() || source}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-neutral-800/70 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-[#76b900]"></div>
                <span className="text-sm text-gray-400">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - At bottom of chat panel */}
      <div className="p-4 bg-[#252525] border-t border-neutral-700/30 flex-shrink-0 min-w-0">
        <form onSubmit={handleSubmit} className="flex gap-2 w-full min-w-0">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask a question about your configuration..."
            disabled={isLoading}
            className="flex-1 min-w-0 rounded-lg bg-neutral-800/50 border border-neutral-700 px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#76b900] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-[#76b900] hover:bg-[#5a8c00] text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm flex-shrink-0"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

