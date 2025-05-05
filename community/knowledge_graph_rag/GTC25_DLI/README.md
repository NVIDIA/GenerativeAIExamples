# Knowledge Graph-based RAG System

This repository contains the materials for the NVIDIA GTC 2025 Deep Learning Institute course: "Structure From Chaos: Accelerate GraphRAG With cuGraph and NVIDIA NIM" [DLIT71491].

You can access the online course video at: [NVIDIA On-Demand](https://www.nvidia.com/en-us/on-demand/session/gtc25-dlit71491/)

## Overview

This course demonstrates how to build a Knowledge Graph-based RAG system for financial documents, specifically SEC 10-K filings. The system extracts structured knowledge triplets, builds a dynamic knowledge graph, and provides enhanced query capabilities.

You'll learn how to integrate large language models (LLMs) with NVIDIA Inference Microservices (NIM) and cuGraph to create cutting-edge, graph-based AI solutions for handling complex, interconnected data. The course covers fine-tuning techniques, Langchain agents, and GPU-accelerated graph analytics to enhance AI capabilities and retrieval-augmented generation (RAG) evaluation.

## Prerequisites

- Docker and docker-compose
- 4x NVIDIA A100 GPUs required for the LLM fine-tuning workflow (Notebook 2)
- NVIDIA API key (sign up at [NVIDIA AI portal](https://developer.nvidia.com/))

## Setup

1. Clone this repository
2. Set your NVIDIA API key in the `.env` file:
   ```
   NVIDIA_API_KEY=your-nvapi-key
   NGC_API_KEY=your-ngc-key  # For some containerized models
   ```
3. Start the containers:
   ```bash
   docker-compose up -d
   ```
4. Access the Jupyter Lab environment at: http://localhost:8888

## Notebooks

The course consists of five notebooks that build upon each other:

1. **01_Graph_Triplet_Extraction.ipynb**
   - Extract structured (subject, relation, object) triplets from SEC 10-K filings
   - Transform unstructured text into structured knowledge for a knowledge graph

2. **02_LLM_Finetuning.ipynb**
   - Fine-tune a smaller LLM (LLaMa-3 8B) for more accurate triplet prediction
   - Leverage NVIDIA NeMo and NVIDIA Inference Microservices (NIM)

3. **03_Dynamic_Database.ipynb**
   - Set up a persistent, dynamic backend (ArangoDB) for the knowledge graph
   - Handle triplets being added or deleted over time
   - Create a GraphRAG agent connected to a continuously updating database

4. **04_Evaluation.ipynb**
   - Evaluate the RAG system using Ragas and NVIDIA's Nemotron-340b-reward model
   - Assess metrics such as faithfulness, context precision, and answer relevancy

5. **05_Link_Prediction.ipynb**
   - Improve knowledge graph completeness through link prediction
   - Use techniques like TransE model and non-negative matrix factorization
   - Predict missing relationships within the knowledge graph

## Data

The notebooks use 2021 SEC documents (10-K filings) from the [Kaggle SEC EDGAR Annual Financial Filings 2021 dataset](https://www.kaggle.com/datasets/pranjalverma08/sec-edgar-annual-financial-filings-2021). The data preprocessing tools are included in the `data_prep` directory.

## Requirements

The key Python packages required for this project are listed in `requirements.txt` and include:
- numpy, scipy, scikit-learn
- torch, pykeen, fairscale
- jupyterlab, networkx
- ArangoDB libraries (nx_arangodb, arango)
- NVIDIA GPU libraries (cugraph-cu12, nx_cugraph-cu12)
- LLM frameworks (llama-index, langchain, transformers)
- Evaluation tools (ragas, datasets)

## Docker Environment

The repository uses multiple containers:
- A JupyterLab environment with CUDA support
- NVIDIA NeMo container for model fine-tuning
- NVIDIA NIM container for model serving
- ArangoDB for graph database storage