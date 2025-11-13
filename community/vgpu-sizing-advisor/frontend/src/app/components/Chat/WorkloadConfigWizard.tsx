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
    embeddingModel: "nvidia/nvolveqa-embed-large-1B",
    gpuInventory: { "DC": 1 },
    precision: "fp16",
    vectorDimension: "1024",  // Default to 1024 (matches default embedding model)
    numberOfVectors: "10000", // Default to 10,000
    advancedConfig: {
      modelMemoryOverhead: 1.3,
      cudaMemoryOverhead: 1.2,
      vcpuPerGpu: 8,
      ramGbPerVcpu: 8,
    },
  });

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = config.workloadType === 'rag' ? 4 : 3;
  const [dynamicModels, setDynamicModels] = useState<Array<{ value: string; label: string; modelTag: string }>>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [showAdvancedConfig, setShowAdvancedConfig] = useState(false);
  const [showPromptTooltip, setShowPromptTooltip] = useState(false);
  const [showResponseTooltip, setShowResponseTooltip] = useState(false);

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
    { value: "nvidia/nvolveqa-embed-large-1B", label: "nvidia/nvolveqa-embed-large-1B", desc: "1B parameter embedding model", dimension: 1024 },
    { value: "text-embedding-ada-002-350M", label: "text-embedding-ada-002-350M", desc: "350M parameter OpenAI embedding model", dimension: 1536 },
    { value: "nvidia/nvolveqa-embed-base-400M", label: "nvidia/nvolveqa-embed-base-400M", desc: "400M parameter embedding model", dimension: 768 },
    { value: "nvidia/nemo-embed-qa-200M", label: "nvidia/nemo-embed-qa-200M", desc: "200M parameter QA embedding model", dimension: 768 },
    { value: "all-MiniLM-L6-v2-80M", label: "all-MiniLM-L6-v2-80M", desc: "80M parameter compact embedding model", dimension: 384 },
    { value: "llama-3-2-nv-embedqa-1b-v2", label: "llama-3-2-nv-embedqa-1b-v2", desc: "Llama 3.2 based embedding model", dimension: 1024 }
  ];

  const performanceLevels = [
    { value: "basic", label: "Basic", desc: "Cost-optimized, adequate performance" },
    { value: "standard", label: "Standard", desc: "Good balance of cost and performance" },
    { value: "high", label: "High Performance", desc: "Optimized for speed and throughput" },
    { value: "maximum", label: "Maximum", desc: "Best possible performance, premium cost" }
  ];

  const availableGPUInventory = [
    { value: "DC", label: "NVIDIA RTX Pro 6000 BSE", desc: "96GB GDDR7 with ECC, Blackwell, passive‑cooled dual‑slot PCIe Gen5 – Enterprise AI/graphics, scientific computing & virtual workstations" },
    { value: "l40s", label: "NVIDIA L40S", desc: "48GB GDDR6 with ECC, Ada Lovelace, 350W - ML training & inference + virtual workstations" },
    { value: "l40", label: "NVIDIA L40", desc: "48GB GDDR6 with ECC, Ada Lovelace - Virtual workstations & compute workloads" },
    { value: "l4", label: "NVIDIA L4", desc: "24GB GDDR6 with ECC, Ada Lovelace, 72W - AI inference, small model training & 3D graphics" },
    { value: "a40", label: "NVIDIA A40", desc: "48GB GDDR6 with ECC, Ampere, 300W - 3D design & mixed virtual workstation workloads" },
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
    { value: "fp8", label: "FP8", desc: "8-bit floating point - Higher performance with good accuracy" },
    { value: "fp4", label: "FP4", desc: "4-bit floating point - Maximum performance, lower accuracy" },
  ];

  const handleInputChange = (field: keyof WorkloadConfig, value: string) => {
    setConfig((prev: WorkloadConfig) => {
      const newConfig = { ...prev, [field]: value };
      
      // Auto-set vector dimension when embedding model changes
      if (field === 'embeddingModel') {
        const selectedModel = embeddingModels.find(m => m.value === value);
        if (selectedModel && selectedModel.dimension) {
          newConfig.vectorDimension = selectedModel.dimension.toString();
        }
      }
      
      return newConfig;
    });
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

  // Map model size categories to actual models for vLLM deployment
  const getDefaultModelForSize = (sizeCategory: string): { value: string; label: string; modelTag: string } => {
    switch (sizeCategory) {
      case 'small':
        // Use a small, fast model for < 7B
        return { value: "mistral-7b", label: "Mistral-7B", modelTag: "mistralai/Mistral-7B-Instruct-v0.3" };
      case 'medium':
        // Use a medium model for 7B-30B
        return { value: "llama-3.1-8b", label: "Llama-3.1-8B", modelTag: "meta-llama/Llama-3.1-8B-Instruct" };
      case 'large':
        // Use a large model for 40B-70B
        return { value: "llama-3.1-70b", label: "Llama-3.1-70B", modelTag: "meta-llama/Llama-3.3-70B-Instruct" };
      case 'xlarge':
        // Use an extra large model for 70B+
        return { value: "falcon-180b", label: "Falcon-180B", modelTag: "tiiuae/falcon-180B" };
      default:
        // Default to a small model
        return { value: "mistral-7b", label: "Mistral-7B", modelTag: "mistralai/Mistral-7B-Instruct-v0.3" };
    }
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
      // Default GPU (RTX Pro 6000 BSE) if no GPU is selected
      parts.push(`using available GPU inventory: 1x NVIDIA RTX Pro 6000 BSE`);
    }
    
    // Specific Model - use full HuggingFace model tag
    if (config.specificModel && config.specificModel !== 'unknown') {
      const modelTag = specificModels.find(m => m.value === config.specificModel)?.modelTag || config.specificModel;
      parts.push(`running ${modelTag}`);
    } else if (config.specificModel === 'unknown' && config.modelSize) {
      // If "unknown" is selected, use the default model for the selected size category
      const defaultModel = getDefaultModelForSize(config.modelSize);
      parts.push(`running ${defaultModel.modelTag}`);
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
    // Determine the model tag to use
    let modelTagToUse = null;
    if (config.specificModel && config.specificModel !== 'unknown') {
      modelTagToUse = specificModels.find(m => m.value === config.specificModel)?.modelTag || null;
    } else if (config.specificModel === 'unknown' && config.modelSize) {
      // Use default model for the size category
      modelTagToUse = getDefaultModelForSize(config.modelSize).modelTag;
    }
    
    const structuredConfig = {
      workloadType: config.workloadType,
      specificModel: config.specificModel,
      modelTag: modelTagToUse,
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
      selectedGPU: Object.keys(config.gpuInventory)[0] || 'DC',
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
      embeddingModel: "nvidia/nvolveqa-embed-large-1B",
      gpuInventory: { "DC": 1 },
      precision: "fp16",
      vectorDimension: "1024",  // Default to 1024 (matches default embedding model)
      numberOfVectors: "10000", // Default to 10,000
      advancedConfig: {
        modelMemoryOverhead: 1.3,
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
        // For RAG workloads on step 3, require embedding model selection
        if (config.workloadType === 'rag') {
          return config.embeddingModel !== '';
        }
        // For non-RAG, step 3 is GPU selection (optional)
        return true;
      case 4:
        return true; // GPU selection is optional for RAG workloads
      default:
        return false;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-neutral-900 rounded-lg border border-neutral-700 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
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

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Precision</label>
                      <select
                        value={config.precision}
                        onChange={(e) => handleInputChange("precision", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
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

          {/* Step 3: RAG Configuration (only for RAG workloads) */}
          {currentStep === 3 && config.workloadType === 'rag' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">RAG Configuration</h3>
                <p className="text-sm text-gray-400 mb-6">
                  Configure retrieval-augmented generation components for your knowledge base
                </p>

                {/* Embedding Model Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-2">Embedding Model</label>
                  <select
                    value={config.embeddingModel}
                    onChange={(e) => handleInputChange("embeddingModel", e.target.value)}
                    className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                  >
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

                {/* Vector Database Configuration */}
                <div className="p-4 bg-neutral-800/50 rounded-lg border border-neutral-700">
                  <h4 className="text-md font-semibold text-white mb-4">Vector Database Configuration</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Vector Dimension (auto-set) */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Vector Dimension</label>
                      <input
                        type="text"
                        value={config.vectorDimension || ""}
                        disabled
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-gray-400 cursor-not-allowed"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Auto-set from embedding model
                      </p>
                    </div>

                    {/* Vector Database Size */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Knowledge Base Size</label>
                      <select
                        value={config.numberOfVectors || "10000"}
                        onChange={(e) => handleInputChange("numberOfVectors", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="10000">Small (~10K documents)</option>
                        <option value="100000">Medium (~100K documents)</option>
                        <option value="1000000">Large (~1M documents)</option>
                        <option value="10000000">Extra Large (~10M documents)</option>
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        Total vectors in your knowledge base
                      </p>
                    </div>
                  </div>

                  {/* Vector DB Size Info */}
                  <div className="mt-4 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div className="text-xs text-blue-300">
                        <span className="font-medium">Estimated Vector Index Memory: </span>
                        {config.numberOfVectors === "10000" && "~20 MB"}
                        {config.numberOfVectors === "100000" && "~200 MB"}
                        {config.numberOfVectors === "1000000" && "~2 GB"}
                        {config.numberOfVectors === "10000000" && "~20 GB"}
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* Step 3/4: Additional Requirements (GPU Selection) */}
          {currentStep === (config.workloadType === 'rag' ? 4 : 3) && (
            <div className="space-y-5">
              <h3 className="text-lg font-semibold text-white mb-3">Additional Requirements</h3>
              
              {/* GPU Selection Section */}
              <div>
                <h4 className="text-sm font-medium text-white mb-2">GPU Selection</h4>
                
                <select
                  value={Object.keys(config.gpuInventory)[0] || "DC"}
                  onChange={(e) => {
                    // Clear existing inventory and set the new one
                    setConfig(prev => ({
                      ...prev,
                      gpuInventory: e.target.value ? { [e.target.value]: 1 } : { "DC": 1 }
                    }));
                  }}
                  className="w-full px-3 py-2 rounded-md bg-neutral-800 border border-neutral-700 text-white text-sm focus:outline-none focus:ring-1 focus:ring-green-500 focus:border-green-500"
                >
                  {availableGPUInventory.map((gpu) => (
                    <option key={gpu.value} value={gpu.value}>
                      {gpu.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">
                    Prompt Size (
                    <span 
                      className="relative text-green-500 underline decoration-dotted"
                      onMouseEnter={() => setShowPromptTooltip(true)}
                      onMouseLeave={() => setShowPromptTooltip(false)}
                    >
                      tokens
                      {showPromptTooltip && (
                        <span className="absolute left-0 top-full mt-2 w-64 p-3 bg-neutral-800 border border-neutral-600 rounded-lg shadow-lg text-xs text-gray-300 font-normal z-50 leading-relaxed">
                          Prompt tokens are the input you send to the AI model. This includes your question, context, and any instructions. More tokens = longer inputs you can process. Typical: 1024-4096 tokens (~750-3000 words).
                        </span>
                      )}
                    </span>
                    )
                  </label>
                  <input
                    type="number"
                    value={config.promptSize}
                    onChange={(e) => handleInputChange("promptSize", e.target.value)}
                    placeholder="e.g., 1024"
                    min="256"
                    max="32768"
                    step="256"
                    className="w-full px-3 py-2 rounded-md bg-neutral-800 border border-neutral-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-green-500 focus:border-green-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Maximum input prompt length
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">
                    Response Size (
                    <span 
                      className="relative text-green-500 underline decoration-dotted"
                      onMouseEnter={() => setShowResponseTooltip(true)}
                      onMouseLeave={() => setShowResponseTooltip(false)}
                    >
                      tokens
                      {showResponseTooltip && (
                        <span className="absolute left-0 top-full mt-2 w-64 p-3 bg-neutral-800 border border-neutral-600 rounded-lg shadow-lg text-xs text-gray-300 font-normal z-50 leading-relaxed">
                          Response tokens are the AI-generated output. This is the length of answers the model will generate. More tokens = longer, more detailed responses. Typical: 256-1024 tokens (~200-750 words).
                        </span>
                      )}
                    </span>
                    )
                  </label>
                  <input
                    type="number"
                    value={config.responseSize}
                    onChange={(e) => handleInputChange("responseSize", e.target.value)}
                    placeholder="e.g., 256"
                    min="128"
                    max="8192"
                    step="128"
                    className="w-full px-3 py-2 rounded-md bg-neutral-800 border border-neutral-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-green-500 focus:border-green-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Maximum response length
                  </p>
                </div>
              </div>

              {/* Advanced Configuration Dropdown */}
              <div className="mt-6">
                <button
                  type="button"
                  onClick={() => setShowAdvancedConfig(!showAdvancedConfig)}
                  className="flex items-center gap-2 py-2 hover:opacity-80 transition-opacity"
                >
                  <svg
                    className={`w-4 h-4 text-gray-500 transition-transform ${showAdvancedConfig ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                  <span className="text-sm text-gray-400">Advanced Configuration</span>
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
                      <div className="mt-6 pt-4 border-t border-neutral-700">
                        <button
                          type="button"
                          onClick={() =>
                            setConfig((prev) => ({
                              ...prev,
                              advancedConfig: {
                                modelMemoryOverhead: 1.3,
                                cudaMemoryOverhead: 1.2,
                                vcpuPerGpu: 8,
                                ramGbPerVcpu: 8,
                              },
                            }))
                          }
                          className="w-full px-4 py-2 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg text-sm transition-colors"
                        >
                          Reset to Defaults
                        </button>
                      </div>
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
                onClick={() => {
                  // For non-RAG on step 3 (GPU selection), go back to step 2 directly
                  if (currentStep === 3 && config.workloadType !== 'rag') {
                    setCurrentStep(2);
                  } else {
                    setCurrentStep(currentStep - 1);
                  }
                }}
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