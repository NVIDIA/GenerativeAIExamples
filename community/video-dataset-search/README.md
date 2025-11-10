<!-- 
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
-->


# Multimodal Video Dataset Search

Search videos using text, images, or video queries with NVIDIA Cosmos Embed1. 
Automatically combines video and text embeddings for better search results.

## Prerequisites

- Docker + NVIDIA Container Toolkit
- NVIDIA GPU (8GB+ VRAM)
- NGC API Key ([get one here](https://org.ngc.nvidia.com/setup/api-key))
- Python 3.8+

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Services

```bash
# Pull and start Cosmos Embed1
export NGC_API_KEY="your_api_key_here"

docker pull nvcr.io/nim/nvidia/cosmos-embed1:1.0.0

docker run -it --rm --runtime=nvidia --name=cosmos-embed1 --gpus device=0 -p 8000:8000 -e NGC_API_KEY=$NGC_API_KEY nvcr.io/nim/nvidia/cosmos-embed1:1.0.0

# Start Qdrant
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

### 3. Download Dataset (Optional)

```bash
git clone https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-GR1
```

### 4. Index Videos

```bash
python index_videos.py
```

### 5. Launch Search UI

```bash
python gradio_app.py
```

Open http://localhost:7860 to search videos!

## Configuration

Edit `config.py` to customize:

```python
VIDEO_WEIGHT = 0.6  # Higher = prioritize visual similarity
TEXT_WEIGHT = 0.4   # Higher = prioritize semantic similarity
```

Dataset paths can also be configured in `config.py`:
- `DATASET_LOCAL_PATH`, `DATA_DIR`, and `METADATA_FILE` control where videos and metadata are loaded from.
- By default, the tool expects per-video text to be stored in a `metadata.csv` file in the dataset directory.
