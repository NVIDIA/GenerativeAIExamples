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

import { useState, useEffect } from "react";
import VGPUConfigCard from "./VGPUConfigCard";

interface VGPUConfigDrawerProps {
  config: any;
  isOpen: boolean;
  onClose: () => void;
}

export default function VGPUConfigDrawer({ config, isOpen, onClose }: VGPUConfigDrawerProps) {
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Close drawer on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 z-40 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`fixed inset-y-0 right-0 z-50 bg-neutral-950 shadow-2xl transition-all duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        } ${
          isFullScreen ? "w-full" : "w-full md:w-[600px] lg:w-[700px] xl:w-[800px]"
        }`}
      >
        {/* Drawer Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-[#76b900] to-[#5a8c00] px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-white">vGPU Configuration Details</h2>
              {isFullScreen && (
                <span className="text-sm text-green-100 opacity-75">Full Screen Mode</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {/* Full Screen Toggle */}
              <button
                onClick={() => setIsFullScreen(!isFullScreen)}
                className="p-2 hover:bg-white/10 rounded transition-colors group"
                title={isFullScreen ? "Exit full screen" : "Enter full screen"}
              >
                {isFullScreen ? (
                  <svg className="w-5 h-5 text-white group-hover:text-green-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-white group-hover:text-green-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                )}
              </button>
              {/* Close Button */}
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded transition-colors group"
                title="Close drawer"
              >
                <svg className="w-5 h-5 text-white group-hover:text-green-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Drawer Content */}
        <div className="h-full overflow-y-auto pb-20">
          <div className={`p-6 ${isFullScreen ? "max-w-6xl mx-auto" : ""}`}>
            {config && <VGPUConfigCard config={config} />}
            
            {/* Additional Actions */}
            <div className="mt-6 flex flex-wrap gap-3">
              <button className="px-4 py-2 bg-[#76b900] hover:bg-[#5a8c00] text-white rounded-lg font-medium transition-colors">
                Apply Configuration
              </button>
              <button className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg font-medium transition-colors border border-neutral-700">
                Export as JSON
              </button>
              <button className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg font-medium transition-colors border border-neutral-700">
                Compare Configurations
              </button>
            </div>

            {/* Quick Actions Bar */}
            <div className="mt-8 p-4 bg-neutral-900/50 rounded-lg border border-neutral-800">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Quick Actions</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button className="p-3 bg-neutral-800/50 hover:bg-neutral-800 rounded-lg text-sm text-gray-300 hover:text-white transition-all border border-neutral-700/50 hover:border-[#76b900]/30">
                  <svg className="w-4 h-4 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy Config
                </button>
                <button className="p-3 bg-neutral-800/50 hover:bg-neutral-800 rounded-lg text-sm text-gray-300 hover:text-white transition-all border border-neutral-700/50 hover:border-[#76b900]/30">
                  <svg className="w-4 h-4 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download
                </button>
                <button className="p-3 bg-neutral-800/50 hover:bg-neutral-800 rounded-lg text-sm text-gray-300 hover:text-white transition-all border border-neutral-700/50 hover:border-[#76b900]/30">
                  <svg className="w-4 h-4 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m9.032 4.026a9.001 9.001 0 010-5.368m0 5.368a9.001 9.001 0 01-5.368 0m5.368 0c-.751.285-1.538.5-2.358.636a10.97 10.97 0 01-.388-2.436m0-2.684c.084-.816.232-1.61.436-2.376.894.136 1.765.351 2.598.636" />
                  </svg>
                  Share
                </button>
                <button className="p-3 bg-neutral-800/50 hover:bg-neutral-800 rounded-lg text-sm text-gray-300 hover:text-white transition-all border border-neutral-700/50 hover:border-[#76b900]/30">
                  <svg className="w-4 h-4 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                  </svg>
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
} 