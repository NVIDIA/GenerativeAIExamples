<!--
  SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# RAG Evaluation Application

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## About Evaluating RAGs

RAGs have two components--a retriever and a generator.
To quantify the performance of a RAG pipeline, you have to evaluate these components seperately as well as while they work together.

This RAG evaluation application measures RAG performance using RAGAS metrics and a likert score.
The RAGAS metrics are faithfulness, context relevancy, answer similarity, answer relevancy, and context precision.
The likert score is a value from 1 to 5 based on helpfulness, relevancy, accuracy, and level of detail of the generated answer.

Comparing the metrics for different RAG pipelines can provide insights and help you choose better parameters for the pipeline.
You can evalute the pipelines on standard raw or synthetically generated question-and-answer dataset.

## Prerequisites

- Clone the Generative AI examples Git repository using Git LFS:

  ```console
  $ sudo apt -y install git-lfs
  $ git clone git@github.com:NVIDIA/GenerativeAIExamples.git
  $ cd GenerativeAIExamples/
  $ git lfs pull
  ```

- A host with an NVIDIA A100, H100, or L40S GPU.

- Verify NVIDIA GPU driver version 535 or later is installed and that the GPU is in compute mode:

  ```console
  $ nvidia-smi -q -d compute
  ```

  *Example Output*

  ```{code-block} output
  ---
  emphasize-lines: 4,9
  ---
  ==============NVSMI LOG==============

  Timestamp                                 : Sun Nov 26 21:17:25 2023
  Driver Version                            : 535.129.03
  CUDA Version                              : 12.2

  Attached GPUs                             : 1
  GPU 00000000:CA:00.0
      Compute Mode                          : Default
  ```

  If the driver is not installed or below version 535, refer to the [*NVIDIA Driver Installation Quickstart Guide*](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html).

- Install Docker Engine and Docker Compose.
  Refer to the instructions for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

