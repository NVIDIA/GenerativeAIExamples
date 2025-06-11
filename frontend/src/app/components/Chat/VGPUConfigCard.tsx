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

import { useState } from "react";

interface VGPUConfig {
  title: string;
  description: string;
  parameters: {
    vGPU_profile?: string | null;
    total_CPUs?: number | null;
    vCPU_count?: number | null;
    gpu_memory_size?: number | null;
    video_card_total_memory?: number | null;
    system_RAM?: number | null;
    storage_capacity?: number | null;
    storage_type?: string | null;
    driver_version?: string | null;
    AI_framework?: string | null;
    performance_tier?: string | null;
    concurrent_users?: number | null;
    // Legacy fields for backward compatibility
    relevant_aiwb_toolkit?: string | null;
    RAM?: number | null;
  };
}

interface VGPUConfigCardProps {
  config: VGPUConfig;
}

export default function VGPUConfigCard({ config }: VGPUConfigCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
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

  const formatParameterName = (key: string): string => {
    return key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
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
      case 'vGPU_profile':
        return value;
      case 'total_CPUs':
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

  const getParameterIcon = (key: string): string => {
    switch (key) {
      case 'vGPU_profile':
        return '🖥️';
      case 'total_CPUs':
        return '🏗️';
      case 'vCPU_count':
        return '⚡';
      case 'gpu_memory_size':
        return '🎮';
      case 'video_card_total_memory':
        return '💾';
      case 'system_RAM':
      case 'RAM':
        return '💻';
      case 'storage_capacity':
        return '💿';
      case 'storage_type':
        return '🗄️';
      case 'driver_version':
        return '🔧';
      case 'AI_framework':
      case 'relevant_aiwb_toolkit':
        return '🤖';
      case 'performance_tier':
        return '🚀';
      case 'concurrent_users':
        return '👥';
      default:
        return '⚙️';
    }
  };

  const getParameterLabel = (key: string): string => {
    switch (key) {
      case 'vGPU_profile':
        return 'vGPU Profile';
      case 'total_CPUs':
        return 'Total CPUs';
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
        return formatParameterName(key);
    }
  };

  const isRelevantConfig = Object.values(config.parameters).some(value => value !== null && value !== undefined);

  return (
    <div className="bg-neutral-900 border border-neutral-700 rounded-lg overflow-hidden shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🖥️</span>
            <h3 className="text-lg font-semibold">vGPU Configuration Recommendation</h3>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowRawJSON(!showRawJSON)}
              className="p-1 hover:bg-green-600 rounded transition-colors"
              title="Toggle Raw JSON"
            >
              <span className="text-sm">{ showRawJSON ? '📊' : '🔧' }</span>
            </button>
            <button
              onClick={handleCopy}
              className="p-1 hover:bg-green-600 rounded transition-colors"
              title="Copy JSON"
            >
              <span className="text-sm">📋</span>
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-green-600 rounded transition-colors"
            >
              <span className="text-sm">{isExpanded ? '🔼' : '🔽'}</span>
            </button>
          </div>
        </div>
        {copied && (
          <div className="mt-2 text-sm text-green-100">
            ✅ Copied to clipboard!
          </div>
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-4">
          {/* Description */}
          <div className="mb-4">
            <p className="text-gray-300 text-sm leading-relaxed">
              {config.description}
            </p>
          </div>

          {showRawJSON ? (
            /* Raw JSON View */
            <div className="bg-black rounded-lg p-3 overflow-x-auto">
              <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                {JSON.stringify(config, null, 2)}
              </pre>
            </div>
          ) : (
            /* Structured Configuration View */
            <div className="space-y-3">
              <h4 className="text-white font-medium text-sm mb-3">
                Configuration Details:
              </h4>
              <div className="grid gap-3">
                {Object.entries(config.parameters).map(([key, value]) => {
                  const isSpecified = value !== null && value !== undefined;
                  return (
                    <div
                      key={key}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        isSpecified
                          ? isRelevantConfig
                            ? 'bg-green-900/20 border-green-700 text-white'
                            : 'bg-neutral-800 border-neutral-700 text-white'
                          : 'bg-neutral-800 border-neutral-700 text-gray-400'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{getParameterIcon(key)}</span>
                        <span className="font-medium text-sm">
                          {getParameterLabel(key)}:
                        </span>
                      </div>
                      <span className={`text-sm font-mono ${
                        isSpecified 
                          ? isRelevantConfig 
                            ? 'text-green-300 font-semibold' 
                            : 'text-white font-semibold'
                          : 'text-gray-500'
                      }`}>
                        {formatParameterValue(key, value)}
                      </span>
                    </div>
                  );
                })}
              </div>

              {!isRelevantConfig && (
                <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <span className="text-yellow-400">⚠️</span>
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