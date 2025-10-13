# Custom LLM-as-a-Judge Implementation

This repository demonstrates how to leverage Custom LLM-as-a-Judge through NeMo Evaluator Microservice for evaluating LLM outputs. The example focuses on evaluating medical consultation summaries using a combination of Llama 3.1 70B model for generation and OpenAI's GPT-4.1 as the judge.

## Overview

The implementation evaluates medical consultation summaries on two key metrics:
- **Completeness**: How well the summary captures all critical information (rated 1-5)
- **Correctness**: How accurate the summary is without false information (rated 1-5)

## Prerequisites

- NeMo Microservices setup including:
  - NeMo Evaluator
  - NeMo Data Store
  - NeMo Entity Store
- API keys for:
  - OpenAI (for the judge LLM)
  - NVIDIA build.nvidia.com (for the target model)

## Project Structure

The project uses a JSONL file containing synthetic medical consultation data with the following structure:
```json
{
    "ID": "C012",
    "content": "Date: 2025-04-12\nChief Complaint (CC): ...",
    "summary": "New Clinical Problem: ..."
}
```

## Key Components

1. **Judge LLM Configuration**
   - Uses GPT-4.1 as the judge
   - Custom prompt templates for evaluating completeness and correctness
   - Regex-based score extraction

2. **Target Model Configuration**
   - Uses Llama 3.1 70B for generating summaries
   - Configured through NVIDIA's build.nvidia.com API

3. **Evaluation Process**
   - Generates summaries using the target model
   - Judges the summaries using the judge LLM
   - Aggregates scores for both metrics

## Results

The evaluation provides scores on a scale of 1-5 for both completeness and correctness, with detailed statistics including:
- Mean scores
- Total count of evaluations
- Sum of scores

## Dependencies

See `pyproject.toml` for a complete list of dependencies. Key requirements include:
- datasets>=3.5.0
- huggingface-hub>=0.30.2
- openai>=1.76.0
- transformers>=4.36.0

You can run `uv sync` to produce the required `.venv`!

## Documentation

For more detailed information about Custom LLM-as-a-Judge evaluation, refer to the [official NeMo documentation](https://docs.nvidia.com/nemo/microservices/latest/evaluate/evaluation-custom.html#evaluation-with-llm-as-a-judge).
