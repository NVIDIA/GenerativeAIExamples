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

import { ReactNode } from "react";
import Image from "next/image";

// Basic modal props
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  // File upload props (all optional)
  description?: string;
  isLoading?: boolean;
  error?: string | null;
  selectedFiles?: File[];
  submitButtonText?: string;
  isSubmitDisabled?: boolean;
  onFileSelect?: (files: File[]) => void;
  onRemoveFile?: (index: number) => void;
  onReset?: () => void;
  onSubmit?: () => void;
  fileInputId?: string;
  // Custom content to render before the file upload area
  customContent?: ReactNode;
}

export default function Modal({
  isOpen,
  onClose,
  title,
  description,
  isLoading = false,
  error = null,
  selectedFiles = [],
  submitButtonText = "Submit",
  isSubmitDisabled = false,
  onFileSelect,
  onRemoveFile,
  onReset,
  onSubmit,
  fileInputId = "fileInput",
  customContent,
}: ModalProps) {
  if (!isOpen) return null;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && onFileSelect) {
      const files = Array.from(e.target.files);
      onFileSelect(files);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="mx-4 w-full max-w-lg rounded-lg bg-[#1A1A1A]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-neutral-800 p-4">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 transition-colors hover:text-white"
            aria-label="Close modal"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className="p-4 text-white">
          {description && (
            <div className="mb-4">
              <p className="text-sm text-gray-400">{description}</p>
            </div>
          )}

          {customContent}

          <div className="mb-4">
            <label className="mb-2 block text-sm font-medium">
              Source Files
            </label>
            <div
              className="cursor-pointer rounded-lg border-2 border-dashed border-gray-600 p-4 text-center transition-colors hover:border-[var(--nv-green)]"
              onClick={() => document.getElementById(fileInputId)?.click()}
            >
              <input
                id={fileInputId}
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                accept=".docx,.jpeg,.pdf,.png,.pptx,.svg,.tiff,.txt"
              />
              <div className="flex flex-col items-center justify-center">
                <Image
                  src="/file.svg"
                  alt="Upload files"
                  width={32}
                  height={32}
                  className="mb-2 opacity-50"
                />
                <p className="mb-1 text-sm text-gray-400">
                  Click to upload or drag and drop
                </p>
                <p className="text-xs text-gray-500">
                  Supported file types: DOCX, JPEG,
                  PDF, PNG, PPTX, SVG, TIFF, TXT
                </p>
              </div>
            </div>
          </div>

          {selectedFiles.length > 0 && (
            <div className="mb-4">
              <h3 className="mb-2 text-sm font-medium">Selected Files</h3>
              <div className="scrollbar-thin scrollbar-track-neutral-900 scrollbar-thumb-neutral-700 max-h-48 space-y-2 overflow-y-auto pr-1">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-md bg-neutral-800 px-3 py-2"
                  >
                    <span className="truncate text-sm">{file.name}</span>
                    <button
                      onClick={() => onRemoveFile && onRemoveFile(index)}
                      className="text-gray-400 transition-colors hover:text-white"
                      aria-label={`Remove ${file.name}`}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="mb-4 rounded-md bg-red-900/50 p-3 text-sm text-red-200">
              {error}
            </div>
          )}

          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={onReset}
              className="px-4 py-2 text-sm text-gray-400 transition-colors hover:text-white"
              disabled={isLoading}
              aria-label="Reset form fields"
            >
              Reset
            </button>
            <button
              onClick={onSubmit}
              disabled={isSubmitDisabled || isLoading}
              className="flex items-center gap-2 rounded-md bg-[var(--nv-green)] px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-[#8CCF00] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>{isLoading ? "Processing..." : submitButtonText}</span>
                </>
              ) : (
                submitButtonText
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
