<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Support Matrix


## GPU Requirements

Large Language Models are a heavily GPU-limited workflow.
All LLMs are defined by the number of billions of parameters that make up their networks.
These generative AI examples focus on the Llama 3 Instruct models from Meta.
These models are available in two sizes: 8B and 70B.

|        Chat Model         | GPU Memory Requirement |
| ------------------------- | ---------------------- |
| Meta Llama 3 8B Instruct  | 30 GB                  |
| Meta Llama 3 70B Instruct | 320 GB                 |

These resources can be provided by multiple GPUs on the same machine.

To perform retrieval augmentation, an embedding model is required.
The embedding model converts a sequence of words to a representation in the form of a vector of numbers.

| Default Embedding Model  | GPU Memory Requirement |
| ------------------------ | ---------------------- |
| Snowflake Arctic-Embed-L | 2 GB                   |

For examples that use reranking, the ranking model improves the retrieval process by finding the most relevant passages as context when querying the LLM.

|  Default Ranking Model   | GPU Memory Requirement |
| ------------------------ | ---------------------- |
| NV-RerankQA-Mistral4B-v3 | 9 GB                   |

For information about the GPU memory requirements for alternative models, refer to the following documentation pages:

- NVIDIA NIM for LLMs [Support Matrix](https://docs.nvidia.com/nim/large-language-models/latest/support-matrix.html)
- NVIDIA Text Embedding NIM [Support Matrix](https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/support-matrix.html)
- NVIDIA Text Reranking NIM [Support Matrix](https://docs.nvidia.com/nim/nemo-retriever/text-reranking/latest/support-matrix.html)

For the Milvus database, allow an additional 4GB of GPU Memory.

## CPU and Memory Requirements

For development purposes, have at least 10 CPU cores and 64 GB of RAM.

## Storage Requirements

The two primary considerations for storage in retrieval augmented generation are the model weights and the documents in the vector database.
The file size of the model varies according to the number of parameters in the model:

|          Model           | Disk Storage |
| ------------------------ | ------------ |
| Llama 3 8B Instruct      | 30 GB        |
| Llama 3 70B Instruct     | 140 GB       |
| Snowflake Arctic-Embed-L | 17 GB        |
| NV-RerankQA-Mistral4B-v3 | 23 GB        |

The file space needed for the vector database varies by how many documents that you upload.
For development purposes, 10 GB is sufficient.

You need approximately 60 GB for Docker images.
