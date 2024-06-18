<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Support Matrix

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## GPU Requirements

Large Language Models are a heavily GPU-limited workflow.
All LLMs are defined by the number of billions of parameters that make up their networks.
These generative AI examples focus on the Llama 3 Instruct models from Meta.
These models are available in two sizes: 8B and 70B.

```{list-table}
:header-rows: 1

* - Model
  - GPU Memory Requirement

* - Meta Llama 3 8B Instruct
  - 30 GB

* - Meta Llama 3 70B Instruct
  - 320 GB

```

These resources can be provided by multiple GPUs on the same machine.

To perform retrieval augmentation, an embedding model is required.
The embedding model converts a sequence of words to a representation in the form of a vector of numbers.
This model is much smaller and requires an additional 2GB of GPU memory.

In the examples, Milvus is set as the default vector database.
Milvus is the default because it can use the NVIDIA RAFT libraries that enable GPU acceleration of vector searches.
For the Milvus database, allow an additional 4GB of GPU Memory.

## CPU and Memory Requirements

For development purposes, have at least 10 CPU cores and 64 GB of RAM.

## Storage Requirements

The two primary considerations for storage in retrieval augmented generation are the model weights and the documents in the vector database.
The file size of the model varies according to the number of parameters in the model:

```{list-table}
:header-rows: 1

* - Model
  - Disk Storage

* - Llama 3 8B Instruct
  - 30 GB

* - Llama 3 70B Instruct
  - 140 GB

```

The file space needed for the vector database varies by how many documents that you upload.
For development purposes, 10 GB is sufficient.

You need approximately 60 GB for Docker images.
