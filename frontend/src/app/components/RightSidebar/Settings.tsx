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
import { useSettings } from "../../context/SettingsContext";

export default function Settings() {
  const {
    temperature,
    topP,
    vdbTopK,
    rerankerTopK,
    useGuardrails,
    includeCitations,
    setTemperature,
    setTopP,
    setVdbTopK,
    setRerankerTopK,
    setUseGuardrails,
    setIncludeCitations,
  } = useSettings();

  const [expandedSections, setExpandedSections] = useState({
    ragConfig: true,
    outputPrefs: false,
  });

  const [vdbTopKInput, setVdbTopKInput] = useState(vdbTopK.toString());
  const [rerankerTopKInput, setRerankerTopKInput] = useState(
    rerankerTopK.toString()
  );

  const toggleSection = (section: "ragConfig" | "outputPrefs") => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleVdbTopKChange = (value: string) => {
    setVdbTopKInput(value);
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue > 0) {
      setVdbTopK(numValue);
    }
  };

  const handleRerankerTopKChange = (value: string) => {
    setRerankerTopKInput(value);
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue > 0) {
      setRerankerTopK(numValue);
    }
  };

  // Update input values when context values change
  useEffect(() => {
    setVdbTopKInput(vdbTopK.toString());
    setRerankerTopKInput(rerankerTopK.toString());
  }, [vdbTopK, rerankerTopK]);

  return (
    <div className="text-white">
      <div className="mb-8">
        <button
          onClick={() => toggleSection("ragConfig")}
          className="mb-4 flex w-full items-center justify-between text-sm font-medium hover:text-gray-300"
        >
          <span>RAG Configuration Parameters</span>
          <span className="transform transition-transform duration-200">
            {expandedSections.ragConfig ? "▼" : "▶"}
          </span>
        </button>

        <div
          className={`space-y-6 transition-all duration-200 ${
            expandedSections.ragConfig ? "block" : "hidden"
          }`}
        >
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm">Temperature</label>
              <input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-16 rounded bg-neutral-800 px-2 py-1 text-sm"
                step="0.1"
                min="0"
                max="1"
              />
            </div>
            <input
              type="range"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full accent-[var(--nv-green)]"
              step="0.1"
              min="0"
              max="1"
            />
            <p className="mt-1 text-xs text-gray-400">
              Controls the creativity of the model. Higher values enable more
              creative outputs, suitable for tasks such as creative writing. A
              value within the [0.5, 0.8] range is a good starting point for
              experimentation.
            </p>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm">Top P</label>
              <input
                type="number"
                value={topP}
                onChange={(e) => setTopP(Number(e.target.value))}
                className="w-16 rounded bg-neutral-800 px-2 py-1 text-sm"
                step="0.1"
                min="0"
                max="1"
              />
            </div>
            <input
              type="range"
              value={topP}
              onChange={(e) => setTopP(Number(e.target.value))}
              className="w-full accent-[var(--nv-green)]"
              step="0.1"
              min="0"
              max="1"
            />
            <p className="mt-1 text-xs text-gray-400">
              The number of times the entire dataset is propagated through the
              network during training.
            </p>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm">Vector Database Top K</label>
              <input
                type="number"
                value={vdbTopK}
                onChange={(e) => handleVdbTopKChange(e.target.value)}
                className={`w-24 rounded bg-neutral-800 px-3 py-2 text-sm ${
                  vdbTopK < rerankerTopK ? "border border-red-500" : ""
                }`}
                min="1"
                aria-label="Vector Database Top K"
              />
            </div>
            <p className="mt-1 text-xs text-gray-400">
              The number of top-ranked vectors retrieved from a vector database
              (VDB) during inference. Must be greater than or equal to Reranker
              Top K.
            </p>
            {vdbTopK !== parseInt(vdbTopKInput, 10) &&
              !isNaN(parseInt(vdbTopKInput, 10)) && (
                <p className="mt-1 text-xs text-amber-400">
                  Value adjusted to maintain VDB Top K ≥ Reranker Top K
                  constraint.
                </p>
              )}
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm">Reranker Top K</label>
              <input
                type="number"
                value={rerankerTopK}
                onChange={(e) => handleRerankerTopKChange(e.target.value)}
                className={`w-24 rounded bg-neutral-800 px-3 py-2 text-sm ${
                  rerankerTopK > vdbTopK ? "border border-red-500" : ""
                }`}
                min="1"
                aria-label="Reranker Top K"
              />
            </div>
            <p className="mt-1 text-xs text-gray-400">
              The number of top-ranked documents or knowledge chunks retrieved
              from a retriever model before passing them to the AI for response
              generation. Must be less than or equal to VDB Top K.
            </p>
            {rerankerTopK !== parseInt(rerankerTopKInput, 10) &&
              !isNaN(parseInt(rerankerTopKInput, 10)) && (
                <p className="mt-1 text-xs text-amber-400">
                  Value adjusted to maintain VDB Top K ≥ Reranker Top K
                  constraint.
                </p>
              )}
          </div>
        </div>
      </div>

      <div>
        <button
          onClick={() => toggleSection("outputPrefs")}
          className="mb-4 flex w-full items-center justify-between text-sm font-medium hover:text-gray-300"
        >
          <span>Output Preferences</span>
          <span className="transform transition-transform duration-200">
            {expandedSections.outputPrefs ? "▼" : "▶"}
          </span>
        </button>
        <div
          className={`space-y-4 transition-all duration-200 ${
            expandedSections.outputPrefs ? "block" : "hidden"
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Guardrails</p>
              <p className="text-xs text-gray-400">
                Apply guardrails to every response
              </p>
            </div>
            <button
              onClick={() => setUseGuardrails(!useGuardrails)}
              className={`h-6 w-11 rounded-full transition-colors ${useGuardrails ? "bg-[var(--nv-green)]" : "bg-neutral-800"} relative`}
            >
              <span
                className={`block h-4 w-4 rounded-full bg-white transition-transform ${
                  useGuardrails ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Citations</p>
              <p className="text-xs text-gray-400">
                Include citations from sources
              </p>
            </div>
            <button
              onClick={() => setIncludeCitations(!includeCitations)}
              className={`h-6 w-11 rounded-full transition-colors ${includeCitations ? "bg-[var(--nv-green)]" : "bg-neutral-800"} relative`}
            >
              <span
                className={`block h-4 w-4 rounded-full bg-white transition-transform ${
                  includeCitations ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
