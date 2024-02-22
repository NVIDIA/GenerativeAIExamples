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

6. [**Nvidia AI Endpoint Integration with langchain**](../../notebooks/07_Option(1)_NVIDIA_AI_endpoint_simple.ipynb)
This notebook demonstrates how to build a Retrieval Augmented Generation (RAG) example using the NVIDIA AI endpoint integrated with Langchain, with FAISS as the vector store.

7. [**RAG with langchain and local LLM model from**](../../notebooks/07_Option(2)_minimalistic_RAG_with_langchain_local_HF_LLM.ipynb)
This notebook demonstrates how to plug in a local llm from HuggingFace Hub and build a simple RAG app using langchain.

8. [**Nvidia AI Endpoint with llamaIndex and Langchain**](../../notebooks/08_Option(1)_llama_index_with_NVIDIA_AI_endpoint.ipynb)
This notebook demonstrates how to plug in a NVIDIA AI Endpoint mixtral_8x7b and embedding nvolveqa_40k, bind these into LlamaIndex with these customizations.

9. [**Locally deployed model from Hugginface integration with llamaIndex and Langchain**](../../notebooks/08_Option(2)_llama_index_with_HF_local_LLM.ipynb)
This notebook demonstrates how to plug in a local llm from HuggingFace Hub Llama-2-13b-chat-hf and all-MiniLM-L6-v2 embedding from Huggingface, bind these to into LlamaIndex with these customizations.

10. [**Langchain agent with tools plug in multiple models from  NVIDIA AI Endpoint**](../../notebooks/09_Agent_use_tools_leveraging_NVIDIA_AI_endpoints.ipynb)
This notebook demonstrates how to use multiple NVIDIA's AI endpoint's model like `mixtral_8*7b`, `Deplot` and `Neva`.

# Running the notebooks
If a JupyterLab server needs to be compiled and stood up manually for development purposes, follow the following commands:

- [Optional] Notebook `7 to 9` require GPUs. If you have a GPU and are trying out notebooks `7-9` update the jupyter-server service in the [docker-compose.yaml](../../deploy/compose/docker-compose.yaml) file to use `./notebooks/Dockerfile.gpu_notebook` as the Dockerfile
```
  jupyter-server:
    container_name: notebook-server
    image: notebook-server:latest
    build:
      context: ../../
      dockerfile: ./notebooks/Dockerfile.gpu_notebook
```

- [Optional] Notebook from `7-9` may need multiple GPUs. Update [docker-compose.yaml](../../deploy/compose/docker-compose.yaml) to use multiple gpu ids in `device_ids` field below or set `count: all`
```
  jupyter-server:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0', '1']
              capabilities: [gpu]
```

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
