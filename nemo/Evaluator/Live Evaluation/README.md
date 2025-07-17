# Live Evaluation Implementation

This repository demonstrates how to leverage Live Evaluation through NeMo Evaluator Microservice for real-time evaluation of LLM outputs. The example includes both simple string checking and Custom LLM-as-a-Judge evaluation of medical consultation summaries using Llama 3.3 Nemotron Super 49B as the judge.

## Overview

Live Evaluation enables real-time evaluation without pre-creating persistent evaluation targets and configurations. The implementation demonstrates two key evaluation types:
- **Simple String Checking**: Direct validation of outputs against expected values
- **Custom LLM-as-a-Judge**: Real-time evaluation of medical summaries for correctness (rated 0-4)

## Prerequisites

- Docker and Docker Compose installed
- NVIDIA NGC API key for container access
- NVIDIA API key from build.nvidia.com (for the judge LLM)
- NeMo Microservices Python SDK

## Project Structure

The project includes:
- Docker Compose configuration for local NeMo Evaluator deployment
- Jupyter notebook demonstrating live evaluation workflows
- Configuration files for the microservices setup
- Example medical consultation data for evaluation

## Key Components

1. **Local Deployment**
   - Uses Docker Compose to run NeMo Evaluator locally
   - Includes NeMo Data Store for data management
   - Configured for development and testing

2. **Simple String Checking**
   - Validates outputs using string comparison
   - Supports various comparison operators
   - Returns immediate evaluation results

3. **Custom LLM-as-a-Judge**
   - Uses Llama 3.3 Nemotron Super 49B as judge
   - Custom prompt templates for evaluating correctness
   - Regex-based score extraction (0-4 scale)
   - Real-time evaluation without persistent configs

## Setup Instructions

1. **Login to NGC Container Registry**
   ```bash
   docker login -u '$oauthtoken' -p YOUR_NGC_KEY_HERE nvcr.io
   ```

2. **Set Environment Variables**
   ```bash
   export EVALUATOR_IMAGE=nvcr.io/nvidia/nemo-microservices/evaluator:25.07
   export DATA_STORE_IMAGE=nvcr.io/nvidia/nemo-microservices/datastore:25.07
   export USER_ID=$(id -u)
   export GROUP_ID=$(id -g)
   ```

3. **Start Services**
   ```bash
   docker compose -f docker_compose.yaml up evaluator -d
   ```

## Results

The live evaluation provides immediate feedback including:
- Evaluation status (completed/failed)
- Scores with statistical metrics (mean, count, sum)
- Detailed results for each evaluation metric

## Dependencies

See `pyproject.toml` for a complete list of dependencies. Key requirements include:
- datasets>=3.5.0
- huggingface-hub>=0.30.2
- nemo-microservices>=1.0.1
- openai>=1.76.0

You can run `uv sync` to produce the required `.venv`!

## Documentation

For more detailed information about Live Evaluation, refer to the [official NeMo documentation](https://docs.nvidia.com/nemo/microservices/latest/evaluate/evaluation-live.html).
