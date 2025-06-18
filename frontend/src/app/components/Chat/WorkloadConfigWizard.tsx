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
  performanceLevel: string;
  selectedGPU: string;
  framework: string;
  priority: string;
  // RAG-specific fields
  embeddingModel: string;
  retrievalModel: string;
  inferenceModel: string;
  // Inference-specific fields
  inferenceBatchSize: string;
  inferenceConcurrency: string;
  // Training-specific fields
  trainingEpochs: string;
  datasetSize: string;
  trainingModel: string;
  optimizer: string;
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
    performanceLevel: "",
    selectedGPU: "",
    framework: "",
    priority: "",
    // RAG-specific fields
    embeddingModel: "",
    retrievalModel: "",
    inferenceModel: "",
    // Inference-specific fields
    inferenceBatchSize: "",
    inferenceConcurrency: "",
    // Training-specific fields
    trainingEpochs: "",
    datasetSize: "",
    trainingModel: "",
    optimizer: "",
  });

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  const workloadTypes = [
    { value: "training", label: "AI Model Training", desc: "Training neural networks and deep learning models" },
    { value: "inference", label: "AI Inference", desc: "Running predictions and serving trained models" },
    { value: "fine-tuning", label: "Model Fine-tuning", desc: "Adapting pre-trained models for specific tasks" },
    { value: "rag", label: "RAG (Retrieval-Augmented Generation)", desc: "Document search and generation workflows" },
    { value: "embedding", label: "Embedding Generation", desc: "Creating vector embeddings for similarity search" },
    { value: "multi-modal", label: "Multi-modal AI", desc: "Vision, text, and audio processing combined" }
  ];

  const modelSizes = [
    { value: "small", label: "Small (< 7B parameters)", desc: "Lightweight models, fast inference" },
    { value: "medium", label: "Medium (7B-30B parameters)", desc: "Balanced performance and speed" },
    { value: "large", label: "Large (30B-70B parameters)", desc: "High-quality results, more compute" },
    { value: "xlarge", label: "Extra Large (70B+ parameters)", desc: "State-of-the-art performance" }
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
    { value: "llama-3-8b", label: "Llama 3-8B Instruct" },
    { value: "llama-3-70b", label: "Llama 3-70B Instruct" },
    { value: "llama-3.1-8b", label: "Llama 3.1-8B Instruct" },
    { value: "llama-3.1-70b", label: "Llama 3.1-70B Instruct" },
    { value: "llama-3.3-70b", label: "Llama 3.3-70B Instruct" },
    { value: "mistral-7b", label: "Mistral-7B Instruct" },
    { value: "mixtral-8x7b", label: "Mixtral-8x7B Instruct" },
    { value: "codellama-13b", label: "CodeLlama-13B Instruct" },
    { value: "falcon-40b", label: "Falcon-40B Instruct" },
    { value: "gemma-7b", label: "Gemma-7B" },
    { value: "phi-3-mini", label: "Phi-3 Mini (3.8B)" },
    { value: "phi-3-small", label: "Phi-3 Small (7B)" },
    { value: "custom", label: "Other/Custom Model" },
    { value: "unknown", label: "I don't know the exact model" }
  ];

  const frameworks = [
    { value: "pytorch", label: "PyTorch" },
    { value: "tensorflow", label: "TensorFlow" },
    { value: "huggingface", label: "Hugging Face" },
    { value: "nemo", label: "NVIDIA NeMo" },
    { value: "triton", label: "NVIDIA Triton" },
    { value: "other", label: "Other" }
  ];

  const embeddingModels = [
    { value: "text-embedding-ada-002", label: "OpenAI text-embedding-ada-002" },
    { value: "e5-large", label: "E5-Large" },
    { value: "bge-large", label: "BGE-Large" },
    { value: "gte-large", label: "GTE-Large" },
    { value: "all-mpnet-base-v2", label: "All-MPNet-Base-v2" },
    { value: "custom", label: "Custom Embedding Model" }
  ];

  const retrievalModels = [
    { value: "bge-reranker-large", label: "BGE Reranker Large" },
    { value: "cross-encoder-ms-marco", label: "Cross-Encoder MS-MARCO" },
    { value: "colbert-v2", label: "ColBERT v2" },
    { value: "dense-passage-retrieval", label: "Dense Passage Retrieval" },
    { value: "none", label: "No Retrieval Model (Direct Vector Search)" }
  ];

  const optimizers = [
    { value: "adamw", label: "AdamW" },
    { value: "adam", label: "Adam" },
    { value: "sgd", label: "SGD with Momentum" },
    { value: "rmsprop", label: "RMSprop" },
    { value: "lion", label: "Lion" }
  ];

  const handleInputChange = (field: keyof WorkloadConfig, value: string) => {
    setConfig((prev: WorkloadConfig) => ({ ...prev, [field]: value }));
  };

  const handleGPUSelection = (gpuType: string) => {
    setConfig((prev: WorkloadConfig) => ({ 
      ...prev, 
      selectedGPU: prev.selectedGPU === gpuType ? "" : gpuType 
    }));
  };

  const hasSelectedGPU = (): boolean => {
    return config.selectedGPU !== "";
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
    
    // Model size (for backward compatibility)
    if (config.modelSize && config.workloadType !== 'rag' && config.workloadType !== 'inference' && config.workloadType !== 'training') {
      const sizeLabel = modelSizes.find(s => s.value === config.modelSize)?.label || config.modelSize;
      parts.push(`with ${sizeLabel.toLowerCase()}`);
    }
    
    // Single GPU Selection
    if (config.selectedGPU) {
      const gpuInfo = availableGPUInventory.find(g => g.value === config.selectedGPU);
      parts.push(`using available GPU inventory: 1x ${gpuInfo?.label || config.selectedGPU}`);
    }
    
    // Workload-specific configurations
    if (config.workloadType === 'rag') {
      const ragDetails = [];
      if (config.embeddingModel) {
        ragDetails.push(`embedding model: ${config.embeddingModel}`);
      }
      if (config.retrievalModel) {
        ragDetails.push(`retrieval model: ${config.retrievalModel}`);
      }
      if (config.inferenceModel) {
        ragDetails.push(`inference model: ${config.inferenceModel}`);
      }
      if (ragDetails.length > 0) {
        parts.push(`with ${ragDetails.join(', ')}`);
      }
    } else if (config.workloadType === 'inference') {
      const inferenceDetails = [];
      if (config.specificModel && config.specificModel !== 'unknown') {
        const modelLabel = specificModels.find(m => m.value === config.specificModel)?.label || config.specificModel;
        inferenceDetails.push(`running ${modelLabel}`);
      }
      if (config.inferenceBatchSize) {
        inferenceDetails.push(`batch size: ${config.inferenceBatchSize}`);
      }
      if (config.inferenceConcurrency) {
        inferenceDetails.push(`concurrency: ${config.inferenceConcurrency}`);
      }
      if (inferenceDetails.length > 0) {
        parts.push(inferenceDetails.join(' with '));
      }
    } else if (config.workloadType === 'training' || config.workloadType === 'fine-tuning') {
      const trainingDetails = [];
      if (config.trainingModel) {
        trainingDetails.push(`model: ${config.trainingModel}`);
      }
      if (config.trainingEpochs) {
        trainingDetails.push(`${config.trainingEpochs} epochs`);
      }
      if (config.datasetSize) {
        trainingDetails.push(`dataset size: ${config.datasetSize}`);
      }
      if (config.optimizer) {
        trainingDetails.push(`optimizer: ${config.optimizer}`);
      }
      if (trainingDetails.length > 0) {
        parts.push(`with ${trainingDetails.join(', ')}`);
      }
    } else {
      // For other workload types, use the original logic
    if (config.specificModel && config.specificModel !== 'unknown') {
      const modelLabel = specificModels.find(m => m.value === config.specificModel)?.label || config.specificModel;
      parts.push(`running ${modelLabel}`);
      }
    }
    
    // Performance requirements (for non-RAG workloads)
    if (config.performanceLevel && config.workloadType !== 'rag') {
      const perfLabel = performanceLevels.find(p => p.value === config.performanceLevel)?.label || config.performanceLevel;
      parts.push(`requiring ${perfLabel.toLowerCase()} performance`);
    }
    
    // Memory and batch size (general requirements)
    const requirements = [];
    if (config.memoryRequirement) {
      requirements.push(`${config.memoryRequirement} memory`);
    }
    if (config.batchSize && config.workloadType !== 'inference') {
      requirements.push(`batch size of ${config.batchSize}`);
    }
    
    if (requirements.length > 0) {
      parts.push(`with ${requirements.join(', ')}`);
    }
    
    // Framework
    if (config.framework && config.framework !== 'other') {
      parts.push(`using ${config.framework}`);
    }
    
    // Priority
    if (config.priority) {
      if (config.priority === 'cost') {
        parts.push(`optimizing for cost efficiency`);
      } else if (config.priority === 'performance') {
        parts.push(`prioritizing maximum performance`);
      } else if (config.priority === 'balanced') {
        parts.push(`with balanced cost and performance`);
      }
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
      performanceLevel: "",
      selectedGPU: "",
      framework: "",
      priority: "",
      // RAG-specific fields
      embeddingModel: "",
      retrievalModel: "",
      inferenceModel: "",
      // Inference-specific fields
      inferenceBatchSize: "",
      inferenceConcurrency: "",
      // Training-specific fields
      trainingEpochs: "",
      datasetSize: "",
      trainingModel: "",
      optimizer: "",
    });
    setCurrentStep(1);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return config.workloadType && hasSelectedGPU();
      case 2:
        // Different validation based on workload type
        if (config.workloadType === 'rag') {
          return config.embeddingModel && config.inferenceModel;
        } else if (config.workloadType === 'inference') {
          return config.specificModel && config.inferenceBatchSize;
        } else if (config.workloadType === 'training' || config.workloadType === 'fine-tuning') {
          return config.trainingModel && config.trainingEpochs;
        } else {
        return (config.specificModel || config.modelSize) && config.performanceLevel;
        }
      case 3:
        return true; // Final step, can always proceed
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

              <div>
                <h3 className="text-lg font-semibold text-white mb-4">What GPU do you have available?</h3>
                <p className="text-sm text-gray-400 mb-4">Select one GPU from your inventory. The system will determine if multi-GPU setup is needed.</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
                  {availableGPUInventory.map((gpu) => {
                    const isSelected = config.selectedGPU === gpu.value;
                    
                    return (
                      <button
                        key={gpu.value}
                        onClick={() => handleGPUSelection(gpu.value)}
                        className={`p-4 rounded-lg border text-left transition-all ${
                          isSelected
                            ? "border-green-500 bg-green-900/20 ring-2 ring-green-500"
                            : "border-neutral-600 bg-neutral-800 hover:border-green-600"
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-white flex items-center">
                              {gpu.label}
                              {isSelected && (
                                <svg className="w-5 h-5 ml-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                            <div className="text-sm text-gray-400 mt-1">{gpu.desc}</div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Selected GPU Summary */}
                {config.selectedGPU && (
                  <div className="p-4 bg-green-900/20 border border-green-700 rounded-lg">
                    <h4 className="text-sm font-medium text-green-300 mb-2">Selected GPU:</h4>
                    <div className="flex items-center justify-between">
                      <span className="text-white font-medium">
                        {availableGPUInventory.find(g => g.value === config.selectedGPU)?.label || config.selectedGPU}
                      </span>
                      <span className="text-xs text-gray-400">
                        The system will determine if this GPU is sufficient or if multiple GPUs are needed
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Performance Requirements */}
          {currentStep === 2 && (
            <div className="space-y-6">
              {/* RAG Workload Configuration */}
              {config.workloadType === 'rag' && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">RAG Pipeline Configuration</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Embedding Model</label>
                      <select
                        value={config.embeddingModel}
                        onChange={(e) => handleInputChange("embeddingModel", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select embedding model</option>
                        {embeddingModels.map((model) => (
                          <option key={model.value} value={model.value}>{model.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Retrieval Model (Optional)</label>
                      <select
                        value={config.retrievalModel}
                        onChange={(e) => handleInputChange("retrievalModel", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select retrieval/reranking model</option>
                        {retrievalModels.map((model) => (
                          <option key={model.value} value={model.value}>{model.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Inference Model</label>
                      <select
                        value={config.inferenceModel}
                        onChange={(e) => handleInputChange("inferenceModel", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select inference model</option>
                        {specificModels.map((model) => (
                          <option key={model.value} value={model.value}>{model.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Inference Workload Configuration */}
              {config.workloadType === 'inference' && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Inference Configuration</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Model Name</label>
                      <select
                        value={config.specificModel}
                        onChange={(e) => handleInputChange("specificModel", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select model for inference</option>
                        {specificModels.map((model) => (
                          <option key={model.value} value={model.value}>{model.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Batch Size</label>
                      <select
                        value={config.inferenceBatchSize}
                        onChange={(e) => handleInputChange("inferenceBatchSize", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select batch size</option>
                        <option value="1">1 (Real-time inference)</option>
                        <option value="4">4 (Small batch)</option>
                        <option value="8">8 (Medium batch)</option>
                        <option value="16">16 (Large batch)</option>
                        <option value="32">32 (Very large batch)</option>
                        <option value="64+">64+ (Bulk processing)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Concurrency Level</label>
                      <select
                        value={config.inferenceConcurrency}
                        onChange={(e) => handleInputChange("inferenceConcurrency", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select concurrency level</option>
                        <option value="low">Low (1-5 concurrent requests)</option>
                        <option value="medium">Medium (5-20 concurrent requests)</option>
                        <option value="high">High (20-50 concurrent requests)</option>
                        <option value="very-high">Very High (50+ concurrent requests)</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Training/Fine-tuning Workload Configuration */}
              {(config.workloadType === 'training' || config.workloadType === 'fine-tuning') && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">Training Configuration</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Model</label>
                      <select
                        value={config.trainingModel}
                        onChange={(e) => handleInputChange("trainingModel", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select model to train</option>
                        {specificModels.map((model) => (
                          <option key={model.value} value={model.value}>{model.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Number of Epochs</label>
                      <select
                        value={config.trainingEpochs}
                        onChange={(e) => handleInputChange("trainingEpochs", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select number of epochs</option>
                        <option value="1-5">1-5 epochs (Quick fine-tuning)</option>
                        <option value="5-10">5-10 epochs (Standard training)</option>
                        <option value="10-20">10-20 epochs (Extended training)</option>
                        <option value="20-50">20-50 epochs (Deep training)</option>
                        <option value="50+">50+ epochs (Extensive training)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Dataset Size</label>
                      <select
                        value={config.datasetSize}
                        onChange={(e) => handleInputChange("datasetSize", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select dataset size</option>
                        <option value="small">Small (&lt;10K samples)</option>
                        <option value="medium">Medium (10K-100K samples)</option>
                        <option value="large">Large (100K-1M samples)</option>
                        <option value="very-large">Very Large (1M+ samples)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Optimizer</label>
                      <select
                        value={config.optimizer}
                        onChange={(e) => handleInputChange("optimizer", e.target.value)}
                        className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                      >
                        <option value="">Select optimizer</option>
                        {optimizers.map((opt) => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Default configuration for other workload types */}
              {!['rag', 'inference', 'training', 'fine-tuning'].includes(config.workloadType) && (
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
                    <label className="block text-sm font-medium text-gray-300 mb-2">Performance Level</label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {performanceLevels.map((level) => (
                        <button
                          key={level.value}
                          onClick={() => handleInputChange("performanceLevel", level.value)}
                          className={`p-3 rounded-lg border text-center transition-all ${
                            config.performanceLevel === level.value
                              ? "border-green-500 bg-green-900/20 text-white"
                              : "border-neutral-600 bg-neutral-800 text-gray-300 hover:border-green-600"
                          }`}
                        >
                          <div className="font-medium">{level.label}</div>
                          <div className="text-xs text-gray-400 mt-1">{level.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              )}
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                  <select
                    value={config.priority}
                    onChange={(e) => handleInputChange("priority", e.target.value)}
                    className="w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white"
                  >
                    <option value="">Select priority</option>
                    <option value="cost">Cost Efficiency</option>
                    <option value="balanced">Balanced</option>
                    <option value="performance">Maximum Performance</option>
                  </select>
                </div>
              </div>

              {/* Query Preview */}
              <div className="mt-6 p-4 bg-neutral-800 border border-neutral-600 rounded-lg">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Generated Query Preview:</h4>
                <p className="text-white text-sm italic">"{generateQuery()}"</p>
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