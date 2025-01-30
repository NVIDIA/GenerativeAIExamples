# Multi Agent Self Corrective RAG

# Overview

The Self-Corrective Multi-Agent RAG system uses a graph-based workflow to process queries, retrieve relevant documents, grade document relevance, generate responses, and self-correct through query transformation. Initially, it retrieves relevant documents using a hybrid retrieval approach that combines BM25 and FAISS, ensuring efficient document search. The retrieved documents are then graded for relevance using NVIDIA AI endpoints for embeddings and reranking. Based on the most relevant documents, the system generates a response or, if necessary, transforms the query to refine the search

We are calling this tool as BAT.AI (Bug Automation Tool)
# Target Audience
Devlopers : This tool is designed for developers who need to quickly analyze log files and gain actionable insights using large language model (LLM). The system automatically refines prompts to ensure optimal results, offering developers an intuitive way to interact with log data and streamline their debugging process.  

# Components
- bat_ai.py: Defines the main workflow graph using LangGraph.
- graphnodes.py: Contains the node implementations for the workflow graph.
- multiagent.py: Implements the HybridRetriever class for document retrieval.
- graphedges.py: Contains the implementation of the edges for decision making 
- binaryscroes.py: Contains the formatted output information
- utils.py : It helps to implement the queries, retrieve relevant documents, grade their relevance, and generate responses      using a multi-agent RAG system.
- example.py: The script that analyzes a specified log file for errors based on a user-provided question, leveraging the workflow module to process and generate relevant insights.
    
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
`python main.py path/to/your/logfile.txt --question "What are the critical errors in the log file?"`

# Software Components
NVIDIA NIM Microservices
- NIM of meta/llama-3.1-70b-instruct
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

