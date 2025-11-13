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

export interface DocumentMetadata {
  language?: string;
  date_created?: string;
  last_modified?: string;
  page_number?: number;
  description?: string;
  height?: number;
  width?: number;
  location?: number[];
  location_max_dimensions?: number[];
}

export interface BaseResponse {
  status?: string;
  message?: string;
}

export interface VDBConfig {
  collection_name?: string;
  vdb_endpoint?: string;
}

export interface ExtractionOptions {
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface SplitOptions {
  split_method?: string;
  split_params?: Record<string, any>;
}
