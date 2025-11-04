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

  // Debug the received citations
  console.log("Citations component received:", citations);

  // Check if citation source is a PDF
  const isPDF = (source: string) => {
    return source.toLowerCase().endsWith('.pdf');
  };

  // Extract filename from source path
  const getFileName = (source: string) => {
    return source.split('/').pop() || source;
  };

  // Handle PDF download
  const handleDownload = async (source: string) => {
    const fileName = getFileName(source);
    try {
      // Request the PDF from the backend
      const response = await fetch(`/api/download-citation?source=${encodeURIComponent(source)}`);
      
      if (!response.ok) {
        throw new Error('Failed to download PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF. Please try again.');
    }
  };

  return (
    <div className="space-y-6 text-gray-400">
      <div className="mb-2 p-2 text-center text-sm">
        <span className="font-medium">Showing {citations.length} citations</span>
        <div className="mt-1 text-xs text-gray-500">
          Click the download icon to save vGPU documentation PDFs
        </div>
      </div>
      {citations.map((citation, index) => (
        <div
          key={index}
          className="max-h-72 overflow-y-auto rounded-lg border border-neutral-800 p-4"
        >
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium">Source {index + 1}</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-neutral-900">
                Score: {citation.score !== undefined ? citation.score.toFixed(2) : "N/A"}
              </span>
              {isPDF(citation.source) && (
                <button
                  onClick={() => handleDownload(citation.source)}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-[var(--nv-green)] hover:bg-[var(--nv-green-hover)] text-white rounded transition-colors"
                  title={`Download ${getFileName(citation.source)}`}
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  PDF
                </button>
              )}
            </div>
          </div>
          {renderCitationContent(citation)}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-1">
              <span className="text-xs text-gray-500">Source:</span>
              <span className="text-xs text-gray-400 truncate">{getFileName(citation.source)}</span>
            </div>
            {isPDF(citation.source) && (
              <span className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-300 border border-blue-700/30">
                vGPU Doc
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
