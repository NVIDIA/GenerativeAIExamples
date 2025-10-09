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
import ApplyConfigurationForm from "./ApplyConfigurationForm";

interface VGPUConfigDrawerProps {
  config: any;
  isOpen: boolean;
  onClose: () => void;
}

export default function VGPUConfigDrawer({ config, isOpen, onClose }: VGPUConfigDrawerProps) {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [isApplyFormOpen, setIsApplyFormOpen] = useState(false);

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
                  /* Compress/minimize icon when in fullscreen */
                  <svg className="w-5 h-5 text-white group-hover:text-green-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
                  </svg>
                ) : (
                  /* Expand fullscreen icon */
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
              <button 
                onClick={() => setIsApplyFormOpen(true)}
                className="px-4 py-2 bg-[#76b900] hover:bg-[#5a8c00] text-white rounded-lg font-medium transition-colors"
              >
                Verify Configuration
              </button>

            </div>

            
          </div>
        </div>
      </div>

      {/* Apply Configuration Form Modal */}
      <ApplyConfigurationForm 
        isOpen={isApplyFormOpen}
        onClose={() => setIsApplyFormOpen(false)}
        configuration={config}
      />
    </>
  );
} 