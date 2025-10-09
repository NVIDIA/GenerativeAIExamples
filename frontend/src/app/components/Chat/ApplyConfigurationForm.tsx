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

import React, { useState, useEffect } from "react";

// Spinner component
const Spinner = () => (
  <div className="flex items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
  </div>
);

interface ApplyConfigurationFormProps {
  isOpen: boolean;
  onClose: () => void;
  configuration?: any; // vGPU configuration object to apply
}

interface FormData {
  vmIpAddress: string;
  username: string;
  password: string;
  huggingFaceToken: string;
}

interface FormErrors {
  vmIpAddress?: string;
  username?: string;
  password?: string;
  huggingFaceToken?: string;
}

export default function ApplyConfigurationForm({
  isOpen,
  onClose,
  configuration,
}: ApplyConfigurationFormProps) {
  const [formData, setFormData] = useState<FormData>({
    vmIpAddress: "",
    username: "",
    password: "",
    huggingFaceToken: "",
  });

  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showToken, setShowToken] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [configurationLogs, setConfigurationLogs] = useState<string[]>([]);
  const [isConfigurationComplete, setIsConfigurationComplete] = useState(false);
  const [showDebugLogs, setShowDebugLogs] = useState(false);
  const [currentDisplayMessage, setCurrentDisplayMessage] = useState<string>("");

  // Validate IP address format
  const validateIpAddress = (ip: string): boolean => {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
  };

  // Validate form fields
  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    if (!formData.vmIpAddress) {
      errors.vmIpAddress = "VM IP address is required";
    } else if (!validateIpAddress(formData.vmIpAddress)) {
      errors.vmIpAddress = "Invalid IP address format";
    }

    if (!formData.username) {
      errors.username = "Username is required";
    }

    if (!formData.password) {
      errors.password = "Password is required";
    }

    if (!formData.huggingFaceToken) {
      errors.huggingFaceToken = "Hugging Face token is required";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing (only for fields that exist in FormErrors)
    if (field in formErrors) {
      setFormErrors((prev) => ({ ...prev, [field as keyof FormErrors]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setShowLogs(false); // Hide logs initially
    setIsConfigurationComplete(false);
    setConfigurationLogs(["Starting configuration process..."]);
    setCurrentDisplayMessage(""); // Initialize with empty string

    try {
      // Extract and normalize the configuration data
      let configData = {};
      if (configuration && configuration.parameters) {
        // The configuration comes from the vGPU generation which has parameters field
        configData = configuration.parameters;
      } else if (configuration) {
        // Direct configuration object
        configData = configuration;
      }

      const response = await fetch("/api/apply-configuration", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          vm_ip: formData.vmIpAddress,
          username: formData.username,
          password: formData.password,
          configuration: configData,
          hf_token: formData.huggingFaceToken,
          description: configuration?.description || "vGPU configuration request from UI",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Read the streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          // Process complete lines
          const lines = buffer.split("\n");
          buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.substring(6));
                
                // Update display message if present
                if (data.display_message) {
                  setCurrentDisplayMessage(data.display_message);
                }
                
                // Update logs based on the progress
                if (data.message) {
                  // Split multi-line messages
                  const messages = data.message.split('\n');
                  for (const msg of messages) {
                    if (msg.trim()) {
                      // Strip any timestamps that might be present (format: [HH:MM:SS AM/PM])
                      const cleanMsg = msg.trim().replace(/^\[\d{1,2}:\d{2}:\d{2}\s*(AM|PM)?\]\s*/i, '');
                      setConfigurationLogs((prev) => [...prev, cleanMsg]);
                    }
                  }
                }

                // Handle command results
                if (data.command_results) {
                  for (const result of data.command_results) {
                    if (result.command) {
                      setConfigurationLogs((prev) => [
                        ...prev,
                        `$ ${result.command}`,
                      ]);
                      if (result.output) {
                        setConfigurationLogs((prev) => [
                          ...prev,
                          result.output.trim(),
                        ]);
                      }
                      if (result.error && !result.success) {
                        setConfigurationLogs((prev) => [
                          ...prev,
                          `Error: ${result.error}`,
                        ]);
                      }
                    }
                  }
                }

                // Check for completion or error
                if (data.status === "completed") {
                  // Don't add another success message, it's already in the logs
                  setIsConfigurationComplete(true);
                  setShowLogs(true); // Automatically show logs on completion
                  // Don't clear display message - let the last one persist
                } else if (data.status === "error") {
                  setConfigurationLogs((prev) => [
                    ...prev,
                    `❌ Error: ${data.error || "Configuration failed"}`,
                  ]);
                  setIsConfigurationComplete(true);
                  setShowLogs(true); // Automatically show logs on error
                  // Don't clear display message - let the last one persist
                }
              } catch (parseError) {
                console.error("Error parsing SSE data:", parseError);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Configuration error:", error);
      setConfigurationLogs((prev) => [
        ...prev,
        `❌ Error: ${error instanceof Error ? error.message : "Failed to apply configuration"}`,
      ]);
      setIsConfigurationComplete(true);
      setShowLogs(true); // Show logs on error
      // Don't clear display message here either
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    // Reset state but keep form data
    setIsConfigurationComplete(false);
    setConfigurationLogs([]);
    setShowLogs(false);
    setShowDebugLogs(false);
    setCurrentDisplayMessage("");
    // Form data is intentionally preserved
  };

  const handleClose = () => {
    // Reset form state
    setFormData({
      vmIpAddress: "",
      username: "",
      password: "",
      huggingFaceToken: "",
    });
    setFormErrors({});
    setShowPassword(false);
    setShowToken(false);
    setIsSubmitting(false);
    setShowLogs(false);
    setConfigurationLogs([]);
    setIsConfigurationComplete(false);
    setShowDebugLogs(false);
    setCurrentDisplayMessage("");
    onClose();
  };

  const handleExportLogs = () => {
    // Create log content without timestamps for cleaner export
    let logContent = configurationLogs.join('\n');
    
    // If debug logs are shown, add them to the export
    if (showDebugLogs) {
      const debugSection = "\n\n=== Debug Output ===\n" + 
        configurationLogs.filter(log => {
          if (log.includes("===") || log.startsWith("✓")) return false;
          const includePatterns = [
            "Starting configuration process",
            "Connecting to",
            "Connected successfully",
            "Gathering system information",
            "Hypervisor Layer",
            "Checking GPU availability",
            "GPU:",
            "Starting setup phase",
            "Authenticating with",
            "Setting up Python",
            "Installing",
            "Cleaned up",
            "Attempt",
            "server started",
            "Found",
            "GPU memory detected",
            "Post-launch cleanup",
            "SSH connection closed",
            "PID"
          ];
          return includePatterns.some(pattern => log.includes(pattern));
        }).join('\n');
      
      logContent += debugSection;
    }
    
    // Add header information
    const header = [
      '=== vGPU Configuration Logs ===',
      `Date: ${new Date().toLocaleString()}`,
      `VM IP: ${formData.vmIpAddress}`,
      `Username: ${formData.username}`,
      configuration?.parameters?.vGPU_profile ? `vGPU Profile: ${configuration.parameters.vGPU_profile}` : '',
      configuration?.parameters?.model_name ? `Model: ${configuration.parameters.model_name}` : '',
      '================================\n'
    ].filter(Boolean).join('\n');
    
    const fullContent = header + '\n' + logContent;
    
    // Create blob and download
    const blob = new Blob([fullContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vgpu_config_logs_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-neutral-900 rounded-lg border border-neutral-700 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-700">
          <div>
            <h2 className="text-xl font-semibold text-white">Apply Configuration</h2>
            <p className="text-sm text-gray-400 mt-1">
              Configure your VM with the recommended vGPU settings
            </p>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* VM IP Address */}
            <div>
              <label htmlFor="vmIpAddress" className="block text-sm font-medium text-gray-300 mb-2">
                VM IP Address
              </label>
              <input
                id="vmIpAddress"
                type="text"
                value={formData.vmIpAddress}
                onChange={(e) => handleInputChange("vmIpAddress", e.target.value)}
                placeholder="Enter the IP address of your Virtual Machine (VM)"
                className={`w-full p-3 rounded-lg bg-neutral-800 border ${
                  formErrors.vmIpAddress ? "border-red-500" : "border-neutral-600"
                } text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`}
              />
              {formErrors.vmIpAddress && (
                <p className="mt-1 text-sm text-red-500">{formErrors.vmIpAddress}</p>
              )}
            </div>

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => handleInputChange("username", e.target.value)}
                placeholder="Enter your VM username"
                className={`w-full p-3 rounded-lg bg-neutral-800 border ${
                  formErrors.username ? "border-red-500" : "border-neutral-600"
                } text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`}
              />
              {formErrors.username && (
                <p className="mt-1 text-sm text-red-500">{formErrors.username}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => handleInputChange("password", e.target.value)}
                  placeholder="Enter your VM password"
                  className={`w-full p-3 pr-12 rounded-lg bg-neutral-800 border ${
                    formErrors.password ? "border-red-500" : "border-neutral-600"
                  } text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {formErrors.password && (
                <p className="mt-1 text-sm text-red-500">{formErrors.password}</p>
              )}
            </div>

            {/* Hugging Face Token */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label htmlFor="huggingFaceToken" className="text-sm font-medium text-gray-300">
                  Hugging Face Token
                </label>
                <div className="group relative">
                  <svg className="h-4 w-4 text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-sm text-gray-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                    Used for model downloads from Hugging Face
                  </div>
                </div>
              </div>
              <div className="relative">
                <input
                  id="huggingFaceToken"
                  type={showToken ? "text" : "password"}
                  value={formData.huggingFaceToken}
                  onChange={(e) => handleInputChange("huggingFaceToken", e.target.value)}
                  placeholder="Enter your Hugging Face access token"
                  className={`w-full p-3 pr-12 rounded-lg bg-neutral-800 border ${
                    formErrors.huggingFaceToken ? "border-red-500" : "border-neutral-600"
                  } text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`}
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showToken ? (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {formErrors.huggingFaceToken && (
                <p className="mt-1 text-sm text-red-500">{formErrors.huggingFaceToken}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
                isSubmitting
                  ? "bg-neutral-700 text-gray-400 cursor-not-allowed"
                  : "bg-green-600 text-white hover:bg-green-700"
              }`}
            >
              {isSubmitting 
                ? "Applying Configuration..." 
                : isConfigurationComplete
                ? "Apply Configuration Again"
                : "Apply Configuration"}
            </button>

            {/* Retry Button - Show after completion */}
            {isConfigurationComplete && (
              <div className="mt-4 flex gap-3">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="flex-1 py-3 px-4 rounded-lg font-medium bg-neutral-700 text-white hover:bg-neutral-600 transition-all"
                >
                  Clear Logs & Retry
                </button>
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 py-3 px-4 rounded-lg font-medium bg-neutral-800 text-gray-300 hover:bg-neutral-700 transition-all"
                >
                  Close
                </button>
              </div>
            )}
          </form>

          {/* Configuration Status */}
          {isSubmitting && (
            <div className="mt-6 border-t border-neutral-700 pt-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-white mb-4">Applying Configuration</h3>
                <Spinner />
                <p className="text-sm text-gray-400 mt-4">
                  Please wait while we configure your VM...
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  This process typically takes 1-3 minutes
                </p>
                {currentDisplayMessage && (
                  <div className="mt-4 p-3 bg-neutral-800 rounded-lg border border-neutral-600">
                    <p className="text-sm text-green-400 font-medium animate-pulse">
                      {currentDisplayMessage}
                    </p>
                  </div>
                )}
                {configurationLogs.length > 0 && !currentDisplayMessage && (
                  <p className="text-xs text-gray-400 mt-3 italic">
                    {configurationLogs[configurationLogs.length - 1]}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Configuration Logs - Only show after completion */}
          {!isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && (
            <div className="mt-6 border-t border-neutral-700 pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">Configuration Logs</h3>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleExportLogs}
                    className="px-3 py-1 text-sm bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg transition-colors flex items-center gap-2"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Export Logs
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowLogs(!showLogs)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    {showLogs ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
              
              {showLogs && (
                <div className="bg-black rounded-lg border border-neutral-700 p-4 max-h-64 overflow-y-auto">
                  <div className="space-y-1 font-mono text-sm">
                    {(() => {
                      // Separate logs into categories
                      const summaryLogs: string[] = [];
                      const stepsLogs: string[] = [];
                      const otherLogs: string[] = [];
                      let inSummary = false;
                      let inSteps = false;
                      
                      configurationLogs.forEach((log) => {
                        if (log.includes("=== Configuration Summary ===")) {
                          inSummary = true;
                          inSteps = false;
                          summaryLogs.push(log);
                        } else if (log.includes("=== Steps Completed ===")) {
                          inSummary = false;
                          inSteps = true;
                          stepsLogs.push(log);
                        } else if (inSummary) {
                          summaryLogs.push(log);
                        } else if (inSteps) {
                          stepsLogs.push(log);
                        } else {
                          // Filter out redundant messages
                          const skipMessages = [
                            "✅ Configuration applied successfully!",
                            "Configuration applied successfully.",
                            "PID .* no GPU usage entry found"  // Skip PID messages that show no GPU usage
                          ];
                          
                          const shouldSkip = skipMessages.some(pattern => {
                            if (pattern.includes(".*")) {
                              return new RegExp(pattern).test(log);
                            }
                            return log === pattern;
                          });
                          
                          if (!shouldSkip) {
                            otherLogs.push(log);
                          }
                        }
                      });
                      
                      // Display summary first, then other logs, then steps
                      const orderedLogs = [...summaryLogs, ...otherLogs, ...stepsLogs];
                      
                      // Filter out debug messages from main configuration logs
                      const debugPatterns = [
                        "Starting configuration process",
                        "Connecting to",
                        "Connected successfully",
                        "Gathering system information",
                        "Hypervisor Layer",
                        "Checking GPU availability",
                        "GPU:",
                        "Starting setup phase",
                        "Authenticating with",
                        "Setting up Python",
                        "Installing",
                        "Cleaned up",
                        "Attempt",
                        "server started",
                        "Found",
                        "GPU memory detected",
                        "Post-launch cleanup",
                        "SSH connection closed"
                      ];
                      
                      const filteredLogs = orderedLogs.filter(log => {
                        // Keep summary and steps
                        if (summaryLogs.includes(log) || stepsLogs.includes(log)) {
                          return true;
                        }
                        // Exclude debug messages
                        return !debugPatterns.some(pattern => log.includes(pattern));
                      });
                      
                      return filteredLogs.map((log, index) => {
                        const isSummaryHeader = log.includes("=== Configuration Summary ===") || log.includes("=== Steps Completed ===");
                        const isStepItem = log.startsWith("✓");
                        const isSummaryItem = summaryLogs.includes(log) && !isSummaryHeader;
                        
                        return (
                          <div 
                            key={index} 
                            className={`
                              text-gray-300 
                              ${isSummaryHeader ? 'font-bold text-green-400 mt-3 mb-1' : ''} 
                              ${isStepItem ? 'ml-4 text-green-300' : ''}
                              ${isSummaryItem ? 'ml-4' : ''}
                            `}
                          >
                            {log}
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Debug Output - Show detailed intermediate steps */}
          {!isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">Debug Output</h3>
                <button
                  type="button"
                  onClick={() => setShowDebugLogs(!showDebugLogs)}
                  className="text-gray-400 hover:text-white transition-colors flex items-center gap-2"
                >
                  <span className="text-sm">Show detailed steps</span>
                  {showDebugLogs ? (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>
              </div>
              
              {showDebugLogs && (
                <div className="bg-black rounded-lg border border-neutral-700 p-4 max-h-64 overflow-y-auto">
                  <div className="space-y-1 font-mono text-xs">
                    {(() => {
                      // Filter logs to show only intermediate/debug steps
                      const debugLogs = configurationLogs.filter(log => {
                        // Exclude summary sections
                        if (log.includes("===") || log.startsWith("✓")) return false;
                        
                        // Include these types of messages
                        const includePatterns = [
                          "Starting configuration process",
                          "Connecting to",
                          "Connected successfully",
                          "Gathering system information",
                          "Hypervisor Layer",
                          "Checking GPU availability",
                          "GPU:",
                          "Starting setup phase",
                          "Authenticating with",
                          "Setting up Python",
                          "Installing",
                          "Cleaned up",
                          "Attempt",
                          "server started",
                          "Found",
                          "GPU memory detected",
                          "Post-launch cleanup",
                          "SSH connection closed",
                          "PID"
                        ];
                        
                        return includePatterns.some(pattern => log.includes(pattern));
                      });
                      
                      return debugLogs.map((log, index) => {
                        // Color code different types of messages
                        let className = "text-gray-400";
                        
                        if (log.includes("Error") || log.includes("failed")) {
                          className = "text-red-400";
                        } else if (log.includes("successfully") || log.includes("✓")) {
                          className = "text-green-400";
                        } else if (log.includes("Attempt") || log.includes("GPU memory")) {
                          className = "text-yellow-400";
                        } else if (log.includes("Connecting") || log.includes("Starting")) {
                          className = "text-blue-400";
                        }
                        
                        return (
                          <div key={index} className={className}>
                            <span className="text-gray-600">$</span> {log}
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 