# Knowledge Graph RAG Notebooks

This directory contains the Jupyter notebooks for the NVIDIA GTC 2025 DLI course on Knowledge Graph RAG. The notebooks should be completed in sequence as each builds upon the previous one's outputs.

## Hardware Requirements

- Basic RAG Pipeline (Notebooks 1, 3, 4, 5): Single NVIDIA GPU with CUDA support
- LLM Fine-tuning (Notebook 2): 4x NVIDIA A100 GPUs

## Notebook Details

### 1. Graph Triplet Extraction
**File:** `01_Graph_Triplet_Extraction.ipynb`
- Processes SEC 10-K filings to extract knowledge triplets
- Uses NVIDIA AI Endpoints for extraction
- Outputs: JSON files containing (subject, relation, object) triplets
- Expected runtime: ~30 minutes

### 2. LLM Fine-tuning
**File:** `02_LLM_Finetuning.ipynb`
- Fine-tunes LLaMa-3 8B model for triplet prediction
- Requires 4x A100 GPUs
- Uses NVIDIA NeMo framework
- Outputs: Fine-tuned model weights
- Expected runtime: 6-8 hours

### 3. Dynamic Database
**File:** `03_Dynamic_Database.ipynb`
- Sets up ArangoDB graph database
- Implements dynamic triplet management
- Creates GPU-accelerated GraphRAG agent
- Outputs: Persistent graph database
- Expected runtime: ~20 minutes

### 4. Evaluation
**File:** `04_Evaluation.ipynb`
- Uses Ragas framework for RAG evaluation
- Implements NVIDIA's Nemotron-340b-reward model
- Assesses system performance metrics
- Outputs: Evaluation metrics and visualizations
- Expected runtime: ~45 minutes

### 5. Link Prediction
**File:** `05_Link_Prediction.ipynb`
- Implements TransE model for link prediction
- Uses non-negative matrix factorization
- Improves knowledge graph completeness
- Outputs: Predicted relationships and enhanced graph
- Expected runtime: ~30 minutes

## Data Directory Structure

Each notebook expects the following data structure:
```
data/
├── triples_10k/          # Extracted triplets from 10-K filings
├── csvs/                 # Processed CSV files for graph database
├── evaluation_data/      # Test data for RAG evaluation
└── TransE_model/         # Saved link prediction model
```

## Common Issues & Solutions

1. **GPU Memory:**
   - Notebook 2 requires ~80GB total GPU memory
   - Other notebooks work with 16GB+ GPU memory

2. **Data Loading:**
   - Download Kaggle dataset before starting
   - Run data preparation scripts if needed 