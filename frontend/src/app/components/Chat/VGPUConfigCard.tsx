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

import { useState, ReactNode } from "react";

interface VGPUConfig {
  title: string;
  description: string;
  parameters: {
    vgpu_profile?: string | null;
    total_CPU_count?: number | null;
    vcpu_count?: number | null;
    gpu_memory_size?: number | null;
    system_RAM?: number | null;
    concurrent_users?: number | null;
    // Legacy fields for backward compatibility (to be removed)
    vGPU_profile?: string | null;
    total_CPUs?: number | null;
    vCPU_count?: number | null;
    video_card_total_memory?: number | null;
    storage_capacity?: number | null;
    storage_type?: string | null;
    driver_version?: string | null;
    AI_framework?: string | null;
    performance_tier?: string | null;
    relevant_aiwb_toolkit?: string | null;
    RAM?: number | null;
  };
  // Optional fields for enhanced context
  host_capabilities?: {
    max_ram?: number;
    available_gpus?: string[];
    cpu_cores?: number;
  };
  rationale?: string;
  notes?: string[];
}

interface VGPUConfigCardProps {
  config: VGPUConfig;
}

// Tooltip component
const Tooltip = ({ content, children }: { content: string; children: ReactNode }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="cursor-help"
      >
        {children}
      </div>
      {isVisible && (
        <div className="absolute z-10 px-3 py-2 text-xs text-white bg-gradient-to-br from-[#76b900]/20 to-[#76b900]/10 border border-[#76b900]/30 rounded-md shadow-lg backdrop-blur-sm -top-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
          {content}
          <div className="absolute w-2 h-2 bg-[#76b900]/15 border-l border-b border-[#76b900]/30 transform rotate-45 -bottom-1 left-1/2 -translate-x-1/2"></div>
        </div>
      )}
    </div>
  );
};

// Parameter definitions for tooltips
const parameterDefinitions: { [key: string]: string } = {
  vgpu_profile: "Virtual GPU profile that defines the GPU partitioning and resource allocation",
  vGPU_profile: "Virtual GPU profile that defines the GPU partitioning and resource allocation",
  total_CPU_count: "Total number of physical CPU cores on the host node",
  total_CPUs: "Total number of physical CPU cores available in the host system",
  vcpu_count: "Calculated as: ceil(concurrent_users × CPU-factor × 1.2), capped by total_CPU_count",
  vCPU_count: "Number of virtual CPU cores allocated to this configuration",
  gpu_memory_size: "Total VRAM (in GB) needed = sum(model_params in billions) × precision_factor × 1.2 overhead × concurrent_users",
  system_RAM: "System memory (in GB) allocated to this VM, including OS and framework overhead",
  concurrent_users: "Number of simultaneous inference users expected on this VM",
  // Legacy fields (kept for backward compatibility)
  video_card_total_memory: "Total physical memory available on the GPU hardware",
  storage_capacity: "Total storage space allocated for the workload",
  storage_type: "Type of storage (SSD, NVMe, HDD) for optimal performance",
  driver_version: "NVIDIA driver version required for this configuration",
  AI_framework: "AI/ML framework optimized for this configuration",
  performance_tier: "Performance level classification for this setup"
};

// Key parameters that should be in the primary section
const keyParameters = ['vgpu_profile', 'vGPU_profile', 'gpu_memory_size', 'system_RAM', 'vcpu_count', 'vCPU_count', 'concurrent_users'];

// Icon component using SVG instead of emojis
const ParameterIcon = ({ type, className = "w-4 h-4" }: { type: string; className?: string }) => {
  const iconClass = className;
  
  switch (type) {
    case 'vGPU_profile':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
      );
    case 'cpu':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      );
    case 'memory':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      );
    case 'storage':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
        </svg>
      );
    case 'framework':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      );
    case 'users':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      );
    default:
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      );
  }
};

const getIconType = (key: string): string => {
  switch (key) {
    case 'vgpu_profile':
    case 'vGPU_profile':
      return 'vGPU_profile';
    case 'total_CPU_count':
    case 'total_CPUs':
    case 'vcpu_count':
    case 'vCPU_count':
      return 'cpu';
    case 'gpu_memory_size':
    case 'video_card_total_memory':
    case 'system_RAM':
    case 'RAM':
      return 'memory';
    case 'storage_capacity':
    case 'storage_type':
      return 'storage';
    case 'AI_framework':
    case 'relevant_aiwb_toolkit':
      return 'framework';
    case 'concurrent_users':
      return 'users';
    default:
      return 'default';
  }
};

