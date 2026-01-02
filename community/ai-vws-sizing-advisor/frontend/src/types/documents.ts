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

import {
  DocumentMetadata,
  VDBConfig,
  ExtractionOptions,
  SplitOptions,
} from "@/types/common";

export interface Document {
  document_id?: string;
  document_name: string;
  document_content?: string; // Base64 encoded binary data
  content?: string;
  document_type?: string;
  score?: number;
  size_bytes?: number;
  timestamp?: string;
  metadata?: DocumentMetadata;
}

export interface DocumentResponse {
  document_id: string;
  document_name: string;
  document_content?: string;
  content?: string;
  document_type?: string;
  score?: number;
  size_bytes?: number;
  timestamp?: string;
  metadata?: DocumentMetadata;
  message?: string;
  status?: string;
}

export interface DocumentListResponse {
  message: string;
  total_documents: number;
  documents: DocumentResponse[];
  status?: string;
}

export interface DocumentRequest extends VDBConfig {
  documents: Document[];
}
