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
import { Citation } from "@/types/chat";

interface CitationsProps {
  citations?: Citation[];
}

const renderCitationContent = (citation: Citation) => {
  switch (citation.document_type) {
    case "image":
    case "table":
    case "chart":
      return (
        <div className="relative h-48 w-full">
          <Image
            src={`data:image/png;base64,${citation.text}`}
            alt={`Citation ${citation.document_type}`}
            fill
            className="object-contain"
          />
        </div>
      );

    case "text":
    default:
      return <p className="mb-4 text-sm text-gray-400">{citation.text}</p>;
  }
};

export default function Citations({ citations = [] }: CitationsProps) {
  if (!citations || citations.length === 0) {
    return (
      <div className="p-4 text-center text-gray-400">
        No citations available for this response.
      </div>
    );
  }

  return (
    <div className="space-y-6 text-gray-400">
      {citations.map((citation, index) => (
        <div
          key={index}
          className="max-h-72 overflow-y-auto rounded-lg border border-neutral-800 p-4"
        >
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium">Source {index + 1}</h3>
          </div>
          {renderCitationContent(citation)}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Source:</span>
            <span className="text-xs text-gray-400">{citation.source}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
