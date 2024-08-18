<!--
  SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Evaluation Tool

<!-- TOC -->

- [Evaluation Tool](#evaluation-tool)
  - [Introduction](#introduction)
    - [Synthetic Data Generation](#synthetic-data-generation)
    - [Automated Metrics](#automated-metrics)
    - [LLM-as-a-Judge](#llm-as-a-judge)
  - [Prerequisites](#prerequisites)
  - [Build and Start the Containers](#build-and-start-the-containers)
  - [Results and Conclusion](#results-and-conclusion)

<!-- /TOC -->

## Introduction

Evaluation is crucial for retrieval augmented generation (RAG) pipelines because it ensures the accuracy and relevance of the information that is retrieved as well as the generated content.

There are three components needed for evaluating the performance of a RAG pipeline:

- Data for testing.
- Automated metrics to measure performance of both the context retrieval and response generation.
- Human-like evaluation of the generated response from the end-to-end pipeline.

This tool provides a set of notebooks that demonstrate how to address these requirements in an automated fashion for the default developer RAG example.


### Synthetic Data Generation

Using an existing knowledge base, we can generate synthetic question|answer|context triplets using an LLM.
This tool uses the Mistral 8 x 7B Instruct model from the NVIDIA API Catalog for data generation.

### Automated Metrics

[RAGAS](https://github.com/explodinggradients/ragas) is an automated metrics tool for measuring performance of both the retriever and generator.
This tool uses a LangChain wrapper to connect to NVIDIA API Catalog endpoints to run RAGAS evaluation on our example RAG pipeline.

### LLM-as-a-Judge

This tool uses LLMs to provide human-like feedback and Likert evaluation scores for full end-to-end RAG pipelines.
The Mistral 8 x 7B Instruct model is used as a judge LLM.

## Prerequisites

Complete the [common prerequisites](../../../docs/common-prerequisites.md)


## Build and Start the Containers

1. Export the `NVIDIA_API_KEY` variable in terminal.

   Add the API for the model endpoint:

   ```text
   export NVIDIA_API_KEY="nvapi-<...>"
   ```

1. Start an example to evaluate:

   ```console
   cd RAG/examples/basic_rag/langchain
   USERID=$(id -u) docker compose up -d --build
   ```

1. Edit the `RAG/tools/evaluation/compose.env` file and set directory paths for the data and results.

   - Update `DATASET_DIRECTORY` with the path to a directory with the documents to ingest.

     Copy PDF files to analyze into the specified directory.
     You can use the `RAG/tools/evaluation/dataset.zip` file in the repository for sample PDF files.

   - Update `RESULT_DIRECTORY` with the path for the output Q&A pair dataset.


   You can extract one or more PDF files from the `datasets.zip` file to place into the data directory.

1. Evaluate a RAG pipeline:

   ```console
   cd RAG/tools/evaluation
   docker compose --env-file compose.env up --build
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
