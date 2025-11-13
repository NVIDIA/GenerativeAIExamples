# Prompt Optimization with MIPROv2

This repository demonstrates how to leverage NeMo Evaluator Microservice for prompt optimization using MIPROv2 (Multiprompt Instruction PRoposal Optimizer Version 2). The example showcases systematic prompt improvement through Bayesian Optimization for LLM-as-a-Judge evaluation tasks using the NVIDIA Nemotron Nano 9B V2 model.

## Overview

Prompt Optimization with MIPROv2 enables systematic improvement of LLM prompts through data-driven optimization. The implementation demonstrates:
- **MIPROv2 Optimization**: Bayesian Optimization-based prompt improvement
- **Judge Model Enhancement**: Optimizing NVIDIA Nemotron Nano 9B V2 for helpfulness evaluation
- **Performance Measurement**: Quantitative comparison of baseline vs optimized prompts

## Prerequisites

- Access to deployed NeMo Evaluator Microservice
- Access to NVIDIA NeMo Data Store Microservice
- OpenRouter API key (or NVIDIA API key for NIM endpoints)
- Python environment with `uv` package manager

## Project Structure

The project includes:
- Jupyter notebook demonstrating MIPROv2 prompt optimization workflows
- HelpSteer2 dataset sample for evaluation tasks
- Configuration files for the optimization setup
- Dependencies managed through `pyproject.toml`

## Key Components

1. **MIPROv2 Optimization Engine**
   - Uses Bayesian Optimization for systematic prompt improvement
   - Supports light/medium/heavy optimization intensities
   - Configurable trial parameters and demo examples

2. **Dataset Integration**
   - HelpSteer2 dataset format with prompt/response/reference structure
   - Seamless upload to NeMo Data Store via HuggingFace Hub API
   - Structured evaluation signatures matching dataset schema

3. **NVIDIA Nemotron Nano 9B V2 Judge**
   - Hybrid Mamba-2 and MLP architecture with Attention layers
   - Efficient model optimized for reasoning and non-reasoning tasks
   - Compatible with OpenAI API format through OpenRouter or NIM

4. **Performance Analytics**
   - Quantitative accuracy improvements (baseline vs optimized)
   - Detailed prompt comparison and analysis
   - Statistical metrics with confidence intervals

## Setup Instructions

1. **Install Dependencies**
   ```bash
   # Install uv package manager
   # Follow: https://docs.astral.sh/uv/getting-started/installation/
   
   # Create virtual environment and install dependencies
   uv sync
   ```
2. **Run the Notebook!**

## Optimization Configuration

The MIPROv2 optimization uses the following key parameters:

- **Signature**: `"prompt, response -> reference_helpfulness: int"` matching HelpSteer2 format
- **Initial Instruction**: Baseline prompt for helpfulness evaluation (0-4 scale)
- **Optimization Settings**:
  - `auto: "light"` - Optimization intensity level
  - `num_trials: 1` - Number of optimization trials
  - `max_bootstrapped_demos: 0` - Generated examples count
  - `max_labeled_demos: 0` - Training set examples used
- **Metrics**: Number-check with epsilon=1 tolerance for score validation

## Results

The prompt optimization provides comprehensive analysis including:

### Performance Metrics
- **Baseline Accuracy**: Original prompt performance
- **Optimized Accuracy**: Improved prompt performance  
- **Improvement Percentage**: Quantified enhancement (e.g., +10.14% improvement)

### Prompt Analysis
- **Baseline Prompt**: Original evaluation instruction
- **Optimized Prompt**: Enhanced prompt with improved structure, clarity, and task framing
- **Comparative Analysis**: Side-by-side prompt comparison with performance insights

### Example Results
```
Baseline Accuracy:  0.8118 (n=85)
Optimized Accuracy: 0.8941 (n=85)
Improvement:        +0.0823 (+10.14%)
```

## Dependencies

See `pyproject.toml` for complete dependency list. Key requirements include:
- huggingface-hub==0.26.2
- jupyter>=1.1.1
- pandas>=2.3.2
- requests>=2.32.5

You can run `uv sync` to produce the required `.venv`!

## Dataset Format

The notebook uses HelpSteer2 dataset format:
```json
{
  "prompt": "User query or instruction",
  "response": "Model response to evaluate", 
  "reference_helpfulness": 3
}
```

## Documentation

For more detailed information about Prompt Optimization with MIPROv2, refer to the [official NeMo documentation](https://docs.nvidia.com/nemo/microservices/latest/evaluate/flows/prompt-optimization.html).