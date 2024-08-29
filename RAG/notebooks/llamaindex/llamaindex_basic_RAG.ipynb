{
 "cells": [
  {
   "cell_type": "markdown",
   "id": "c5fb0b9e-f9cd-404f-bd8d-0273e94ac1fe",
   "metadata": {},
   "source": [
    "# RAG Example Using NVIDIA API Catalog and LlamaIndex"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "2969cdab-82fc-4ce5-bde1-b4f629691f27",
   "metadata": {},
   "source": [
    "This notebook introduces how to use LlamaIndex to interact with NVIDIA hosted NIM microservices like chat, embedding, and reranking models to build a simple retrieval-augmented generation (RAG) application.\n",
    "\n",
    "Alternatively, for a more interactive experience with a graphical user interface, you can refer to our [code](https://github.com/jayrodge/llm-assistant-cloud-app/) and [YouTube video](https://www.youtube.com/watch?v=09uDCmLzYHA) for Gradio-based RAG Q&A reference application that also uses NVIDIA hosted NIM microservices."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "e4253bd0-4313-4056-95f5-899a180879c2",
   "metadata": {},
   "source": [
    "## Terminology"
   ]
  },
  {
   "attachments": {},
   "cell_type": "markdown",
   "id": "5a084a00-b65d-483a-a7c6-b4c12e4272dd",
   "metadata": {},
   "source": [
    "#### RAG\n",
    "\n",
    "- RAG is a technique for augmenting LLM knowledge with additional data.\n",
    "- LLMs can reason about wide-ranging topics, but their knowledge is limited to the public data up to a specific point in time that they were trained on.\n",
    "- If you want to build AI applications that can reason about private data or data introduced after a model's cutoff date, you need to augment the knowledge of the model with the specific information it needs.\n",
    "- The process of bringing the appropriate information and inserting it into the model prompt is known as retrieval augmented generation (RAG).\n",
    "\n",
    "The preceding summary of RAG originates in the LangChain v0.2 tutorial [Build a RAG App](https://python.langchain.com/v0.2/docs/tutorials/rag/) tutorial in the LangChain v0.2 documentation.\n",
    "\n",
    "For comprehensive information, refer to the LLamaIndex documentation for [Building an LLM Application](https://docs.llamaindex.ai/en/stable/understanding/#:~:text=on%20your%20machine.-,Building%20a%20RAG%20pipeline,-%3A%20Retrieval%2DAugmented%20Generation).\n",
    "\n",
    "#### NIM\n",
    "\n",
    "- [NIM microservices](https://developer.nvidia.com/blog/nvidia-nim-offers-optimized-inference-microservices-for-deploying-ai-models-at-scale/) are containerized microservices that simplify the deployment of generative AI models like LLMs and are optimized to run on NVIDIA GPUs. \n",
    "- NIM microservices support models across domains like chat, embedding, reranking, and more from both the community and NVIDIA.\n",
    "\n",
    "#### NVIDIA API Catalog\n",
    "\n",
    "- [NVIDIA API Catalog](https://build.nvidia.com/explore/discover) is a hosted platform for accessing a wide range of microservices online.\n",
    "- You can test models on the catalog and then export them with an NVIDIA AI Enterprise license for on-premises or cloud deployment\n",
    "\n",
    "#### LlamaIndex Concepts\n",
    "\n",
    " - `Data connectors` ingest your existing data from their native source and format.\n",
    " - `Data indexes` structure your data in intermediate representations that are easy and performant for LLMs to consume.\n",
    " - `Engines` provide natural language access to your data for building context-augmented LLM apps.\n",
    "\n",
    "LlamaIndex also provides integrations like `llms-nvidia`, `embeddings-nvidia` & `nvidia-rerank` to work with NVIDIA microservices."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "ca300278-5ff4-47c4-ab70-c6584ef73c9f",
   "metadata": {},
   "source": [
    "## Installation and Requirements\n",
    "\n",
    "Create a Python environment (preferably with Conda) using Python version 3.10.14. \n",
    "To install Jupyter Lab, refer to the [installation](https://jupyter.org/install) page."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "1b7a52a0-7e5e-4064-9665-cb947d600f84",
   "metadata": {},
   "source": [
    "## Getting Started!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "36287c2e-8708-4006-8adf-851f06cce02d",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Requirements\n",
    "!pip install --upgrade pip\n",
    "!pip install llama-index-core==0.10.50\n",
    "!pip install llama-index-readers-file==0.1.25\n",
    "!pip install llama-index-llms-nvidia==0.1.3\n",
    "!pip install llama-index-embeddings-nvidia==0.1.4\n",
    "!pip install llama-index-postprocessor-nvidia-rerank==0.1.2\n",
    "!pip install ipywidgets==8.1.3"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "04495732-c2db-4c97-91d0-96708814334d",
   "metadata": {},
   "source": [
    "To get started you need a `NVIDIA_API_KEY` to use NVIDIA AI Foundation models:\n",
    "\n",
    "1) Create a free account with [NVIDIA](https://build.nvidia.com/explore/discover).\n",
    "2) Click on your model of choice.\n",
    "3) Under Input select the Python tab, and click **Get API Key** and then click **Generate Key**.\n",
    "4) Copy and save the generated key as NVIDIA_API_KEY. From there, you should have access to the endpoints."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "bbb51115-79f8-48c3-b3ee-d434916945f6",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Enter your NVIDIA API key:  ········\n"
     ]
    }
   ],
   "source": [
    "import getpass\n",
    "import os\n",
    "\n",
    "if not os.environ.get(\"NVIDIA_API_KEY\", \"\").startswith(\"nvapi-\"):\n",
    "    nvidia_api_key = getpass.getpass(\"Enter your NVIDIA API key: \")\n",
    "    assert nvidia_api_key.startswith(\"nvapi-\"), f\"{nvidia_api_key[:5]}... is not a valid key\"\n",
    "    os.environ[\"NVIDIA_API_KEY\"] = nvidia_api_key"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "25656ab5-0046-4e27-be65-b3d3d547b4c6",
   "metadata": {},
   "source": [
    "## RAG Example using LLM and Embedding"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "54e86bc0-e9c5-4a2b-be0e-7fca0331e886",
   "metadata": {},
   "source": [
    "### 1) Initialize the LLM\n",
    "\n",
    "`llama-index-llms-nvidia`, also known as NVIDIA's LLM connector,\n",
    "allows your connect to and generate from compatible models available on the NVIDIA API catalog.\n",
    "\n",
    "Here we will use **mixtral-8x7b-instruct-v0.1** "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "75f7bdd3-2c6f-4ba2-bd89-175cedbf4f3b",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Settings enables global configuration as a singleton object throughout your application.\n",
    "# Here, it is used to set the LLM, embedding model, and text splitter configurations globally.\n",
    "from llama_index.core import Settings\n",
    "from llama_index.llms.nvidia import NVIDIA\n",
    "\n",
    "# Here we are using mixtral-8x7b-instruct-v0.1 model from API Catalog\n",
    "Settings.llm = NVIDIA(model=\"mistralai/mixtral-8x7b-instruct-v0.1\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "35cc87a6-2f83-4652-95f1-cf349db8bad6",
   "metadata": {},
   "source": [
    "### 2) Intiatlize the embedding\n",
    "\n",
    "We selected **NV-Embed-QA** as the embedding"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "d88f7838-b9f9-4fc5-8779-84df6cb26017",
   "metadata": {},
   "outputs": [],
   "source": [
    "from llama_index.embeddings.nvidia import NVIDIAEmbedding\n",
    "Settings.embed_model = NVIDIAEmbedding(model=\"NV-Embed-QA\", truncate=\"END\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "b9862f2e-5055-4fe4-818d-708091243d74",
   "metadata": {},
   "source": [
    "### 3) Obtain some toy text dataset\n",
    "Here we are loading a toy data from a text documents and in real-time data can be loaded from various sources. "
   ]
  },
  {
   "cell_type": "markdown",
   "id": "851b16b3-43ac-4269-9f37-05a33efe24fb",
   "metadata": {},
   "source": [
    "Real world documents can be very long, this makes it hard to fit in the context window of many models. Even for those models that could fit the full post in their context window, models can struggle to find information in very long inputs.\n",
    "\n",
    "To handle this we’ll split the Document into chunks for embedding and vector storage."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "804c85f6-181b-4291-a685-d6b378015544",
   "metadata": {},
   "outputs": [],
   "source": [
    "# For this example we load a toy data set (it's a simple text file with some information about Sweden)\n",
    "TOY_DATA_PATH = \"./data/\"\n",
    "\n",
    "from llama_index.core.node_parser import SentenceSplitter\n",
    "from llama_index.core import SimpleDirectoryReader\n",
    "Settings.text_splitter = SentenceSplitter(chunk_size=400)\n",
    "documents = SimpleDirectoryReader(TOY_DATA_PATH).load_data()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "9b0a7da3-b6e7-46f1-9c31-3c6ef5f04d56",
   "metadata": {},
   "source": [
    "Note:\n",
    " - `SimpleDirectoryReader` takes care of storing basic file information such as the filename, filepath, and file type as metadata by default. This metadata can be used to keep track of the source file, allowing us to use it later for citation or metadata filtering."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "f867df18-11c8-45ea-b81c-1603459431f9",
   "metadata": {},
   "source": [
    "### 4) Process the documents into VectorStoreIndex\n",
    "\n",
    "In RAG, your data is loaded and prepared for queries or \"indexed\". User queries act on the index, which filters your data down to the most relevant context. This context and your query then go to the LLM along with a prompt, and the LLM provides a response."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "2d7b2fbd-8cb1-4d68-9659-2426b9ecffe3",
   "metadata": {},
   "outputs": [],
   "source": [
    "from llama_index.core import VectorStoreIndex\n",
    "# When you use from_documents, your Documents are split into chunks and parsed into Node objects\n",
    "# By default, VectorStoreIndex stores everything in memory\n",
    "index = VectorStoreIndex.from_documents(documents)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "3fe85dad-12bb-47d2-a407-9b89b5270d4e",
   "metadata": {},
   "source": [
    "### 5) Create a Query Engine to ask question over your data"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "5de3e07d-5fbe-4fe7-8f23-ed0b082f2413",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Returns a Query engine for this index.\n",
    "query_engine = index.as_query_engine(similarity_top_k=10)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "5aa362c9-48ab-4646-bc29-bc2aca92505d",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      " Sweden is a Northern European country, occupying the eastern part of the Scandinavian Peninsula. It shares borders with Norway to the west and north, Finland to the east, and is linked to Denmark in the southwest by the Öresund Bridge. Sweden is the largest country in Northern Europe and the fifth largest in Europe, with a total area of 449,964 km2. The country stretches between latitudes 55° and 70° N, and mostly between longitudes 11° and 25° E.\n",
      "\n",
      "Sweden's diverse climate is influenced by its varied topography, which includes a long coastline, numerous lakes, vast forested areas, and the Scandes mountain range that separates it from Norway. The capital and largest city is Stockholm.\n",
      "\n",
      "Sweden has a population of approximately 10.5 million people, with the majority residing in urban areas. The country is known for its extensive coastline, numerous lakes, and vast forested areas, as well as its commitment to social welfare, gender equality, and environmental sustainability.\n",
      "\n",
      "Historically, Sweden has maintained a policy of neutrality and non-participation in military alliances. However, it has recently moved towards cooperation with NATO.\n",
      "\n",
      "Sweden is a highly developed country, ranked seventh in the Human Development Index. It is a constitutional monarchy and parliamentary democracy, with legislative power vested in the 349-member unicameral Riksdag. The country is known for its high standard of living, universal health care, and tertiary education for its citizens.\n",
      "\n",
      "The official language of Sweden is Swedish, a North Germanic language closely related to Danish and Norwegian. English is widely spoken and understood by a majority of Swedes.\n",
      "\n",
      "Sweden's economy is mixed and largely service-oriented, with a strong emphasis on engineering, telecommunications, automotive, and pharmaceutical industries. The country is home to several multinational corporations, including IKEA, Volvo, Ericsson, and H&M.\n",
      "\n",
      "In summary, Sweden is a highly developed, forested country located in Northern Europe, known for its extensive coastline, high standard of living, commitment to social welfare, and diverse climate.\n"
     ]
    }
   ],
   "source": [
    "response = query_engine.query(\n",
    "    \"Tell me about Sweden?\"\n",
    ")\n",
    "print(response)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "c29478b0-0fb1-4678-93cd-b159dc9884a7",
   "metadata": {},
   "source": [
    "## RAG Example with LLM, Embedding & Reranking"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "id": "b88a91ed-5905-474e-8d8e-f5d887638a1d",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      " I don't have information about a \"Nordic Channel\" in the context of your query. However, I can share that the Swedish broadcasting landscape has seen significant developments. Radio broadcasts started in 1925, and in response to pirate radio stations, a second and third network were established in 1954 and 1962, respectively. In 1989, a satellite service known as Kanal 5 began broadcasting, which might be the service you're referring to, although it's not specifically labeled as \"Nordic Channel\" in the information provided.\n"
     ]
    }
   ],
   "source": [
    "# Let's test a more complex query using the above LLM Embedding query_engine and see if the reranker can help.\n",
    "response = query_engine.query(\n",
    "    \"What is Nordic Channel?\"\n",
    ")\n",
    "print(response)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "9d3854c7-68a3-45b4-9e69-2c4e583d651f",
   "metadata": {},
   "source": [
    "### Enhancing accuracy for single data sources\n",
    "\n",
    "This example demonstrates how a re-ranking model can be used to combine retrieval results and improve accuracy during retrieval of documents.\n",
    "\n",
    "Typically, reranking is a critical piece of high-accuracy, efficient retrieval pipelines. Generally, there are two important use cases:\n",
    "\n",
    "- Combining results from multiple data sources\n",
    "- Enhancing accuracy for single data sources\n",
    "\n",
    "Here, we focus on demonstrating only the second use case."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "id": "b7e8677e-a37f-42e2-8fea-4c4413f7d682",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      " The Nordic Channel was a Swedish-language satellite service that was launched in 1989. It is now known as Kanal 5.\n"
     ]
    }
   ],
   "source": [
    "# We will narrow the collection to 40 results and further narrow it to 4 with the reranker.\n",
    "from llama_index.postprocessor.nvidia_rerank import NVIDIARerank\n",
    "\n",
    "reranker_query_engine = index.as_query_engine(\n",
    "    similarity_top_k=40, node_postprocessors=[NVIDIARerank(top_n=4)]\n",
    ")\n",
    "\n",
    "response = reranker_query_engine.query(\n",
    "    \"What is Nordic Channel?\"\n",
    ")\n",
    "print(response)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "aa2c289d-b10f-4bad-bb55-edc779e544f4",
   "metadata": {},
   "source": [
    "#### Note:\n",
    " - In this notebook, we used NVIDIA NIM microservices from the NVIDIA API Catalog.\n",
    " - The above APIs, NVIDIA (llms), NVIDIAEmbedding, and NVIDIARerank, also support self-hosted microservices.\n",
    " - Change the `base_url` to your deployed NIM URL\n",
    " - Example: NVIDIA(model=\"meta/llama3-8b-instruct\", base_url=\"http://your-nim-host-address:8000/v1\")\n",
    " - NIM can be hosted locally using Docker, following the [NVIDIA NIM for LLMs](https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html) documentation."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "d6ea831a-76a5-431f-9b7f-f5bad5cb567b",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Example Code snippet if you want to use a self-hosted NIM\n",
    "from llama_index.llms.nvidia import NVIDIA\n",
    "\n",
    "llm = NVIDIA(model=\"meta/llama3-8b-instruct\", base_url=\"http://your-nim-host-address:8000/v1\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python (rag_notebooks)",
   "language": "python",
   "name": "rag_notebooks"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.14"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
