# Evaluation Tool

## Tool Details
Evaluation is crucial for retrieval augmented generation (RAG) pipelines as it ensures the accuracy and relevance of information retrieved as well as the generated content.

There are 3 components needed for evaluating the performance of a RAG pipeline:
1. Data for testing.
2. Automated metrics to measure performance of both the context retrieval and response generation.
3. Human-like evaluation of the generated response from the end-to-end pipeline.

This tool provides a set of notebooks that show examples of how to address these requirements in an automated fashion.

### Synthetic Data Generation
Using an existing knowledge base we can synthetically generate question|answer|context triplets using a LLM. This tool uses the Llama 2 70B model on [Nvidia AI Playground](https://www.nvidia.com/en-us/research/ai-playground/) for data generation.

### Automated Metrics
[RAGAS](https://github.com/explodinggradients/ragas) is an automated metrics tool for measuring performance of both the retriever and generator. We utilize the Nvidia AI Playground langchain wrapper to run RAGAS evaluation on our example RAG pipeline.

### LLM-as-a-Judge
We can use LLMs to provide human-like feedback and Likert evaluation scores for full end-to-end RAG pipelines. This tool uses Llama 2 70B as a judge LLM.
