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
  huggingFaceToken: string;
}

interface FormErrors {
  huggingFaceToken?: string;
}

export default function ApplyConfigurationForm({
  isOpen,
  onClose,
  configuration,
}: ApplyConfigurationFormProps) {
  const [formData, setFormData] = useState<FormData>({
    huggingFaceToken: "",
  });

  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [showToken, setShowToken] = useState(false);
  
  // Single deployment state (always local)
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [configurationLogs, setConfigurationLogs] = useState<string[]>([]);
  const [isConfigurationComplete, setIsConfigurationComplete] = useState(false);
  const [showDebugLogs, setShowDebugLogs] = useState(false);
  const [currentDisplayMessage, setCurrentDisplayMessage] = useState("");
  const [testMetrics, setTestMetrics] = useState<any>(null);
  const [deploymentError, setDeploymentError] = useState<string | null>(null);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [copiedResults, setCopiedResults] = useState(false);
  const [copiedLogs, setCopiedLogs] = useState(false);
  const [showGpuMismatchWarning, setShowGpuMismatchWarning] = useState(false);
  const [gpuMismatchDetails, setGpuMismatchDetails] = useState<{
    systemGpu: string;
    recommendedGpu: string;
  } | null>(null);
  const [isCheckingGpu, setIsCheckingGpu] = useState(false);

  // Extract GPU model from vGPU profile (e.g., "BSE-24Q" -> "BSE", "L40S-12Q" -> "L40S")
  const extractGpuFromProfile = (profile: string): string | null => {
    if (!profile) return null;
    
    // Match known GPU patterns (order matters - check longer patterns first)
    const gpuPatterns = [
      { pattern: /^BSE-/i, name: "BSE" },
      { pattern: /^DC-/i, name: "BSE" }, // DC profiles are Blackwell Server Edition
      { pattern: /^L40S-/i, name: "L40S" },
      { pattern: /^L40-/i, name: "L40" },
      { pattern: /^L4-/i, name: "L4" },
      { pattern: /^A100-/i, name: "A100" },
      { pattern: /^A40-/i, name: "A40" },
      { pattern: /^A10-/i, name: "A10" },
      { pattern: /^H100-/i, name: "H100" },
      { pattern: /^RTX6000-/i, name: "RTX6000" },
    ];
    
    for (const { pattern, name } of gpuPatterns) {
      if (pattern.test(profile)) {
        return name;
      }
    }
    
    // Fallback: extract prefix before dash
    const match = profile.match(/^([^-]+)-/);
    return match ? match[1] : null;
  };

  // Detect system GPU
  const detectSystemGpu = async (): Promise<string | null> => {
    try {
      const response = await fetch('/api/detect-gpu');
      if (response.ok) {
        const data = await response.json();
        return data.gpu_model || null;
      }
    } catch (error) {
      console.error('Failed to detect system GPU:', error);
    }
    return null;
  };

  // Extract core GPU model from full GPU name
  const extractCoreGpuModel = (gpuName: string): string => {
    const name = gpuName.toUpperCase();
    
    // Map full names to short codes (matches backend logic)
    if (name.includes('BLACKWELL') || name.includes('BSE')) {
      return 'BSE';
    }
    if (name.includes('L40S')) {
      return 'L40S';
    }
    if (name.includes('L40') && !name.includes('L40S')) {
      return 'L40';
    }
    if (name.includes('L4') && !name.includes('L40')) {
      return 'L4';
    }
    if (name.includes('A40')) {
      return 'A40';
    }
    if (name.includes('A100')) {
      return 'A100';
    }
    if (name.includes('H100')) {
      return 'H100';
    }
    if (name.includes('A10')) {
      return 'A10';
    }
    
    // Fallback: return first meaningful token
    const tokens = name.split(/[\s\-_]+/).filter(t => t.length > 1);
    return tokens[0] || name;
  };

  // Validate form fields
  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    // Only require Hugging Face token for local deployment
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

    // Check for GPU mismatch BEFORE validating HF token
    setIsCheckingGpu(true);
    try {
      // Extract recommended GPU from configuration
      const vgpuProfile = configuration?.parameters?.vgpu_profile || 
                          configuration?.parameters?.vGPU_profile ||
                          configuration?.vgpu_profile ||
                          configuration?.vGPU_profile;
      
      const recommendedGpu = extractGpuFromProfile(vgpuProfile);
      const systemGpuFull = await detectSystemGpu();
      
      // Only check if both GPUs are detected and they don't match
      if (systemGpuFull && recommendedGpu) {
        const systemGpuCore = extractCoreGpuModel(systemGpuFull);
        const recommendedGpuCore = recommendedGpu.toUpperCase();
        
        console.log(`GPU Check: System="${systemGpuCore}" vs Recommended="${recommendedGpuCore}"`);
        
        if (systemGpuCore !== recommendedGpuCore) {
          setGpuMismatchDetails({
            systemGpu: systemGpuFull,
            recommendedGpu: recommendedGpu,
          });
          setShowGpuMismatchWarning(true);
          setIsCheckingGpu(false);
          return; // Stop here and wait for user decision
        }
      }
    } catch (error) {
      console.error('GPU detection error:', error);
      // Continue anyway if detection fails
    }
    setIsCheckingGpu(false);

    // Proceed with deployment
    proceedWithDeployment();
  };

  const proceedWithDeployment = async () => {
    // Reset state for new deployment
    setIsSubmitting(true);
    setShowLogs(false);
    setIsConfigurationComplete(false);
    setTestMetrics(null);
    setConfigurationLogs(["Starting local vLLM deployment..."]);
    setCurrentDisplayMessage("");
    setDeploymentError(null);
    setShowGpuMismatchWarning(false); // Close warning if open

    try {
      // Extract and normalize the configuration data
      let configData: any = {};
      if (configuration && configuration.parameters) {
        // The configuration comes from the vGPU generation which has parameters field
        configData = configuration.parameters;
      } else if (configuration) {
        // Direct configuration object
        configData = configuration;
      } else {
        // Provide a minimal default configuration for testing
        configData = {
          vGPU_profile: "test",
          model_name: "test-model"
        };
      }

      // Build payload based on deployment mode
      // Extract model from configuration (could be model_tag, model_name, or in parameters)
      const model = configData?.model_tag || 
                   configData?.model_name || 
                   configData?.parameters?.model_tag ||
                   configData?.parameters?.model_name ||
                   'Qwen/Qwen2.5-0.5B-Instruct';  // Default to an open-access model
      
      // Store the model for display in loading message
      setCurrentModel(model);
      
      // Always deploy locally
      const payload: any = {
        deployment_mode: 'local',
        hf_token: formData.huggingFaceToken,
        configuration: configData,
        model_tag: model,
      };
      
      const response = await fetch('/api/apply-configuration', {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        // Try to get the error details from the response
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
          const responseText = await response.text();
          console.error("Backend error response body:", responseText);
          
          try {
            const errorData = JSON.parse(responseText);
            console.error("Backend error JSON:", errorData);
            if (errorData.detail) {
              if (Array.isArray(errorData.detail)) {
                // Pydantic validation errors are arrays
                const errors = errorData.detail.map((e: any) => 
                  `${e.loc?.join('.')} - ${e.msg}`
                ).join('; ');
                errorDetail += ` - Validation errors: ${errors}`;
              } else {
                errorDetail += ` - ${JSON.stringify(errorData.detail)}`;
              }
            }
          } catch (parseError) {
            // Not JSON, just use the text
            errorDetail += ` - ${responseText}`;
          }
        } catch (e) {
          console.error("Error reading response:", e);
          // If we can't parse the error, just use the status
        }
        console.error("Final error message:", errorDetail);
        throw new Error(errorDetail);
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
                
                // Handle test metrics
                if (data.metrics) {
                  setTestMetrics(data.metrics);
                  setShowLogs(true); // Show logs when metrics arrive
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
                if (data.status === "completed" || data.status === "success") {
                  // Don't add another success message, it's already in the logs
                  setIsConfigurationComplete(true);
                  setDeploymentError(null); // Clear any previous errors
                  setShowLogs(true); // Automatically show logs on completion
                  // Don't clear display message - let the last one persist
                } else if (data.status === "error") {
                  const errorMsg = data.error || "Configuration test failed";
                  setConfigurationLogs((prev) => [
                    ...prev,
                    `❌ Error: ${errorMsg}`,
                  ]);
                  setDeploymentError(errorMsg);
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
      let errorMsg = "Failed to apply configuration";
      
      // Check if it's a network error (backend not responding)
      if (error instanceof TypeError && error.message.includes('fetch')) {
        errorMsg = "Backend is not responding or is not running. Please ensure the backend server is started.";
      } else if (error instanceof Error) {
        errorMsg = error.message;
      }
      
      setConfigurationLogs((prev) => [
        ...prev,
        `❌ Error: ${errorMsg}`,
      ]);
      setDeploymentError(errorMsg);
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
    setDeploymentError(null);
    setTestMetrics(null);
    setShowLogs(false);
    setShowDebugLogs(false);
    setCurrentDisplayMessage("");
    setCopiedResults(false);
    setCopiedLogs(false);
    // Form data is intentionally preserved
  };

  const handleClose = async () => {
    // Reset form state
    setFormData({
      huggingFaceToken: "",
    });
    setFormErrors({});
    setShowToken(false);
    
    // Reset deployment state
    setIsSubmitting(false);
    setShowLogs(false);
    setConfigurationLogs([]);
    setIsConfigurationComplete(false);
    setShowDebugLogs(false);
    setCurrentDisplayMessage("");
    setTestMetrics(null);
    setDeploymentError(null);
    setCopiedResults(false);
    setCopiedLogs(false);
    
    onClose();
  };

  // Helper function to copy text to clipboard with fallback
  const copyToClipboard = async (text: string) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers or non-HTTPS
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
          document.execCommand('copy');
        } finally {
          document.body.removeChild(textArea);
        }
      }
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy to clipboard');
    }
  };

  // Helper function to get formatted deployment results
  const getDeploymentResultsText = () => {
    const results: string[] = [];
    let capturing = false;
    let hasResultsMarker = false;
    
    // First check if there's a DEPLOYMENT RESULTS marker
    for (const log of configurationLogs) {
      if (log.includes("=== DEPLOYMENT RESULTS ===")) {
        hasResultsMarker = true;
        break;
      }
    }
    
    // If there's no results marker, capture error messages
    if (!hasResultsMarker) {
      for (const log of configurationLogs) {
        // Capture error messages and important status info
        if (log.includes("❌ Error:") || 
            log.includes("Error:") ||
            log.includes("failed") ||
            log.includes("Failed") ||
            log.includes("Container exited") ||
            log.includes("Permission denied") ||
            log.includes("Connection refused")) {
          results.push(log);
        }
      }
      return results;
    }
    
    // Otherwise, capture logs between the markers
    for (const log of configurationLogs) {
      // Start capturing after "=== DEPLOYMENT RESULTS ==="
      if (log.includes("=== DEPLOYMENT RESULTS ===")) {
        capturing = true;
        continue; // Skip the header itself
      }
      
      // Stop capturing when we hit deployment logs
      if (log.includes("=== DEPLOYMENT LOG ===")) {
        break;
      }
      
      // Only capture if we're in the results section
      if (capturing) {
        results.push(log);
      }
    }
    
    return results;
  };

  // Helper function to get debug logs
  const getDebugLogsText = () => {
    const results: string[] = [];
    let capturing = false;
    
    for (const log of configurationLogs) {
      // Start capturing after "=== DEPLOYMENT LOG ==="
      if (log.includes("=== DEPLOYMENT LOG ===")) {
        capturing = true;
        continue; // Don't include the header itself
      }
      
      // Capture everything after the deployment log marker
      if (capturing && log.trim() !== "") {
        results.push(log);
      }
    }
    
    return results;
  };

  const handleExportLogs = () => {
    // Get deployment results
    const deploymentResults = getDeploymentResultsText();
    const debugLogs = getDebugLogsText();
    
    // Add header information for local deployment
    const header = [
      '=== vLLM Deployment Export ===',
      `Date: ${new Date().toLocaleString()}`,
      `Mode: Local Docker Deployment`,
      '================================\n'
    ].join('\n');
    
    // Build content
    let fullContent = header + '\n';
    
    // Add deployment results
    fullContent += '\n=== DEPLOYMENT RESULTS ===\n\n';
    if (deploymentError || deploymentResults.some(r => r.includes("Error:") || r.includes("failed"))) {
      fullContent += `Status: Deployment Failed\n\n`;
      if (deploymentError) {
        fullContent += `${deploymentError}\n\n`;
      }
      if (deploymentResults.length > 0) {
        fullContent += deploymentResults.join('\n');
        fullContent += '\n';
      }
    } else if (deploymentResults.length > 0) {
      fullContent += deploymentResults.join('\n');
      fullContent += '\n';
    } else {
      fullContent += 'No results available\n\n';
    }
    
    // Add debug logs if they exist
    if (debugLogs.length > 0) {
      fullContent += '\n\n=== DEPLOYMENT LOG ===\n\n';
      fullContent += debugLogs.join('\n');
      fullContent += '\n';
    }
    
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
        <div className="p-6 border-b border-neutral-700">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Apply Configuration</h2>
              <p className="text-sm text-gray-400 mt-1">
                Deploy vLLM locally using Docker with your recommended configuration
              </p>
            </div>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-neutral-800 rounded transition-colors group"
              title="Close"
            >
              <svg className="w-5 h-5 text-gray-400 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Hugging Face Token */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <label htmlFor="huggingFaceToken" className="text-sm font-medium text-gray-300">
                  Hugging Face Token
                </label>
              </div>
              <div className="mb-2 flex items-start gap-2 text-xs text-gray-400">
                <svg className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="leading-relaxed">
                    Used for model downloads. Ensure you have access to gated models.{' '}
                    <a
                      href="https://huggingface.co/settings/tokens"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-400 hover:text-green-300 underline inline-flex items-center gap-0.5"
                    >
                      Create token
                      <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </p>
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
              disabled={isSubmitting || isCheckingGpu}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
                isSubmitting || isCheckingGpu
                  ? "bg-neutral-700 text-gray-400 cursor-not-allowed"
                  : "bg-green-600 text-white hover:bg-green-700"
              }`}
            >
              {isCheckingGpu
                ? "Checking GPU compatibility..."
                : isSubmitting 
                ? "Deploying..." 
                : isConfigurationComplete
                ? "Apply Configuration Again"
                : "Apply Configuration"}
            </button>
          </form>

          {/* Configuration Status */}
          {isSubmitting && (
            <div className="mt-6 border-t border-neutral-700 pt-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-white mb-4">
                  Deploying vLLM Locally
                </h3>
                <Spinner />
                <p className="text-sm text-gray-400 mt-4">
                  Setting up vLLM container running{' '}
                  {currentModel && (
                    <a
                      href={`https://huggingface.co/${currentModel}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-400 hover:text-green-300 underline"
                    >
                      {currentModel}
                    </a>
                  )}
                  {!currentModel && <span className="text-green-400">model</span>}
                  {' '}on this machine
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

          {/* Deployment Summary - Performance Info */}
          {!isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && (
            <div className="mt-6 border-t border-neutral-700 pt-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  {deploymentError || configurationLogs.some(log => 
                    log.includes('failed') || 
                    log.includes('Error:') || 
                    log.includes('Permission denied') ||
                    log.includes('Connection refused')
                  ) ? (
                    <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  <h3 className="text-lg font-semibold text-white">
                    {deploymentError || configurationLogs.some(log => 
                      log.includes('failed') || 
                      log.includes('Error:') || 
                      log.includes('Permission denied') ||
                      log.includes('Connection refused')
                    ) ? 'Deployment Failed' : 'Deployment Results'}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleExportLogs}
                    className="px-3 py-1.5 text-sm bg-neutral-700 hover:bg-neutral-600 text-white rounded-md transition-colors flex items-center gap-2 font-medium"
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
                    title={showLogs ? "Collapse results" : "Expand results"}
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
                <div className="relative bg-neutral-900 rounded-lg border border-neutral-700">
                  <div className="p-8 max-h-96 overflow-y-auto custom-scrollbar">
                    {/* Error Display */}
                    {(deploymentError || configurationLogs.some(log => 
                      log.includes('failed') || 
                      log.includes('Error:') || 
                      log.includes('Permission denied') ||
                      log.includes('Connection refused')
                    )) && (
                      <div className="mb-6 p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
                        <div className="flex items-start gap-3">
                          <svg className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div className="flex-1">
                            <h4 className="text-red-400 font-semibold mb-2">Deployment Error</h4>
                            <p className="text-red-300 text-sm">
                              {deploymentError || 
                                configurationLogs.find(log => 
                                  log.includes('Error:') || 
                                  log.includes('failed') ||
                                  log.includes('Permission denied') ||
                                  log.includes('Connection refused')
                                )?.replace(/^[❌$]\s*/, '') || 
                                'Deployment failed. Check the debug output for details.'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                    {(() => {
                      // Get filtered deployment results
                      const resultLogs = getDeploymentResultsText();
                      
                      // Filter out empty lines for display
                      const displayLogs = resultLogs.filter(log => log.trim() !== "");
                      
                      return (
                        <div className="space-y-1">
                          {displayLogs.map((log, logIndex) => {
                            // Determine log styling based on content
                            let className = "text-gray-300 text-sm leading-relaxed break-words";
                            
                            // Status line (e.g., "Status: Deployment Successful") - larger and more prominent
                            if (log.includes("Status:")) {
                              className = "text-emerald-500 font-bold text-lg mt-6 mb-3 break-words tracking-wide text-center";
                            }
                            // Subsection headers (Workload details, System details, etc.)
                            else if (log.trim().endsWith(":") && !log.startsWith("•")) {
                              className = "text-emerald-400 font-bold text-base mt-5 mb-2 break-words tracking-wide";
                            }
                            // Bullet points - enhanced with better color and spacing
                            else if (log.startsWith("•")) {
                              // Check for special indicators within bullet points
                              if (log.includes("matches recommended profile") || log.includes("within expected range") || log.includes("Actual usage vs expected")) {
                                className = "text-white font-medium text-sm ml-6 break-words leading-relaxed";
                              } else if (log.includes("does not match") || log.includes("outside expected") || log.includes("GPU does not match")) {
                                className = "text-red-300 font-medium text-sm ml-6 break-words leading-relaxed";
                              } else {
                                className = "text-gray-100 font-normal text-sm ml-6 break-words leading-relaxed";
                              }
                            }
                            // Success indicators
                            else if (log.includes("Yes!") || log.includes("Match: Yes")) {
                              className = "text-green-400 font-semibold ml-4 break-words";
                            }
                            // Error/incompatible indicators  
                            else if (log.includes("Match: No") || log.includes("Outside expected")) {
                              className = "text-red-400 font-semibold ml-4 break-words";
                            }
                            // Comparison data
                            else if (log.includes("Expected") || log.includes("Actual") || log.includes("Difference")) {
                              className = "text-emerald-300 ml-4 break-words";
                            }
                            // Errors
                            else if (log.includes("Error") && !log.includes("Expected")) {
                              className = "text-red-400 font-semibold break-words";
                            }
                    
                            return (
                              <div key={logIndex} className={className}>
                                {log}
                              </div>
                            );
                          })}
                        </div>
                      );
                    })()}
                  </div>
                  {/* Copy button and message - fixed at bottom */}
                  <div className="relative p-3 bg-neutral-900">
                    {copiedResults && (
                      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2 text-green-400 text-xs bg-neutral-800/90 px-3 py-1.5 rounded border border-green-500/30">
                        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Copied to clipboard
                      </div>
                    )}
                    <button
                      onClick={async () => {
                        const deploymentResults = getDeploymentResultsText();
                        const text = `Deployment Results\n${"=".repeat(18)}\n${deploymentResults.join("\n")}`;
                        await copyToClipboard(text);
                        setCopiedResults(true);
                        setTimeout(() => setCopiedResults(false), 2000);
                      }}
                      className="absolute bottom-3 right-3 p-2 bg-neutral-800 hover:bg-neutral-700 rounded transition-colors border border-neutral-600 text-gray-400 hover:text-gray-200"
                      title="Copy deployment results"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Deployment Logs - Execution Steps */}
          {!isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <h3 className="text-sm font-medium text-gray-300">Deployment Logs</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setShowDebugLogs(!showDebugLogs)}
                  className="text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-2"
                >
                  <span className="text-xs">Show execution steps</span>
                  {showDebugLogs ? (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </button>
              </div>
              
              {showDebugLogs && (
                <div className="relative bg-black rounded-lg border border-neutral-800">
                  <div className="p-4 max-h-80 overflow-y-auto">
                    <div className="space-y-1 font-mono text-xs">
                    {(() => {
                          // Get filtered debug logs
                          const debugLogs = getDebugLogsText();
                      
                      return debugLogs.map((log, index) => {
                        // Color code different types of messages
                        let className = "text-gray-400";
                            let prefix = "$";
                        
                        if (log.includes("Error") || log.includes("failed")) {
                          className = "text-red-400";
                              prefix = "$";
                            } else if (log.includes("Inference response:")) {
                              className = "text-purple-400";
                              prefix = "→";
                            } else if (log.includes("successful") || log.includes("ready") || log.includes("detected")) {
                          className = "text-green-400";
                              prefix = "$";
                            } else if (log.includes("Waiting") || log.includes("Starting")) {
                          className = "text-blue-400";
                              prefix = "$";
                            } else if (log.includes("Checking") || log.includes("Testing")) {
                              className = "text-cyan-400";
                              prefix = "$";
                        }
                        
                        return (
                              <div key={index} className={`${className} flex gap-2`}>
                                <span className="text-gray-600 select-none">{prefix}</span>
                                <span className="break-words">{log}</span>
                          </div>
                        );
                      });
                    })()}
                    </div>
                  </div>
                  {/* Copy button and message - fixed at bottom */}
                  <div className="relative p-3 bg-black">
                    {copiedLogs && (
                      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2 text-green-400 text-xs font-mono bg-neutral-800/90 px-3 py-1.5 rounded border border-green-500/30">
                        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Copied to clipboard
                      </div>
                    )}
                    <button
                      onClick={async () => {
                        const debugLogs = getDebugLogsText();
                        const text = `Deployment Logs\n${"=".repeat(16)}\n${debugLogs.join("\n")}`;
                        await copyToClipboard(text);
                        setCopiedLogs(true);
                        setTimeout(() => setCopiedLogs(false), 2000);
                      }}
                      className="absolute bottom-3 right-3 p-2 bg-neutral-800 hover:bg-neutral-700 rounded transition-colors border border-neutral-600 text-gray-400 hover:text-gray-200"
                      title="Copy deployment logs"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* GPU Mismatch Warning Modal */}
      {showGpuMismatchWarning && gpuMismatchDetails && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
          <div className="bg-neutral-900 border border-yellow-500/50 rounded-xl shadow-2xl max-w-lg w-full animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="bg-gradient-to-r from-yellow-600/20 to-orange-600/20 border-b border-yellow-500/30 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-500/20 rounded-lg">
                  <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-yellow-500">GPU Mismatch Detected</h3>
                  <p className="text-sm text-gray-400">System GPU does not match recommendation</p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-5 space-y-4">
              <div className="space-y-3 text-gray-300">
                <p className="leading-relaxed">
                  The GPU on your system <span className="font-semibold text-white">does not match</span> the recommended GPU for this configuration.
                </p>
                
                <div className="bg-neutral-800/50 border border-neutral-700 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-400">System GPU:</span>
                    <span className="text-base font-bold text-red-400">{gpuMismatchDetails.systemGpu}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-400">Recommended GPU:</span>
                    <span className="text-base font-bold text-green-400">{gpuMismatchDetails.recommendedGpu}</span>
                  </div>
                </div>

                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4 space-y-2">
                  <p className="text-sm font-medium text-yellow-400">⚠️ Warning</p>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    Deploying this configuration on a different GPU than recommended may result in:
                  </p>
                  <ul className="text-sm text-gray-400 leading-relaxed list-disc list-inside space-y-1 ml-2">
                    <li>Incorrect memory sizing and performance issues</li>
                    <li>Deployment failures or out-of-memory errors</li>
                    <li>Suboptimal performance characteristics</li>
                    <li>Inaccurate test results and metrics</li>
                  </ul>
                </div>

                <p className="text-sm text-gray-400">
                  It is strongly recommended to deploy this configuration on a system with the <span className="font-medium text-white">{gpuMismatchDetails.recommendedGpu}</span> GPU or generate a new configuration for your <span className="font-medium text-white">{gpuMismatchDetails.systemGpu}</span> GPU.
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-neutral-800/50 border-t border-neutral-700 flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
              <button
                onClick={() => {
                  setShowGpuMismatchWarning(false);
                  setGpuMismatchDetails(null);
                }}
                className="px-6 py-2.5 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Cancel Deployment
              </button>
              <button
                onClick={() => {
                  setShowGpuMismatchWarning(false);
                  proceedWithDeployment();
                }}
                className="px-6 py-2.5 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Deploy Anyway (Not Recommended)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 