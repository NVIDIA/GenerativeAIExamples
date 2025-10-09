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

interface AdvancedConfig {
  modelMemoryOverhead: number;
  hypervisorReserveGb: number;
  cudaMemoryOverhead: number;
  vcpuPerGpu: number;
  ramGbPerVcpu: number;
}

interface WorkloadConfig {
  workloadType: string;
  specificModel: string;
  modelSize: string;
  batchSize: string;
  promptSize: string;
  responseSize: string;
  embeddingModel: string;
  gpuInventory: { [key: string]: number };
  precision: string;
  vectorDimension?: string;
  numberOfVectors?: string;
  advancedConfig: AdvancedConfig;
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
    promptSize: "1024",
    responseSize: "256",
    embeddingModel: "",
    gpuInventory: {},
    precision: "",
    vectorDimension: "384",  // Default to 384
    numberOfVectors: "10000", // Default to 10,000
    advancedConfig: {
      modelMemoryOverhead: 1.3,
      hypervisorReserveGb: 3.0,
      cudaMemoryOverhead: 1.2,
      vcpuPerGpu: 8,
      ramGbPerVcpu: 8,
    },
  });

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;
  const [dynamicModels, setDynamicModels] = useState<Array<{ value: string; label: string; modelTag: string }>>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [showAdvancedConfig, setShowAdvancedConfig] = useState(false);

  // Fetch dynamic models from backend on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        // Use Next.js API route to avoid CORS issues
        const response = await fetch('/api/available-models');
        
        if (response.ok) {
          const data = await response.json();
          if (data.models && data.models.length > 0) {
            // Use modelTag as value to ensure uniqueness (full model ID like "org/model-name")
            const formattedModels = data.models.map((model: any) => ({
              value: model.modelTag.toLowerCase().replace(/\//g, '-').replace(/\./g, '-'),
              label: model.label,
              modelTag: model.modelTag
            }));
            setDynamicModels(formattedModels);
            console.log(`✓ Successfully loaded ${formattedModels.length} models from HuggingFace`);
          } else {
            console.warn('No models returned from API');
          }
        } else {
          console.warn('API returned non-OK status:', response.status);
        }
      } catch (error) {
        console.error('Failed to fetch dynamic models:', error);
        console.log('Using fallback model list');
        // Fallback to hardcoded models will be used
      } finally {
        setIsLoadingModels(false);
      }
    };

    if (isOpen) {
      fetchModels();
    }
  }, [isOpen]);

  const workloadTypes = [
    { value: "rag", label: "RAG (Retrieval-Augmented Generation)", desc: "Document search and generation workflows" },
    { value: "inference", label: "LLM Inference", desc: "Running predictions and serving trained models" },
    // { value: "fine-tuning", label: "Model Fine-Tuning", desc: "Adapting pre-trained models for specific tasks" }
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
    { value: "DC", label: "NVIDIA RTX PRO 6000 Blackwell Server Edition (Refer as DC)", desc: "96GB GDDR7 with ECC, Blackwell, passive‑cooled dual‑slot PCIe Gen5 – Enterprise AI/graphics, scientific computing & virtual workstations" },
  ];

  // Fallback hardcoded models in case dynamic fetch fails
  const fallbackModels = [
    { value: "llama-3-8b", label: "Llama-3-8B", modelTag: "meta-llama/Meta-Llama-3-8B-Instruct" },
    { value: "llama-3-70b", label: "Llama-3-70B", modelTag: "meta-llama/Meta-Llama-3-70B-Instruct" },
    { value: "llama-3.1-8b", label: "Llama-3.1-8B", modelTag: "meta-llama/Llama-3.1-8B-Instruct" },
    { value: "llama-3.1-70b", label: "Llama-3.1-70B", modelTag: "meta-llama/Llama-3.3-70B-Instruct" },
    { value: "mistral-7b", label: "Mistral-7B", modelTag: "mistralai/Mistral-7B-Instruct-v0.3" },
    { value: "falcon-7b", label: "Falcon-7B", modelTag: "tiiuae/falcon-7b-instruct" },
    { value: "falcon-40b", label: "Falcon-40B", modelTag: "tiiuae/falcon-40b-instruct" },
    { value: "falcon-180b", label: "Falcon-180B", modelTag: "tiiuae/falcon-180B" },
    { value: "qwen-14b", label: "Qwen-14B", modelTag: "Qwen/Qwen3-14B" },
  ];

  // Use dynamic models if loaded, otherwise use fallback
  const specificModels = dynamicModels.length > 0 ? dynamicModels : fallbackModels;

  const precisionOptions = [
    { value: "fp16", label: "FP16", desc: "Half precision - Recommended balance of performance and accuracy" },
    { value: "int8", label: "INT-8", desc: "8-bit integer - Highest performance, some accuracy trade-off" },
  ];

  const handleInputChange = (field: keyof WorkloadConfig, value: string) => {
    setConfig((prev: WorkloadConfig) => ({ ...prev, [field]: value }));
  };

  const handleAdvancedConfigChange = (field: keyof AdvancedConfig, value: number) => {
    setConfig((prev: WorkloadConfig) => ({
      ...prev,
      advancedConfig: {
        ...prev.advancedConfig,
        [field]: value,
      },
    }));
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

  const getRecommendedEmbeddingModel = (): string => {
    // First check for specific model recommendations
    if (config.specificModel && config.specificModel !== 'unknown') {
      if (config.specificModel.includes('llama-3')) {
        return 'llama-3-2-nv-embedqa-1b-v2';
      }
      if (config.specificModel.includes('mistral')) {
        return 'nvidia/nemo-embed-qa-200M';
      }
      if (config.specificModel.includes('falcon-180b')) {
        return 'nvidia/nvolveqa-embed-large-1B';
      }
      if (config.specificModel.includes('falcon-40b')) {
        return 'nvidia/nvolveqa-embed-base-400M';
      }
      if (config.specificModel.includes('falcon-7b')) {
        return 'all-MiniLM-L6-v2-80M';
      }
      if (config.specificModel.includes('qwen')) {
        return 'text-embedding-ada-002-350M';
      }
    }
    
    // Fall back to model size category recommendations
    if (config.modelSize) {
      switch (config.modelSize) {
        case 'small':
          return 'all-MiniLM-L6-v2-80M';
        case 'medium':
          return 'nvidia/nvolveqa-embed-base-400M';
        case 'large':
          return 'nvidia/nvolveqa-embed-large-1B';
        case 'xlarge':
          return 'llama-3-2-nv-embedqa-1b-v2';
        default:
          return 'nvidia/nvolveqa-embed-large-1B';
      }
    }
    
    // Default recommendation
    return 'nvidia/nvolveqa-embed-large-1B';
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
    if (config.workloadType === 'rag' && config.embeddingModel) {
      const modelLabel = embeddingModels.find(m => m.value === config.embeddingModel)?.label || config.embeddingModel;
      parts.push(`using embedding model ${modelLabel}`);
    } else if (config.workloadType === 'rag') {
      // Use recommended embedding model based on selection
      const recommendedModel = getRecommendedEmbeddingModel();
      const modelLabel = embeddingModels.find(m => m.value === recommendedModel)?.label || recommendedModel;
      parts.push(`using embedding model ${modelLabel}`);
    }
    
    // Performance requirements
    const requirements = [];
    if (config.promptSize) {
      requirements.push(`prompt size of ${config.promptSize} tokens`);
    }
    if (config.responseSize) {
      requirements.push(`response size of ${config.responseSize} tokens`);
    }
    if (config.batchSize) {
      requirements.push(`batch size of ${config.batchSize}`);
    }
    
    if (requirements.length > 0) {
      parts.push(`with ${requirements.join(', ')}`);
    }
    
    // Precision
    if (config.precision) {
      const precisionLabel = precisionOptions.find(p => p.value === config.precision)?.label || config.precision;
      parts.push(`with ${precisionLabel} precision`);
    } else {
      // Recommended precision
      parts.push(`with FP16 precision`);
    }
    
    // Add retrieval configuration for RAG workloads
    if (config.workloadType === 'rag' && (config.vectorDimension || config.numberOfVectors)) {
      const retrievalParts = [];
      if (config.vectorDimension) {
        retrievalParts.push(`${config.vectorDimension}d vectors`);
      }
      if (config.numberOfVectors) {
        retrievalParts.push(`${config.numberOfVectors} total vectors`);
      }
      if (retrievalParts.length > 0) {
        parts.push(`with retrieval configuration: ${retrievalParts.join(', ')}`);
      }
    }
    
    const naturalLanguageQuery = parts.join(' ') + '.';
    
    // EMBED THE STRUCTURED CONFIG DATA AS JSON
    // This preserves all the original user selections
    const structuredConfig = {
      workloadType: config.workloadType,
      specificModel: config.specificModel,
      modelTag: config.specificModel ? specificModels.find(m => m.value === config.specificModel)?.modelTag : null,
      modelSize: config.modelSize,
      batchSize: config.batchSize,
      promptSize: config.promptSize ? parseInt(config.promptSize) : 1024,
      responseSize: config.responseSize ? parseInt(config.responseSize) : 256,
      embeddingModel: config.workloadType === 'rag' ? (config.embeddingModel || getRecommendedEmbeddingModel()) : null,
      gpuInventory: config.gpuInventory,
      precision: config.precision || 'fp16',
      // Add retrieval config for RAG
      ...(config.workloadType === 'rag' && {
        vectorDimension: config.vectorDimension ? parseInt(config.vectorDimension) : null,
        numberOfVectors: config.numberOfVectors ? parseInt(config.numberOfVectors) : null,
      }),
      // Add computed values for easier backend processing
      selectedGPU: Object.keys(config.gpuInventory)[0] || 'l40s',
      gpuCount: Object.values(config.gpuInventory)[0] as number || 1,
      // Include advanced configuration
      advancedConfig: config.advancedConfig,
    };
    
    // Embed as HTML comment that won't be visible to user but can be parsed in backend
    return naturalLanguageQuery + `\n<!--VGPU_CONFIG:${JSON.stringify(structuredConfig)}-->`;
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
      promptSize: "1024",
      responseSize: "256",
      embeddingModel: "",
      gpuInventory: {},
      precision: "",
      vectorDimension: "384",  // Default to 384
      numberOfVectors: "10000", // Default to 10,000
      advancedConfig: {
        modelMemoryOverhead: 1.3,
        hypervisorReserveGb: 3.0,
        cudaMemoryOverhead: 1.2,
        vcpuPerGpu: 8,
        ramGbPerVcpu: 8,
      },
    });
    setCurrentStep(1);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return config.workloadType !== "";
      case 2:
        // If "unknown" is selected, user must also select a model size
        if (config.specificModel === 'unknown') {
          return config.modelSize !== '';
        }
        // Otherwise, just need a specific model selected
        return config.specificModel !== '';
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
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Specific Model (if known)
                      {isLoadingModels && <span className="ml-2 text-sm text-green-500 animate-pulse">Loading models...</span>}
                    </label>
                    <select
                      value={config.specificModel}
                      onChange={(e) => handleInputChange("specificModel", e.target.value)}
                      className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white mb-4"
                      disabled={isLoadingModels}
                    >
                      <option value="" disabled>
                        {isLoadingModels ? "Loading models from HuggingFace..." : "Select a specific model"}
                      </option>
                      <option value="unknown">Unknown / Not Sure</option>
                      {specificModels.map((model) => (
                        <option key={model.value} value={model.value}>{model.label}</option>
                      ))}
                    </select>
                    {!isLoadingModels && dynamicModels.length > 0 && (
                      <p className="text-xs text-green-500 mb-2">✓ {dynamicModels.length} models loaded from HuggingFace</p>
                    )}
                  </div>

                  {/* Only show model size category when "unknown" is selected */}
                  {config.specificModel === 'unknown' && (
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

                  {/* Only show embedding model for RAG workloads */}
                  {config.workloadType === 'rag' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Embedding Model</label>
                      <select
                        value={config.embeddingModel}
                        onChange={(e) => handleInputChange("embeddingModel", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Recommended ({getRecommendedEmbeddingModel()})</option>
                        {embeddingModels.map((model) => (
                          <option key={model.value} value={model.value}>{model.label}</option>
                        ))}
                      </select>
                      {config.embeddingModel && (
                        <p className="text-sm text-gray-400 mt-2">
                          {embeddingModels.find(m => m.value === config.embeddingModel)?.desc}
                        </p>
                      )}
                      {!config.embeddingModel && (
                        <p className="text-sm text-gray-400 mt-2">
                          {embeddingModels.find(m => m.value === getRecommendedEmbeddingModel())?.desc}
                        </p>
                      )}
                    </div>
                  )}

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
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

                  {/* Retrieval Section - Only for RAG workload */}
                  {config.workloadType === 'rag' && (
                    <div className="mt-6 pt-6 border-t border-neutral-700">
                      <h4 className="text-md font-semibold text-white mb-4">Retrieval Configuration</h4>
                      <p className="text-sm text-gray-400 mb-4">
                        Configure vector database settings for RAG retrieval
                      </p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Vector Dimension</label>
                          <select
                            value={config.vectorDimension || ""}
                            onChange={(e) => handleInputChange("vectorDimension", e.target.value)}
                            className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                          >
                            <option value="">Select dimension</option>
                            <option value="384">384 (Compact)</option>
                            <option value="768">768 (Standard)</option>
                            <option value="1024">1024 (Large)</option>
                          </select>
                          <p className="text-sm text-gray-400 mt-1">
                            Must match your embedding model's output dimension
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">Number of Vectors</label>
                          <input
                            type="number"
                            value={config.numberOfVectors || ""}
                            onChange={(e) => handleInputChange("numberOfVectors", e.target.value)}
                            placeholder="e.g., 1000000"
                            min="1000"
                            step="1000"
                            className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white placeholder-gray-500"
                          />
                          <p className="text-sm text-gray-400 mt-1">
                            Total vectors in your knowledge base
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Prompt Size (tokens)</label>
                  <input
                    type="number"
                    value={config.promptSize}
                    onChange={(e) => handleInputChange("promptSize", e.target.value)}
                    placeholder="e.g., 1024"
                    min="256"
                    max="32768"
                    step="256"
                    className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white placeholder-gray-500"
                  />
                  <p className="text-sm text-gray-400 mt-1">
                    Maximum input prompt length in tokens
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Response Size (tokens)</label>
                  <input
                    type="number"
                    value={config.responseSize}
                    onChange={(e) => handleInputChange("responseSize", e.target.value)}
                    placeholder="e.g., 256"
                    min="128"
                    max="8192"
                    step="128"
                    className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white placeholder-gray-500"
                  />
                  <p className="text-sm text-gray-400 mt-1">
                    Maximum response length in tokens
                  </p>
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

              {/* Advanced Configuration Dropdown */}
              <div className="mt-6 pt-6 border-t border-neutral-700">
                <button
                  type="button"
                  onClick={() => setShowAdvancedConfig(!showAdvancedConfig)}
                  className="w-full flex items-center justify-between p-4 bg-neutral-800 hover:bg-neutral-750 rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-md font-semibold text-white">Advanced Configuration</span>
                    <span className="text-xs text-gray-400 bg-neutral-700 px-2 py-1 rounded">Optional</span>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform ${showAdvancedConfig ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showAdvancedConfig && (
                  <div className="mt-4 p-4 bg-neutral-800 rounded-lg border border-neutral-700">
                    <p className="text-sm text-gray-400 mb-6">
                      Fine-tune calculator accuracy with advanced parameters. The defaults are suitable for most use cases.
                    </p>

                    <div className="space-y-6">
                      {/* Model Memory Overhead */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-sm font-medium text-gray-300">
                            Model Memory Overhead
                          </label>
                          <span className="text-sm text-green-500 font-mono">
                            {config.advancedConfig.modelMemoryOverhead.toFixed(2)}x
                          </span>
                        </div>
                        <input
                          type="range"
                          min="1.0"
                          max="2.0"
                          step="0.1"
                          value={config.advancedConfig.modelMemoryOverhead}
                          onChange={(e) =>
                            handleAdvancedConfigChange("modelMemoryOverhead", parseFloat(e.target.value))
                          }
                          className="w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-gray-400 mt-1">
                          Multiplier for model weight memory footprint (1.0-2.0)
                        </p>
                      </div>

                      {/* Hypervisor Reserve GB */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-sm font-medium text-gray-300">
                            Hypervisor Reserve (GB)
                          </label>
                          <span className="text-sm text-green-500 font-mono">
                            {config.advancedConfig.hypervisorReserveGb.toFixed(1)} GB
                          </span>
                        </div>
                        <input
                          type="range"
                          min="0.0"
                          max="10.0"
                          step="0.5"
                          value={config.advancedConfig.hypervisorReserveGb}
                          onChange={(e) =>
                            handleAdvancedConfigChange("hypervisorReserveGb", parseFloat(e.target.value))
                          }
                          className="w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-gray-400 mt-1">
                          GPU memory reserved for hypervisor layer (0.0-10.0 GB)
                        </p>
                      </div>

                      {/* CUDA Memory Overhead */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-sm font-medium text-gray-300">
                            CUDA Memory Overhead
                          </label>
                          <span className="text-sm text-green-500 font-mono">
                            {config.advancedConfig.cudaMemoryOverhead.toFixed(2)}x
                          </span>
                        </div>
                        <input
                          type="range"
                          min="1.0"
                          max="1.5"
                          step="0.05"
                          value={config.advancedConfig.cudaMemoryOverhead}
                          onChange={(e) =>
                            handleAdvancedConfigChange("cudaMemoryOverhead", parseFloat(e.target.value))
                          }
                          className="w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-gray-400 mt-1">
                          CUDA runtime memory overhead multiplier (1.0-1.5)
                        </p>
                      </div>

                      {/* vCPU per GPU */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-sm font-medium text-gray-300">
                            vCPUs per GPU
                          </label>
                          <span className="text-sm text-green-500 font-mono">
                            {config.advancedConfig.vcpuPerGpu}
                          </span>
                        </div>
                        <input
                          type="range"
                          min="1"
                          max="32"
                          step="1"
                          value={config.advancedConfig.vcpuPerGpu}
                          onChange={(e) =>
                            handleAdvancedConfigChange("vcpuPerGpu", parseInt(e.target.value))
                          }
                          className="w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-gray-400 mt-1">
                          Number of vCPUs to allocate per GPU (1-32)
                        </p>
                      </div>

                      {/* RAM GB per vCPU */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-sm font-medium text-gray-300">
                            RAM per vCPU (GB)
                          </label>
                          <span className="text-sm text-green-500 font-mono">
                            {config.advancedConfig.ramGbPerVcpu} GB
                          </span>
                        </div>
                        <input
                          type="range"
                          min="2"
                          max="32"
                          step="1"
                          value={config.advancedConfig.ramGbPerVcpu}
                          onChange={(e) =>
                            handleAdvancedConfigChange("ramGbPerVcpu", parseInt(e.target.value))
                          }
                          className="w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <p className="text-xs text-gray-400 mt-1">
                          GB of system RAM to allocate per vCPU (2-32 GB)
                        </p>
                      </div>

                      {/* Reset to Defaults Button */}
                      <button
                        type="button"
                        onClick={() =>
                          setConfig((prev) => ({
                            ...prev,
                            advancedConfig: {
                              modelMemoryOverhead: 1.3,
                              hypervisorReserveGb: 3.0,
                              cudaMemoryOverhead: 1.2,
                              vcpuPerGpu: 8,
                              ramGbPerVcpu: 8,
                            },
                          }))
                        }
                        className="w-full px-4 py-2 bg-neutral-700 text-white rounded-lg hover:bg-neutral-600 transition-colors"
                      >
                        Reset to Defaults
                      </button>
                    </div>
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