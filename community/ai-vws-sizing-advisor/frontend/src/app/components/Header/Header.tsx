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

import Image from "next/image";

interface HeaderProps {
  onToggleSidebar: (panel: "citations") => void;
  activePanel: "citations" | null;
}

export default function Header({ onToggleSidebar, activePanel }: HeaderProps) {
  // Pull model names from centralized configuration (via environment variables)
  const reasoningModel = (process.env.NEXT_PUBLIC_MODEL_NAME || "nvidia/llama-3.3-nemotron-super-49b-v1").replace(/^nvidia\//, '');
  const embeddingModel = (process.env.NEXT_PUBLIC_EMBEDDING_MODEL || "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1").replace(/^nvidia\//, '');

  return (
    <div className="flex h-14 items-center justify-between border-b border-neutral-800 bg-black px-4">
      <div className="flex items-center gap-2">
        <Image
          src="/nvidia-logo.svg"
          alt="NVIDIA Logo"
          width={128}
          height={24}
        />
        <span className="text-lg font-semibold text-white">AI vWS Sizing Advisor</span>
      </div>

      <div className="absolute left-1/2 -translate-x-1/2 transform"></div>
      <div className="flex items-center gap-3">
        <span className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-1 text-sm text-neutral-100">
          Reasoning: <span className="text-[#76b900]">{reasoningModel}</span>
        </span>
        <span className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-1 text-sm text-neutral-100">
          Embedding: <span className="text-[#76b900]">{embeddingModel}</span>
        </span>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={() => onToggleSidebar("citations")}
          className={`flex items-center gap-2 text-sm ${
            activePanel === "citations" ? "text-white" : "text-gray-400"
          } transition-colors hover:text-white`}
        >
          <Image
            src="/citations.svg"
            alt="Citations Icon"
            width={16}
            height={16}
          />
          Citations
        </button>
      </div>
    </div>
  );
}