# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

# Dataset paths - change this to the path to your dataset
DATASET_LOCAL_PATH = Path(__file__).parent / "PhysicalAI-Robotics-GR00T-GR1" 
METADATA_FILE = DATASET_LOCAL_PATH / "metadata.csv"
DATA_DIR = DATASET_LOCAL_PATH / "gr1"

# API endpoints
COSMOS_API_URL = "http://localhost:8000/v1/embeddings"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "video_embeddings"
EMBEDDING_DIM = 256

# Equal weights for video and text embeddings - can be adjusted to prioritize one over the other
VIDEO_WEIGHT = 0.5
TEXT_WEIGHT = 0.5
