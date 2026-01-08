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

import { useEffect, useState } from "react";
import Citations from "./Citations";
import ChatPanel from "./ChatPanel";
import { useSidebar } from "../../context/SidebarContext";

interface RightSidebarProps {
  vgpuConfig?: any;
  onSendChatMessage?: (message: string) => void;
  chatHistory?: Array<{ role: "user" | "assistant"; content: string }>;
  isChatLoading?: boolean;
}

export default function RightSidebar({
  vgpuConfig,
  onSendChatMessage,
  chatHistory = [],
  isChatLoading = false,
}: RightSidebarProps) {
  const { activePanel, closeSidebar, activeCitations } = useSidebar();
  const [displayPanel, setDisplayPanel] = useState(activePanel);

  useEffect(() => {
    if (activePanel) {
      setDisplayPanel(activePanel);
    } else {
      const timer = setTimeout(() => {
        setDisplayPanel(null);
      }, 300); // Match the transition duration
      return () => clearTimeout(timer);
    }
  }, [activePanel]);

  const getPanelTitle = () => {
    if (displayPanel === "citations") return "Citations";
    if (displayPanel === "chat") return "Configuration Chat";
    return "";
  };

  return (
    <div
      className={`fixed bottom-0 right-0 top-14 w-[450px] transform border-l border-neutral-800 bg-black transition-transform duration-300 ease-in-out ${
        !!activePanel ? "translate-x-0" : "translate-x-full"
      }`}
    >
      <div className="flex h-full flex-col">
        {displayPanel !== "chat" && (
          <div className="flex items-center justify-between border-b border-neutral-800 p-4">
            <h2 className="text-xl font-semibold text-white">
              {getPanelTitle()}
            </h2>
            <button
              onClick={closeSidebar}
              className="text-gray-400 transition-colors hover:text-white text-2xl leading-none"
              aria-label="Close sidebar"
            >
              ×
            </button>
          </div>
        )}
        <div className="flex-1 overflow-hidden">
          {displayPanel === "citations" && (
            <div className="h-full overflow-y-auto p-4">
              <Citations citations={activeCitations} />
            </div>
          )}
          {displayPanel === "chat" && onSendChatMessage && (
            <div className="h-full relative">
              <button
                onClick={closeSidebar}
                className="absolute top-4 right-4 z-10 text-gray-400 hover:text-white text-2xl leading-none"
                aria-label="Close chat"
              >
                ×
              </button>
              <ChatPanel
                vgpuConfig={vgpuConfig}
                onSendMessage={onSendChatMessage}
                chatHistory={chatHistory}
                isLoading={isChatLoading}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}