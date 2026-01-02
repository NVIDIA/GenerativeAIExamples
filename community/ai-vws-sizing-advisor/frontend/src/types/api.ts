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

import { Message } from "./chat";
import { DocumentMetadata } from "./common";

export interface GenerateResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: {
    index: number;
    message: Message;
    finish_reason?: string;
    logprobs: null;
  }[];
  usage: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  sources?: {
    total_results: number;
    results: SourceResult[];
  };
}

export interface SourceResult {
  document_id: string;
  content: string;
  document_name: string;
  document_type: "image" | "text" | "table" | "chart";
  score: number;
  metadata: DocumentMetadata;
}