- Install the NVIDIA Container Toolkit.

  1. Refer to the [installation documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

  1. When you configure the runtime, set the NVIDIA runtime as the default:

     ```console
     $ sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
     ```

     If you did not set the runtime as the default, you can reconfigure the runtime by running the preceding command.

  1. Verify the NVIDIA container toolkit is installed and configured as the default container runtime:

     ```console
     $ cat /etc/docker/daemon.json
     ```

     *Example Output*

     ```json
     {
         "default-runtime": "nvidia",
         "runtimes": {
             "nvidia": {
                 "args": [],
                 "path": "nvidia-container-runtime"
             }
         }
     }
     ```

  1. Run the `nvidia-smi` command in a container to verify the configuration:

     ```console
     $ sudo docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi -L
     ```

     *Example Output*

     ```output
     GPU 0: NVIDIA A100 80GB PCIe (UUID: GPU-d8ce95c1-12f7-3174-6395-e573163a2ace)
     ```

## Generating Data with the Synthetic Data Generator

To generate a synthetic Q&A pair dataset from custom documents, perform the following steps:

1. In the Generative AI Examples repository, edit the `deploy/compose/eval-app-compose.env` file and specify the input and output paths:

   - Update `DATASET_DIRECTORY` with the path to a directory with the documents to ingest.

     Copy PDF files to analyze into the specified directory.
     You can use the `notebooks/dataset.zip` file in the repository for sample PDF files.

   - Update `RESULT_DIRECTORY` with the path for the output Q&A pair dataset.

1. Set your NVIDIA API key in an environment variable:

   ```console
   $ export NVIDIA_API_KEY='nvapi-*'
   ```

1. From the root of the repository, build and run the synthetic data generator:

   ```console
   $ docker compose \
       --env-file deploy/compose/eval-app-compose.env \
       -f deploy/compose/docker-compose-evaluation-application.yaml \
       build synthetic_data_generator

   $ docker compose \
       --env-file deploy/compose/eval-app-compose.env \
       -f deploy/compose/docker-compose-evaluation-application.yaml \
       up synthetic_data_generator
   ```

   *Example Output*

   ```output
   [+] Running 1/0
    ✔ Container data-generator  Created
   Attaching to data-generator
   data-generator  | INFO:data_generator:1/1
   data-generator  | INFO:pikepdf._core:pikepdf C++ to Python logger bridge initialized
   data-generator  | INFO:matplotlib.font_manager:generated new fontManager
   data-generator  | [nltk_data] Downloading package punkt to /root/nltk_data...
   data-generator  | [nltk_data]   Unzipping tokenizers/punkt.zip.
   data-generator  | [nltk_data] Downloading package averaged_perceptron_tagger to
   data-generator  | [nltk_data]     /root/nltk_data...
   data-generator  | [nltk_data]   Unzipping taggers/averaged_perceptron_tagger.zip.
   data-generator  | INFO:__main__:\DATA GENERATED
   data-generator  |
   data-generator exited with code 0
   ```
  

## Generating Answers and Evaluating a RAG Pipeline

1. Start an instance of the Chain Server.

   You can run an example, such as [Using the NVIDIA API Catalog](https://nvidia.github.io/GenerativeAIExamples/latest/api-catalog.html), to start a Chain Server.

1. From the root of the repository, build and run the RAG evaluator:

   ```console
   $ docker compose \
       --env-file deploy/compose/eval-app-compose.env \
       -f deploy/compose/docker-compose-evaluation-application.yaml \
       build rag_evaluator

   $ docker compose \
       --env-file deploy/compose/eval-app-compose.env \
       -f deploy/compose/docker-compose-evaluation-application.yaml \
       run rag_evaluator
   ```

   *Example Output*

   ```output
   INFO:llm_answer_generator:1/1
   INFO:llm_answer_generator:1/6
   INFO:llm_answer_generator:data: {"id":"e7262f2b-0753-4b6c-813d-a38cd4a5954c","choices":[{"index":0,"message":{"role":"assistant","content":""},"finish_reason":""}]}
   ...
   Evaluating:  94%|███████████████████████████████████████████████████████████████████    | 34/36 [00:18<00:00,  2.10it/s]
   WARNING:ragas.metrics._context_recall:Invalid JSON response. Expected dictionary with key 'Attributed'
   Evaluating: 100%|███████████████████████████████████████████████████████████████████████| 36/36 [00:22<00:00,  1.62it/s]
   INFO:evaluator:Results written to /result_dir/result.json and /result_dir/result.parquet
   INFO:__main__:
   RAG EVALUATED WITH RAGAS METRICS
   ```

## Results and Conclusion

Find the following as results of running evaluation application on given `qna.json` dataset.
The `RESULT_DIRECTORY` path has two newly created files.

- A JSON file, `result.json`, with aggregated PERF metrics like the following example:

  ```json
  {
    "answer_similarity": 0.7944183243305074,
    "faithfulness": 0.25,
    "context_precision": 0.249999999975,
    "context_relevancy": 0.4837612078324153,
    "answer_relevancy": 0.6902010104258721,
    "context_recall": 0.5,
    "ragas_score": 0.4203451750317139
  }
  ```

- A parquet file, `result.parquet`, with PERF metrics for each Q&A pair like the following example:

  ```json
  {
    "question": "What is the contact email for Jordan Dodge who works in the SHIELD and GeForce NOW division at NVIDIA Corporation?",
    "answer": " jdodge@nvidia.com",
    "contexts": [
    "products and technologies or enhancements to our existing product and technologies ; market acceptance of our products or our partners ’ products ; design, manufacturing or software defects ; changes in consumer preferences or demands ; changes in industry standards and interfaces ; unexpected loss of performance of our products or technologies when integrated into systems ; as well as other factors detailed from time to time in the most recent reports nvidia files with the securities and exchange commission, or sec, including, but not limited to, its annual report on form 10 - k and quarterly reports on form 10 - q. copies of reports filed with the sec are posted on the company ’ s website and are available from nvidia without charge. these forward - looking statements are not guarantees of future performance and speak only as of the date hereof, and, except as required by law, nvidia disclaims any obligation to update these forward - looking statements to reflect future events or circumstances. © 2023 nvidia corporation. all rights reserved. nvidia, the nvidia logo, bluefield and connectx are trademarks and / or registered trademarks of nvidia corporation in the u. s. and other countries. all other trademarks and copyrights are the property of their respective owners. features, pricing, availability and specifications are subject to change without notice. alexa korkos director, product pr ampere computing + 1 - 925 - 286 - 5270 akorkos @ amperecomputing. com jordan dodge shield, geforce now nvidia corp. + 1 - 408 - 506 - 6849 jdodge @ nvidia. com"
    ],
    "ground_truth": "jdodge@nvidia.com",
    "answer_similarity": 1,
    "faithfulness": 0,
    "context_precision": 0.9999999999,
    "context_relevancy": 0.35714285714285715,
    "answer_relevancy": 0.7686588526523409,
    "context_recall": 1,
    "ragas_score": 0
  }
  ```
