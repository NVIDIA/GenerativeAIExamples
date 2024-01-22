# Jupyter Notebooks
For development and experimentation purposes, the Jupyter notebooks provide guidance to building knowledge augmented chatbots.

The following Jupyter notebooks are provided with the AI workflow for the default canonical RAG example:

1. [**LLM Streaming Client**](../../notebooks/01-llm-streaming-client.ipynb)

This notebook demonstrates how to use a client to stream responses from an LLM deployed to NVIDIA Triton Inference Server with NVIDIA TensorRT-LLM (TRT-LLM). This deployment format optimizes the model for low latency and high throughput inference.

2. [**Document Question-Answering with LangChain**](../../notebooks/02_langchain_simple.ipynb)

This notebook demonstrates how to use LangChain to build a chatbot that references a custom knowledge-base. LangChain provides a simple framework for connecting LLMs to your own data sources. It shows how to integrate a TensorRT-LLM to LangChain using a custom wrapper.

3. [**Document Question-Answering with LlamaIndex**](../../notebooks/03_llama_index_simple.ipynb)

This notebook demonstrates how to use LlamaIndex to build a chatbot that references a custom knowledge-base. It contains the same functionality as the notebook before, but uses some LlamaIndex components instead of LangChain components. It also shows how the two frameworks can be used together.

4. [**Advanced Document Question-Answering with LlamaIndex**](../../notebooks/04_llamaindex_hier_node_parser.ipynb)

This notebook demonstrates how to use LlamaIndex to build a more complex retrieval for a chatbot. The retrieval method shown in this notebook works well for code documentation; it retrieves more contiguous document blocks that preserve both code snippets and explanations of code.

5. [**Interact with REST FastAPI Server**](../../notebooks/05_dataloader.ipynb)

This notebook demonstrates how to use the REST FastAPI server to upload the knowledge base and then ask a question without and with the knowledge base.

# Running the notebooks
If a JupyterLab server needs to be compiled and stood up manually for development purposes, run the following commands:
- Build the container
```
  source deploy/compose/compose.env
  docker compose -f deploy/compose/docker-compose.yaml build jupyter-server

```
- Run the container which starts the notebook server
```
  source deploy/compose/compose.env
  docker compose -f deploy/compose/docker-compose.yaml up jupyter-server
```
- Using a web browser, type in the following URL to access the notebooks.

    ``http://host-ip:8888``