export default function VGPUConfigCard({ config }: VGPUConfigCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showAdvancedDetails, setShowAdvancedDetails] = useState(false);
  const [showRawJSON, setShowRawJSON] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  const formatParameterValue = (key: string, value: any): string => {
    if (value === null || value === undefined) {
      return "Not specified";
    }
    
    switch (key) {
      case 'gpu_memory_size':
      case 'video_card_total_memory':
      case 'system_RAM':
      case 'RAM':
      case 'storage_capacity':
        return `${value} GB`;
      case 'vgpu_profile':
      case 'vGPU_profile':
        return value;
      case 'total_CPU_count':
      case 'total_CPUs':
      case 'vcpu_count':
      case 'vCPU_count':
        return `${value} cores`;
      case 'concurrent_users':
        return `${value} users`;
      case 'storage_type':
      case 'driver_version':
      case 'AI_framework':
      case 'relevant_aiwb_toolkit':
      case 'performance_tier':
        return String(value);
      default:
        return String(value);
    }
  };

  const getParameterLabel = (key: string): string => {
    switch (key) {
      case 'vgpu_profile':
      case 'vGPU_profile':
        return 'vGPU Profile';
      case 'total_CPU_count':
      case 'total_CPUs':
        return 'Total CPUs';
      case 'vcpu_count':
      case 'vCPU_count':
        return 'vCPU Count';
      case 'gpu_memory_size':
        return 'GPU Memory';
      case 'video_card_total_memory':
        return 'Video Card Total Memory';
      case 'system_RAM':
        return 'System RAM';
      case 'RAM':
        return 'RAM';
      case 'storage_capacity':
        return 'Storage Capacity';
      case 'storage_type':
        return 'Storage Type';
      case 'driver_version':
        return 'Driver Version';
      case 'AI_framework':
        return 'AI Framework';
      case 'relevant_aiwb_toolkit':
        return 'AI Toolkit';
      case 'performance_tier':
        return 'Performance Tier';
      case 'concurrent_users':
        return 'Concurrent Users';
      default:
        return key.replace(/_/g, ' ').replace(/^./, str => str.toUpperCase());
    }
  };

  const isRelevantConfig = Object.values(config.parameters).some(value => value !== null && value !== undefined);

  // Separate key and advanced parameters
  const keyParams = Object.entries(config.parameters).filter(([key]) => 
    keyParameters.includes(key) && config.parameters[key as keyof typeof config.parameters] !== null
  );
  
  const advancedParams = Object.entries(config.parameters).filter(([key]) => 
    !keyParameters.includes(key) && config.parameters[key as keyof typeof config.parameters] !== null
  );

  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg overflow-hidden shadow-lg">
      {/* Header with NVIDIA green gradient */}
      <div className="bg-gradient-to-r from-[#76b900] to-[#5a8c00] text-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">vGPU Configuration Recommendation</h3>
            <p className="text-sm text-green-100 mt-0.5 opacity-90">Optimized for your AI workload requirements</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowRawJSON(!showRawJSON)}
              className="p-2 hover:bg-white/10 rounded transition-colors"
              title="Toggle Raw JSON"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </button>
            <button
              onClick={handleCopy}
              className="p-2 hover:bg-white/10 rounded transition-colors"
              title="Copy JSON"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 hover:bg-white/10 rounded transition-colors"
            >
              <svg className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
        {copied && (
          <div className="mt-2 text-sm text-green-100 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Copied to clipboard
          </div>
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-6">
          {/* Description */}
          {config.description && (
            <div className="mb-6 p-5 bg-gradient-to-br from-[#76b900]/10 to-[#76b900]/5 rounded-lg border border-[#76b900]/20 backdrop-blur-sm">
              <p className="text-gray-100 text-sm leading-relaxed">
                {config.description}
              </p>
            </div>
          )}

          {/* Why this config section */}
          {(config.rationale || isRelevantConfig) && (
            <div className="mb-6 p-4 bg-blue-950/30 border border-blue-900/50 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-blue-300 font-medium text-sm mb-1">Why this configuration?</h4>
                  <p className="text-blue-200/80 text-sm">
                    {config.rationale || "This configuration balances performance and resource efficiency for your specific AI workload, ensuring optimal GPU utilization while maintaining cost-effectiveness."}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Host Capabilities Context */}
          {config.host_capabilities && (
            <div className="mb-6 p-4 bg-gray-800/30 border border-gray-700/50 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
                <div className="w-full">
                  <h4 className="text-gray-300 font-medium text-sm mb-3">Detected Host Capabilities</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {config.host_capabilities.max_ram && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500 text-sm">Max RAM:</span>
                        <span className="text-gray-300 font-medium">{config.host_capabilities.max_ram} GB</span>
                      </div>
                    )}
                    {config.host_capabilities.cpu_cores && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500 text-sm">CPU Cores:</span>
                        <span className="text-gray-300 font-medium">{config.host_capabilities.cpu_cores}</span>
                      </div>
                    )}
                    {config.host_capabilities.available_gpus && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500 text-sm">Available GPUs:</span>
                        <span className="text-gray-300 font-medium">{config.host_capabilities.available_gpus.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {showRawJSON ? (
            /* Raw JSON View */
            <div className="bg-black rounded-lg p-4 overflow-x-auto border border-neutral-800">
              <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                {JSON.stringify(config, null, 2)}
              </pre>
            </div>
          ) : (
            /* Structured Configuration View */
            <div className="space-y-6">
              {/* Key Parameters Section */}
              {keyParams.length > 0 && (
                <div>
                  <h4 className="text-white font-medium text-sm mb-4 uppercase tracking-wider">Key Parameters</h4>
                  <div className="bg-neutral-850/40 rounded-lg p-4 border border-neutral-700/60">
                    <div className="grid gap-4 md:grid-cols-2">
                      {keyParams.map(([key, value], index) => (
                        <div
                          key={key}
                          className="flex items-center justify-between p-4 rounded-lg bg-neutral-800/70 border border-neutral-700/60 hover:bg-neutral-800 hover:border-[#76b900]/40 transition-all duration-200 group"
                        >
                          <div className="flex items-center gap-3">
                            <div className="text-gray-400 group-hover:text-[#76b900]/70 transition-colors">
                              <ParameterIcon type={getIconType(key)} />
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-200">
                                {getParameterLabel(key)}
                              </span>
                              {parameterDefinitions[key] && (
                                <Tooltip content={parameterDefinitions[key]}>
                                  <svg className="w-4 h-4 text-gray-500 hover:text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                </Tooltip>
                              )}
                            </div>
                          </div>
                          <span className="text-[#76b900] font-bold text-lg">
                            {formatParameterValue(key, value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Advanced Details - Collapsible */}
              {advancedParams.length > 0 && (
                <div>
                  <button
                    onClick={() => setShowAdvancedDetails(!showAdvancedDetails)}
                    className="flex items-center gap-2 text-gray-400 hover:text-[#76b900]/70 transition-all duration-150 ease-in-out mb-4 group"
                  >
                    <svg className={`w-4 h-4 transform transition-transform duration-150 ease-in-out ${showAdvancedDetails ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="text-sm font-medium uppercase tracking-wider">Advanced Details</span>
                  </button>
                  
                  <div className={`transition-all duration-150 ease-in-out overflow-hidden ${showAdvancedDetails ? 'opacity-100 max-h-[2000px]' : 'opacity-0 max-h-0'}`}>
                    <div className="bg-neutral-850/60 rounded-lg p-4 border border-neutral-700/60">
                      <div className="grid gap-4 md:grid-cols-2">
                        {advancedParams.map(([key, value], index) => (
                          <div
                            key={key}
                            className="group"
                          >
                            <div className="flex items-start gap-3 p-3 rounded-lg bg-neutral-800/60 border border-neutral-700/40 hover:border-[#76b900]/30 hover:bg-neutral-800/80 transition-all duration-200">
                              <div className="mt-0.5">
                                <ParameterIcon type={getIconType(key)} className="w-4 h-4 text-gray-500" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
                                    {getParameterLabel(key)}
                                  </span>
                                  {parameterDefinitions[key] && (
                                    <Tooltip content={parameterDefinitions[key]}>
                                      <svg className="w-3 h-3 text-gray-600 hover:text-gray-500 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                    </Tooltip>
                                  )}
                                </div>
                                <span className="text-sm font-medium text-gray-200 break-words">
                                  {formatParameterValue(key, value)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Notes/Recommendations */}
              {config.notes && config.notes.length > 0 && (
                <div className="mt-6 p-4 bg-amber-950/20 border border-amber-900/50 rounded-lg">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <h4 className="text-amber-300 font-medium text-sm mb-2">Recommendations</h4>
                      <ul className="space-y-1">
                        {config.notes.map((note, index) => (
                          <li key={index} className="text-amber-200/80 text-sm">• {note}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* No config warning */}
              {!isRelevantConfig && (
                <div className="mt-4 p-4 bg-yellow-950/20 border border-yellow-900/50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-yellow-300 text-sm">
                      No specific vGPU configuration was recommended for this query.
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
} 