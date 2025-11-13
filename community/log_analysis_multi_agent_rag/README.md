# Multi Agent Self Corrective RAG

# Overview

The Self-Corrective Multi-Agent RAG system uses a graph-based workflow to process queries, retrieve relevant documents, grade document relevance, generate responses, and self-correct through query transformation. Initially, it retrieves relevant documents using a hybrid retrieval approach that combines BM25 and FAISS, ensuring efficient document search. The retrieved documents are then graded for relevance using NVIDIA AI endpoints for embeddings and reranking. Based on the most relevant documents, the system generates a response or, if necessary, transforms the query to refine the search

We are calling this tool as BAT.AI (Bug Automation Tool)
# Target Audience
Devlopers : This tool is designed for developers who need to quickly analyze log files and gain actionable insights using large language model (LLM). The system automatically refines prompts to ensure optimal results, offering developers an intuitive way to interact with log data and streamline their debugging process.  

# How to Use

This repository provides a sample code to demonstrate how you can use the log analysis tool for your logs. Follow the instructions below to set up and integrate the tool into your workflow.

### Set up your API Key:

- **Generate your API key** by following the steps in the link below:
  [Click here to view the steps for generating an API Key](https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html#generate-an-api-key)

- **Store your API key** : You can securely store your API key by creating a `.env` file in the root directory of your project
- **example.py** : The sample script showcases how to integrate log analysis into your workflow. It demonstrates how to pass your log data through the system, generate insights, and manage the output.

# Components
- bat_ai.py: Defines the main workflow graph using LangGraph.
- graphnodes.py: Contains the node implementations for the workflow graph.
- multiagent.py: Implements the HybridRetriever class for document retrieval.
- graphedges.py: Contains the implementation of the edges for decision making 
- binaryscroes.py: Contains the formatted output information
- utils.py : It helps to implement the queries, retrieve relevant documents, grade their relevance, and generate responses using a multi-agent RAG system.

    
![SW Architecture](<BAT.AI SW Architecture Diagram.drawio.png>)

# Key Features
    Hybrid document retrieval (BM25 + FAISS)
    Document relevance grading
    Self-corrective query transformation
    NVIDIA AI-powered embeddings and reranking
    
# Setup
    Install the required dependencies.
    Set up the NVIDIA API key in your environment.
    Prepare your document corpus and update the file path in the code.


# Code
`python example.py path/to/your/logfile.txt --question "What are the critical errors in the log file?"`

# Software Components
NVIDIA NIM Microservices
- NIM of nvidia/llama-3.3-nemotron-super-49b-v1.5
- Retriever Models
- NIM of nvidia/llama-3_2-nv-embedqa-1b-v2
- NIM of nvidia/llama-3_2-nv-rerankqa-1b-v2


# Workflow

1. Retrieve Relevant Documents:
    The system searches for and retrieves log entries or documents that are most relevant to the user's query.
2. Grade Document Relevance:
    The retrieved documents are evaluated and ranked based on their relevance to the input query.
3. Generate a Response or Transform the Query:
    The system generates a response based on the most relevant documents or modifies the query to refine the search for better results.
4. Evaluate the Generation and Decide to Output or Continue the Process:
    The quality of the generated response is assessed; if it meets the required standards, it’s outputted. If not, the query is further refined and the process repeats.

