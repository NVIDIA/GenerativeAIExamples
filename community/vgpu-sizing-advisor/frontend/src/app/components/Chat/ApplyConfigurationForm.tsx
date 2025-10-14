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
  const [deploymentMode, setDeploymentMode] = useState<'local' | 'remote'>('remote');
  const [formData, setFormData] = useState<FormData>({
    vmIpAddress: "",
    username: "",
    password: "",
    huggingFaceToken: "",
  });

  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showToken, setShowToken] = useState(false);
  
  // Separate state for local vs remote deployments
  const [localState, setLocalState] = useState({
    isSubmitting: false,
    showLogs: false,
    logs: [] as string[],
    isComplete: false,
    showDebugLogs: false,
    displayMessage: "",
    testMetrics: null as any,
    error: null as string | null,
  });
  
  const [remoteState, setRemoteState] = useState({
    isSubmitting: false,
    showLogs: false,
    logs: [] as string[],
    isComplete: false,
    showDebugLogs: false,
    displayMessage: "",
    testMetrics: null as any,
    error: null as string | null,
  });

  // Get current state based on deployment mode
  const currentState = deploymentMode === 'local' ? localState : remoteState;
  const setCurrentState = deploymentMode === 'local' ? setLocalState : setRemoteState;
  
  // Convenience accessors for current state
  const isSubmitting = currentState.isSubmitting;
  const showLogs = currentState.showLogs;
  const configurationLogs = currentState.logs;
  const isConfigurationComplete = currentState.isComplete;
  const showDebugLogs = currentState.showDebugLogs;
  const currentDisplayMessage = currentState.displayMessage;
  const testMetrics = currentState.testMetrics;
  const deploymentError = currentState.error;

  // Helper functions to update current state
  const updateCurrentState = (updates: Partial<typeof currentState>) => {
    setCurrentState(prev => ({ ...prev, ...updates }));
  };

  const setIsSubmitting = (value: boolean) => updateCurrentState({ isSubmitting: value });
  const setShowLogs = (value: boolean) => updateCurrentState({ showLogs: value });
  const setConfigurationLogs = (logs: string[] | ((prev: string[]) => string[])) => {
    if (typeof logs === 'function') {
      setCurrentState(prev => ({ ...prev, logs: logs(prev.logs) }));
    } else {
      updateCurrentState({ logs });
    }
  };
  const setIsConfigurationComplete = (value: boolean) => updateCurrentState({ isComplete: value });
  const setShowDebugLogs = (value: boolean) => updateCurrentState({ showDebugLogs: value });
  const setCurrentDisplayMessage = (value: string) => updateCurrentState({ displayMessage: value });
  const setTestMetrics = (value: any) => updateCurrentState({ testMetrics: value });
  const setDeploymentError = (value: string | null) => updateCurrentState({ error: value });

  // Validate IP address format
  const validateIpAddress = (ip: string): boolean => {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
  };

  // Validate form fields
  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    // Only validate VM fields if in remote mode
    if (deploymentMode === 'remote') {
      if (!formData.vmIpAddress) {
        errors.vmIpAddress = "VM IP address is required";
      } else if (!validateIpAddress(formData.vmIpAddress)) {
        errors.vmIpAddress = "Invalid IP address format";
      }

      if (!formData.username) {
        errors.username = "Username is required";
      }

      if (!formData.password) {
        errors.password = "Password is required (used for automatic SSH key setup)";
      }
    }

    // Always require Hugging Face token
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
    
    // Debug: Check deployment mode at submission
    console.log("=== HANDLE SUBMIT CALLED ===");
    console.log("Current deploymentMode:", deploymentMode);
    console.log("========================");

    if (!validateForm()) {
      return;
    }

    // Update the appropriate state (local or remote)
    setCurrentState(prev => ({
      ...prev,
      isSubmitting: true,
      showLogs: false,
      isComplete: false,
      testMetrics: null,
      logs: [deploymentMode === 'local' ? "Starting local deployment test..." : "Starting configuration test..."],
      displayMessage: "",
      error: null,
    }));

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
      
      console.log("🔍 Model Selection Debug:");
      console.log("  - configData:", configData);
      console.log("  - configData.model_tag:", configData?.model_tag);
      console.log("  - configData.model_name:", configData?.model_name);
      console.log("  - configData.parameters?.model_tag:", configData?.parameters?.model_tag);
      console.log("  - configData.parameters?.model_name:", configData?.parameters?.model_name);
      console.log("  - Selected model:", model);
      
      const payload: any = {
        deployment_mode: deploymentMode,
        hf_token: formData.huggingFaceToken,
        configuration: configData,
        model_tag: model,
        test_duration_seconds: 30,
      };
      
      // Only include VM credentials for remote mode
      if (deploymentMode === 'remote') {
        payload.vm_ip = formData.vmIpAddress;
        payload.username = formData.username;
        payload.password = formData.password;
      }
      
      console.log("=".repeat(80));
      console.log("FRONTEND: Sending request with deployment_mode:", deploymentMode);
      console.log("FRONTEND: Full payload:", JSON.stringify(payload, null, 2));
      console.log("=".repeat(80));
      
      const response = await fetch('/api/test-configuration', {
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
      const errorMsg = error instanceof Error ? error.message : "Failed to apply configuration";
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
    // Form data is intentionally preserved
  };

  const handleClose = async () => {
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
    
    // Reset both local and remote states
    setLocalState({
      isSubmitting: false,
      showLogs: false,
      logs: [],
      isComplete: false,
      showDebugLogs: false,
      displayMessage: "",
      testMetrics: null,
      error: null,
    });
    
    setRemoteState({
      isSubmitting: false,
      showLogs: false,
      logs: [],
      isComplete: false,
      showDebugLogs: false,
      displayMessage: "",
      testMetrics: null,
      error: null,
    });
    
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
    const resultPatterns = [
      "=== vLLM Server Configuration",
      "Configuration Details:",
      "Model:",
      "Status:",
      "GPU Detected:",
      "GPU Memory Utilization",
      "Max Model Length:",
      "KV Cache:",
      "Hardware Usage During Test:",
      "GPU Compute Utilization:",
      "GPU Memory Active:",
      "GPU Temperature:",
      "Power Draw:",
      "Advisor System Configuration:",
      "vGPU Profile:",
      "vCPUs:",
      "System RAM:",
      "GPU Memory Size:",
      "Configuration Validation:",
      "✅",
      "⚠️",
      "vLLM deployment successful",
      "NVIDIA Driver:"
    ];
    
    return configurationLogs.filter(log => {
      // Exclude error messages if deploymentError is set (shown separately)
      if (deploymentError && (log.includes("❌ Error:") || log.includes("Error:"))) {
        return false;
      }
      // Exclude "Next Steps" section and API testing commands
      if (log.includes("Next Steps:") || 
          log.includes("Test API:") || 
          log.includes("View Logs:") || 
          log.includes("Stop Server:") ||
          log.includes("Server Endpoint:") ||
          log.includes("Health Endpoint:") ||
          log.includes("curl") ||
          log.includes("ssh") ||
          log.includes("tail") ||
          log.includes("pkill")) {
        return false;
      }
      // Exclude Inference Test section
      if (log.includes("Inference Test:") ||
          log.includes("Query:") ||
          log.includes("Max Tokens:") ||
          log.includes("Response Preview:")) {
        return false;
      }
      return resultPatterns.some(pattern => log.includes(pattern));
    });
  };

  // Helper function to get debug logs
  const getDebugLogsText = () => {
    const debugPatterns = [
      "Starting configuration",
      "Testing SSH connection",
      "SSH connection",
      "Checking NVIDIA GPU",
      "GPU detected:",
      "NVIDIA Driver:",
      "GPU matches requested",
      "Checking Python",
      "Python version:",
      "Virtual environment",
      "Checking vLLM",
      "vLLM already installed",
      "Authenticating with Hugging Face",
      "Authenticating with HuggingFace",
      "Clearing cached HuggingFace",
      "Successfully authenticated",
      "HuggingFace authentication failed",
      "Failed to authenticate",
      "Error:",
      "Checking for existing vLLM",
      "Cleared any existing",
      "Starting vLLM server with model:",
      "Starting vLLM",
      "vLLM server starting",
      "Waiting for vLLM",
      "vLLM server is ready",
      "Verifying vLLM process",
      "Testing inference endpoint with prompt:",
      "Inference response:",
      "Inference test",
      "Stopping vLLM server"
    ];
    
    return configurationLogs.filter(log => {
      return debugPatterns.some(pattern => log.includes(pattern));
    });
  };

  const handleExportLogs = () => {
    // Get deployment results
    const deploymentResults = getDeploymentResultsText();
    const debugLogs = getDebugLogsText();
    
    // Add header information based on deployment mode
    const header = deploymentMode === 'local' 
      ? [
          '=== Local vLLM Deployment Export ===',
          `Date: ${new Date().toLocaleString()}`,
          `Machine: ${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}`,
          configuration?.parameters?.vGPU_profile ? `vGPU Profile: ${configuration.parameters.vGPU_profile}` : '',
          configuration?.parameters?.model_name ? `Model: ${configuration.parameters.model_name}` : '',
          '================================\n'
        ].filter(Boolean).join('\n')
      : [
          '=== Remote vLLM Deployment Export ===',
          `Date: ${new Date().toLocaleString()}`,
          `VM IP: ${formData.vmIpAddress}`,
          `Username: ${formData.username}`,
          configuration?.parameters?.vGPU_profile ? `vGPU Profile: ${configuration.parameters.vGPU_profile}` : '',
          configuration?.parameters?.model_name ? `Model: ${configuration.parameters.model_name}` : '',
          '================================\n'
        ].filter(Boolean).join('\n');
    
    // Build content
    let fullContent = header + '\n';
    
    // Add deployment results
    fullContent += '\n=== DEPLOYMENT RESULTS ===\n\n';
    if (deploymentError) {
      fullContent += `Status: ❌ Deployment Failed\n\n`;
      fullContent += `${deploymentError}\n\n`;
    } else if (deploymentResults.length > 0) {
      fullContent += `Status: ✅ Deployment Successful\n\n`;
      fullContent += deploymentResults.join('\n');
      fullContent += '\n';
    }
    
    // Add debug logs if they exist
    if (debugLogs.length > 0) {
      fullContent += '\n\n=== DEBUG OUTPUT ===\n\n';
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
              <h2 className="text-xl font-semibold text-white">Deploy vLLM Server</h2>
              <p className="text-sm text-gray-400 mt-1">
                {deploymentMode === 'local' 
                  ? 'Deploy vLLM inference server locally on this machine'
                  : 'Deploy vLLM inference server on remote VM with Hugging Face integration'
                }
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

          {/* Deployment Mode Tabs */}
          <div className="flex gap-2 mt-4 border-b border-neutral-600">
            <button
              type="button"
              onClick={() => setDeploymentMode('local')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                deploymentMode === 'local'
                  ? 'text-green-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Local Machine
              {deploymentMode === 'local' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-400"></div>
              )}
            </button>
            <button
              type="button"
              onClick={() => setDeploymentMode('remote')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                deploymentMode === 'remote'
                  ? 'text-green-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Remote VM
              {deploymentMode === 'remote' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-400"></div>
              )}
            </button>
          </div>
        </div>

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Remote VM Fields - Only show when in remote mode */}
            {deploymentMode === 'remote' && (
              <>
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
                Password{' '}
                <span className="relative group">
                  <span className="text-green-400 text-xs cursor-help">(Auto-configures SSH keys)</span>
                  {/* Hover Tooltip */}
                  <div className="invisible group-hover:visible absolute left-0 top-full mt-2 w-80 bg-green-900/95 border border-green-500/50 rounded-lg p-4 shadow-xl z-50">
                    <div className="flex items-start gap-3">
                      <svg className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h4 className="text-green-300 font-semibold mb-1 text-sm">Automatic SSH Setup</h4>
                        <p className="text-green-200 text-xs">
                          Just enter your VM password once! The tool will automatically set up secure SSH keys (vgpu_sizing_advisor) for you.
                        </p>
                        <p className="text-green-200 text-xs mt-2">
                          <strong>First time:</strong> Uses password to copy SSH keys to VM.<br />
                          <strong>After that:</strong> Secure key-based authentication (no password needed).
                        </p>
                      </div>
                    </div>
                  </div>
                </span>
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
              </>
            )}

            {/* Hugging Face Token - Always visible for both local and remote */}
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
                  : "bg-blue-600 text-white hover:bg-blue-700"
              }`}
            >
              {isSubmitting 
                ? (deploymentMode === 'local' ? "Testing Locally..." : "Running Test...") 
                : isConfigurationComplete
                ? (deploymentMode === 'local' ? "Test Locally Again" : "Run Test Again")
                : (deploymentMode === 'local' ? "Test Locally" : "Test on Remote VM")}
            </button>
          </form>

          {/* Configuration Status */}
          {isSubmitting && (
            <div className="mt-6 border-t border-neutral-700 pt-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-white mb-4">Running Configuration Test</h3>
                <Spinner />
                <p className="text-sm text-gray-400 mt-4">
                  {deploymentMode === 'local' 
                    ? 'Please wait while we test locally on this machine...'
                    : 'Please wait while we test your VM configuration...'}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  This test typically takes 30-60 seconds
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

          {/* Deployment Summary - VM Performance Info */}
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
                <div className="bg-gradient-to-br from-neutral-900 to-black rounded-lg border border-neutral-700 overflow-hidden group">
                  <div className="relative">
                    <div className="p-6 max-h-96 overflow-y-auto">
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
                      
                      // Group logs into sections
                      const sections: { title: string; logs: string[]; }[] = [];
                      let currentSection: { title: string; logs: string[]; } | null = null;
                      
                      resultLogs.forEach((log) => {
                        if (log.includes("=== vLLM Server Configuration")) {
                          currentSection = { title: "Status", logs: [] };
                          sections.push(currentSection);
                        } else if (log.includes("Configuration Details:")) {
                          currentSection = { title: "Configuration Details", logs: [] };
                          sections.push(currentSection);
                        } else if (log.includes("Hardware Usage During Test:")) {
                          currentSection = { title: "Hardware Usage", logs: [] };
                          sections.push(currentSection);
                        } else if (log.includes("Inference Test:")) {
                          currentSection = { title: "Inference Test", logs: [] };
                          sections.push(currentSection);
                        } else if (log.includes("Advisor System Configuration:")) {
                          currentSection = { title: "System Specification", logs: [] };
                          sections.push(currentSection);
                        } else if (log.includes("Configuration Validation:")) {
                          currentSection = { title: "Validation", logs: [] };
                          sections.push(currentSection);
                        } else if (currentSection && !log.includes("===")) {
                          currentSection.logs.push(log);
                        }
                      });
                      
                      return (
                        <div className="space-y-6">
                          {sections.map((section, sectionIndex) => (
                            <div key={sectionIndex}>
                              <div className="mb-3">
                                <h4 className="text-sm font-semibold text-green-400 uppercase tracking-wide">{section.title}</h4>
                              </div>
                              <div className="space-y-1.5 pl-4">
                                {section.logs.map((log, logIndex) => {
                                  // Determine log styling based on content
                                  let className = "text-gray-300 text-sm leading-relaxed break-words";
                                  
                                  if (log.startsWith("•")) {
                                    className = "text-gray-200 font-medium break-words";
                                  } else if (log.includes("✅")) {
                                    className = "text-green-400 break-words";
                                  } else if (log.includes("⚠️")) {
                                    className = "text-yellow-400 break-words";
                                  } else if (log.includes("❌") || log.includes("Error")) {
                                    className = "text-red-400 break-words";
                                  } else if (log.includes("Model:") || log.includes("Status:") || log.includes("GPU Detected:")) {
                                    className = "text-blue-300 font-medium break-words";
                                  } else if (log.includes("Response Preview:") || log.includes("Query:")) {
                                    className = "text-purple-300 font-mono text-xs bg-black/50 px-2 py-1.5 rounded block break-words";
                                  }
                        
                        return (
                                    <div key={logIndex} className={className}>
                            {log}
                          </div>
                        );
                                })}
                              </div>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                    </div>
                    <button
                      onClick={async () => {
                        const deploymentResults = getDeploymentResultsText();
                        const text = `Deployment Results\n${"=".repeat(18)}\n${deploymentResults.join("\n")}`;
                        await copyToClipboard(text);
                      }}
                      className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-neutral-800 hover:bg-neutral-700 text-gray-400 hover:text-gray-200 p-1.5 rounded"
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

          {/* Debug Output - Execution Steps */}
          {!isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <h3 className="text-sm font-medium text-gray-300">Debug Output</h3>
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
                <div className="bg-black rounded-lg border border-neutral-800 overflow-hidden group">
                  <div className="relative">
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
                    <button
                      onClick={async () => {
                        const debugLogs = getDebugLogsText();
                        const text = `Debug Output\n${"=".repeat(12)}\n${debugLogs.join("\n")}`;
                        await copyToClipboard(text);
                      }}
                      className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-neutral-800 hover:bg-neutral-700 text-gray-400 hover:text-gray-200 p-1.5 rounded"
                      title="Copy debug output"
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
    </div>
  );
} 