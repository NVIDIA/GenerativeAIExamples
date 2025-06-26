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

import React, { useState } from "react";

interface WorkloadConfig {
  workloadType: string;
  specificModel: string;
  modelSize: string;
  batchSize: string;
  memoryRequirement: string;
  embeddingModel: string;
  concurrentUsers: string;
  gpuInventory: { [key: string]: number };
  framework: string;
  precision: string;
}

interface WorkloadConfigWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (query: string) => void;
}

export default function WorkloadConfigWizard({
  isOpen,
  onClose,
  onSubmit,
}: WorkloadConfigWizardProps) {
  const [config, setConfig] = useState<WorkloadConfig>({
    workloadType: "",
    specificModel: "",
    modelSize: "",
    batchSize: "",
    memoryRequirement: "",
    embeddingModel: "",
    concurrentUsers: "",
    gpuInventory: {},
    framework: "",
    precision: "",
  });

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  const workloadTypes = [
    { value: "rag", label: "RAG (Retrieval-Augmented Generation)", desc: "Document search and generation workflows" },
    { value: "training", label: "Model Training", desc: "Training neural networks and deep learning models" },
    { value: "inference", label: "LLM Inference", desc: "Running predictions and serving trained models" },
    { value: "fine-tuning", label: "Model Fine-Tuning", desc: "Adapting pre-trained models for specific tasks" }
  ];

  const modelSizes = [
    { value: "small", label: "Small (< 7B parameters)", desc: "Lightweight models, fast inference" },
    { value: "medium", label: "Medium (7B-30B parameters)", desc: "Balanced performance and speed" },
    { value: "large", label: "Large (40B-70B parameters)", desc: "High-quality results, more compute" },
    { value: "xlarge", label: "Extra Large (70B+ parameters)", desc: "Heavy compute, stronger reasoning models" }
  ];

  const embeddingModels = [
    { value: "nvidia/nvolveqa-embed-large-1B", label: "nvidia/nvolveqa-embed-large-1B", desc: "1B parameter embedding model" },
    { value: "text-embedding-ada-002-350M", label: "text-embedding-ada-002-350M", desc: "350M parameter OpenAI embedding model" },
    { value: "nvidia/nvolveqa-embed-base-400M", label: "nvidia/nvolveqa-embed-base-400M", desc: "400M parameter embedding model" },
    { value: "nvidia/nemo-embed-qa-200M", label: "nvidia/nemo-embed-qa-200M", desc: "200M parameter QA embedding model" },
    { value: "all-MiniLM-L6-v2-80M", label: "all-MiniLM-L6-v2-80M", desc: "80M parameter compact embedding model" },
    { value: "llama-3-2-nv-embedqa-1b-v2", label: "llama-3-2-nv-embedqa-1b-v2", desc: "Llama 3.2 based embedding model" }
  ];

  const performanceLevels = [
    { value: "basic", label: "Basic", desc: "Cost-optimized, adequate performance" },
    { value: "standard", label: "Standard", desc: "Good balance of cost and performance" },
    { value: "high", label: "High Performance", desc: "Optimized for speed and throughput" },
    { value: "maximum", label: "Maximum", desc: "Best possible performance, premium cost" }
  ];

  const availableGPUInventory = [
    { value: "l40s", label: "NVIDIA L40S", desc: "48GB GDDR6 with ECC, Ada Lovelace, 350W - ML training & inference + virtual workstations" },
    { value: "l40", label: "NVIDIA L40", desc: "48GB GDDR6 with ECC, Ada Lovelace - Virtual workstations & compute workloads" },
    { value: "l4", label: "NVIDIA L4", desc: "24GB GDDR6 with ECC, Ada Lovelace, 72W - AI inference, small model training & 3D graphics" },
    { value: "a40", label: "NVIDIA A40", desc: "48GB GDDR6 with ECC, Ampere, 300W - 3D design & mixed virtual workstation workloads" },
    { value: "a16", label: "NVIDIA A16", desc: "4x 16GB GDDR6 with ECC, Ampere, 250W - Entry-level virtual workstations" },
    { value: "a10", label: "NVIDIA A10", desc: "24GB GDDR6 with ECC, Ampere, 140W - Mainstream professional visualization" },
    { value: "blackwell", label: "NVIDIA Blackwell", desc: "Next-generation architecture (specifications pending)" },
    { value: "mixed", label: "Mixed RTX vWS GPUs", desc: "Multiple different RTX vWS compatible GPU models" }
  ];

  const specificModels = [
    { value: "llama-3-8b", label: "Llama-3-8B" },
    { value: "llama-3-70b", label: "Llama-3-70B" },
    { value: "llama-3.1-8b", label: "Llama-3.1-8B" },
    { value: "llama-3.1-70b", label: "Llama-3.1-70B" },
    { value: "mistral-7b", label: "Mistral-7B" },
    { value: "falcon-7b", label: "Falcon-7B" },
    { value: "falcon-40b", label: "Falcon-40B" },
    { value: "falcon-180b", label: "Falcon-180B" },
    { value: "qwen-14b", label: "Qwen-14B" },
  ];

  const frameworks = [
    { value: "pytorch", label: "PyTorch" },
    { value: "tensorflow", label: "TensorFlow" },
    { value: "huggingface", label: "Hugging Face" },
    { value: "nemo", label: "NVIDIA NeMo" },
    { value: "triton", label: "NVIDIA Triton" },
    { value: "other", label: "Other" }
  ];

  const precisionOptions = [
    { value: "fp16", label: "FP16", desc: "Half precision - Recommended balance of performance and accuracy" },
    { value: "int8", label: "INT-8", desc: "8-bit integer - Highest performance, some accuracy trade-off" },
  ];

  const handleInputChange = (field: keyof WorkloadConfig, value: string) => {
    setConfig((prev: WorkloadConfig) => ({ ...prev, [field]: value }));
  };

  const handleGPUInventoryChange = (gpuType: string, quantity: number) => {
    setConfig((prev: WorkloadConfig) => {
      const newInventory = { ...prev.gpuInventory };
      if (quantity <= 0) {
        delete newInventory[gpuType];
      } else {
        newInventory[gpuType] = quantity;
      }
      return { ...prev, gpuInventory: newInventory };
    });
  };

  const getTotalGPUs = (): number => {
    return Object.values(config.gpuInventory).reduce((sum, count) => {
      return sum + (count as number);
    }, 0);
  };

  const generateQuery = (): string => {
    const parts = [];
    
    // Base query structure
    parts.push(`I need a vGPU configuration for`);
    
    // Workload type
    if (config.workloadType) {
      const workloadLabel = workloadTypes.find(w => w.value === config.workloadType)?.label || config.workloadType;
      parts.push(`${workloadLabel.trim()}`);
    }
    
    // Model size
    if (config.modelSize) {
      const sizeLabel = modelSizes.find(s => s.value === config.modelSize)?.label || config.modelSize;
      parts.push(`with ${sizeLabel.toLowerCase()}`);
    }
    
    // GPU Inventory - Enhanced with specific quantities
    if (config.gpuInventory && Object.keys(config.gpuInventory).length > 0) {
      const gpuLabels = Object.entries(config.gpuInventory)
        .filter(([_, quantity]: [string, number]) => quantity > 0)
        .map(([gpu, quantity]: [string, number]) => {
          const gpuInfo = availableGPUInventory.find(g => g.value === gpu);
          return `${quantity}x ${gpuInfo?.label || gpu}`;
        });
      parts.push(`using available GPU inventory: ${gpuLabels.join(', ')}`);
    } else {
      // Recommended GPU (L40S) if no GPU is selected
      parts.push(`using available GPU inventory: 1x NVIDIA L40S`);
    }
    
    // Specific Model
    if (config.specificModel && config.specificModel !== 'unknown') {
      const modelLabel = specificModels.find(m => m.value === config.specificModel)?.label || config.specificModel;
      parts.push(`running ${modelLabel}`);
    }
    
    // Performance requirements
    if (config.embeddingModel) {
      const modelLabel = embeddingModels.find(m => m.value === config.embeddingModel)?.label || config.embeddingModel;
      parts.push(`using embedding model ${modelLabel}`);
    } else {
      // Recommended embedding model
      parts.push(`using embedding model nvidia/nvolveqa-embed-large-1B`);
    }
    
    // Memory and batch size
    const requirements = [];
    if (config.memoryRequirement) {
      requirements.push(`${config.memoryRequirement} memory`);
    }
    if (config.batchSize) {
      requirements.push(`batch size of ${config.batchSize}`);
    }
    if (config.concurrentUsers) {
      requirements.push(`${config.concurrentUsers} concurrent users`);
    }
    
    if (requirements.length > 0) {
      parts.push(`with ${requirements.join(', ')}`);
    }
    
    // Framework
    if (config.framework && config.framework !== 'other') {
      parts.push(`using ${config.framework}`);
    }
    
    // Precision
    if (config.precision) {
      const precisionLabel = precisionOptions.find(p => p.value === config.precision)?.label || config.precision;
      parts.push(`with ${precisionLabel} precision`);
    } else {
      // Recommended precision
      parts.push(`with FP16 precision`);
    }
    
    return parts.join(' ') + '.';
  };

  const handleSubmit = () => {
    const query = generateQuery();
    onSubmit(query);
    onClose();
    // Reset form
    setConfig({
      workloadType: "",
      specificModel: "",
      modelSize: "",
      batchSize: "",
      memoryRequirement: "",
      embeddingModel: "",
      concurrentUsers: "",
      gpuInventory: {},
      framework: "",
      precision: "",
    });
    setCurrentStep(1);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return config.workloadType !== "";
      case 2:
        return config.specificModel || config.modelSize;
      case 3:
        return true; // Additional requirements are optional
      default:
        return false;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-neutral-900 rounded-lg border border-neutral-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-6 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">AI Workload Configuration Wizard</h2>
              <p className="text-green-100 text-sm mt-1">
                Configure your AI workload to get personalized vGPU recommendations
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-green-200 text-xl"
            >
              ✕
            </button>
          </div>
          
          {/* Progress indicator */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm">
              <span>Step {currentStep} of {totalSteps}</span>
              <span>{Math.round((currentStep / totalSteps) * 100)}% Complete</span>
            </div>
            <div className="w-full bg-green-800 rounded-full h-2 mt-2">
              <div 
                className="bg-white rounded-full h-2 transition-all duration-300"
                style={{ width: `${(currentStep / totalSteps) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Step 1: Workload Type & Use Case */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">What type of AI workload do you need?</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {workloadTypes.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => handleInputChange("workloadType", type.value)}
                      className={`p-4 rounded-lg border text-left transition-all ${
                        config.workloadType === type.value
                          ? "border-green-500 bg-green-900/20 text-white"
                          : "border-neutral-600 bg-neutral-800 text-gray-300 hover:border-green-600"
                      }`}
                    >
                      <div className="font-medium">{type.label}</div>
                      <div className="text-sm text-gray-400 mt-1">{type.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Performance Requirements */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Model Size & Performance</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Specific Model (if known)</label>
                    <select
                      value={config.specificModel}
                      onChange={(e) => handleInputChange("specificModel", e.target.value)}
                      className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white mb-4"
                    >
                      <option value="">Select a specific model</option>
                      {specificModels.map((model) => (
                        <option key={model.value} value={model.value}>{model.label}</option>
                      ))}
                    </select>
                  </div>

                  {(config.specificModel === 'unknown' || config.specificModel === '') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Model Size Category</label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {modelSizes.map((size) => (
                          <button
                            key={size.value}
                            onClick={() => handleInputChange("modelSize", size.value)}
                            className={`p-3 rounded-lg border text-left transition-all ${
                              config.modelSize === size.value
                                ? "border-green-500 bg-green-900/20 text-white"
                                : "border-neutral-600 bg-neutral-800 text-gray-300 hover:border-green-600"
                            }`}
                          >
                            <div className="font-medium">{size.label}</div>
                            <div className="text-sm text-gray-400">{size.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Embedding Model (Optional)</label>
                    <select
                      value={config.embeddingModel}
                      onChange={(e) => handleInputChange("embeddingModel", e.target.value)}
                      className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                    >
                      <option value="">Recommended (nvidia/nvolveqa-embed-large-1B)</option>
                      {embeddingModels.map((model) => (
                        <option key={model.value} value={model.value}>{model.label}</option>
                      ))}
                    </select>
                    {config.embeddingModel && (
                      <p className="text-sm text-gray-400 mt-2">
                        {embeddingModels.find(m => m.value === config.embeddingModel)?.desc}
                      </p>
                    )}
                  </div>

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Framework</label>
                      <select
                        value={config.framework}
                        onChange={(e) => handleInputChange("framework", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select framework</option>
                        {frameworks.map((fw) => (
                          <option key={fw.value} value={fw.value}>{fw.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Precision</label>
                      <select
                        value={config.precision}
                        onChange={(e) => handleInputChange("precision", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Recommended (FP16)</option>
                        {precisionOptions.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                      {config.precision && (
                        <p className="text-sm text-gray-400 mt-2">
                          {precisionOptions.find(p => p.value === config.precision)?.desc}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Additional Requirements */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Additional Requirements (Optional)</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Memory Requirement</label>
                  <select
                    value={config.memoryRequirement}
                    onChange={(e) => handleInputChange("memoryRequirement", e.target.value)}
                    className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                  >
                    <option value="">Select memory needs</option>
                    <option value="8-16 GB">Low (8-16 GB)</option>
                    <option value="16-32 GB">Medium (16-32 GB)</option>
                    <option value="32-64 GB">High (32-64 GB)</option>
                    <option value="64+ GB">Very High (64+ GB)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Concurrent Users</label>
                  <select
                    value={config.concurrentUsers}
                    onChange={(e) => handleInputChange("concurrentUsers", e.target.value)}
                    className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                  >
                    <option value="">Select user load</option>
                    <option value="1-10">Small (1-10 users)</option>
                    <option value="10-50">Medium (10-50 users)</option>
                    <option value="50-200">Large (50-200 users)</option>
                    <option value="200+">Enterprise (200+ users)</option>
                  </select>
                </div>
              </div>

              {/* GPU Selection Section */}
              <div className="mt-6 pt-6 border-t border-neutral-700">
                <h4 className="text-md font-semibold text-white mb-4">GPU Selection</h4>
                <p className="text-sm text-gray-400 mb-4">
                  Select the GPU you want to use. If you don't select a GPU, the recommended NVIDIA L40S will be used.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">GPU Model</label>
                    <select
                      value={Object.keys(config.gpuInventory)[0] || ""}
                      onChange={(e) => {
                        // Clear existing inventory and set the new one
                        setConfig(prev => ({
                          ...prev,
                          gpuInventory: e.target.value ? { [e.target.value]: 1 } : {}
                        }));
                      }}
                      className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                    >
                      <option value="">Recommended (NVIDIA L40S)</option>
                      {availableGPUInventory.map((gpu) => (
                        <option key={gpu.value} value={gpu.value}>
                          {gpu.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Quantity selector for selected GPU */}
                  {Object.keys(config.gpuInventory)[0] && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Quantity</label>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => {
                            const gpuType = Object.keys(config.gpuInventory)[0];
                            const currentQty = config.gpuInventory[gpuType] || 1;
                            handleGPUInventoryChange(gpuType, Math.max(1, currentQty - 1));
                          }}
                          className="w-10 h-10 rounded-full border border-green-500 text-green-500 hover:bg-green-500 hover:text-white text-lg font-bold transition-all"
                        >
                          −
                        </button>
                        <span className="w-16 text-center text-white font-mono text-lg">
                          {Object.values(config.gpuInventory)[0] || 1}
                        </span>
                        <button
                          onClick={() => {
                            const gpuType = Object.keys(config.gpuInventory)[0];
                            const currentQty = config.gpuInventory[gpuType] || 1;
                            handleGPUInventoryChange(gpuType, currentQty + 1);
                          }}
                          className="w-10 h-10 rounded-full border border-green-500 text-green-500 hover:bg-green-500 hover:text-white text-lg font-bold transition-all"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Show selected GPU description */}
                {Object.keys(config.gpuInventory)[0] && (
                  <div className="mt-3 p-3 bg-neutral-800 border border-neutral-600 rounded-lg">
                    <p className="text-sm text-gray-400">
                      {availableGPUInventory.find(g => g.value === Object.keys(config.gpuInventory)[0])?.desc}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-neutral-700 flex justify-between">
          <div className="flex space-x-3">
            {currentStep > 1 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="px-4 py-2 bg-neutral-700 text-white rounded-lg hover:bg-neutral-600 transition-colors"
              >
                ← Previous
              </button>
            )}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-neutral-700 text-white rounded-lg hover:bg-neutral-600 transition-colors"
            >
              Cancel
            </button>
            
            {currentStep < totalSteps ? (
              <button
                onClick={() => setCurrentStep(currentStep + 1)}
                disabled={!canProceed()}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  canProceed()
                    ? "bg-green-600 text-white hover:bg-green-700"
                    : "bg-neutral-600 text-gray-400 cursor-not-allowed"
                }`}
              >
                Next →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
Get Recommendations
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 