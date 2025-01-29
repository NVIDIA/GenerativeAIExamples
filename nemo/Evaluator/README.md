# NeMo Evaluator Notebooks

A collection of example notebooks demonstrating how to use the NeMo Evaluator microservice for different evaluation scenarios.

## Getting Started
[Getting Started with NeMo Evaluator](GettingStarted/Getting%20Started%20with%20NeMo%20Evaluator.ipynb)
- Demonstrates basic usage of NeMo Evaluator
- Shows how to evaluate a baseline Llama 3.1 8B Instruct model using BigBench
- Explains how to evaluate a customized model on a title-generation task using ROUGE metrics
- Covers fundamental concepts like creating evaluation targets, configs and running jobs

## LLM as a Judge 
[LLM As a Judge](LLMAsAJudge/LLM%20As%20a%20Judge.ipynb)
- Shows how to use LLMs to evaluate other models' outputs
- Demonstrates custom LLM-as-a-judge evaluation setup for summarization tasks
- Covers creating evaluation targets, configurations and running evaluation jobs
- Includes examples of judge prompts and result analysis

## Embedding and RAG Evaluation
[NeMo Evaluator Retriever and RAG Evaluation](EmbeddingAndRAG/NeMo_Evaluator_Retriever_and_RAG_Evaluation.ipynb)
- Demonstrates evaluation of retrieval and RAG systems
- Covers:
  - Retriever Model Evaluation on FiQA
  - Retriever + Reranking Evaluation on FiQA
  - RAG Evaluation on FiQA with Ragas Metrics
  - RAG Evaluation on Synthetic Data with Ragas Metrics
- Shows how to work with custom datasets and different evaluation metrics


