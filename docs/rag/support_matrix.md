# GPU Requirements
Large Language Models are a heavily GPU-limited workflow. All LLMs are defined by the number of billions of parameters that make up their networks. For this workflow, we are focusing on the Llama 2 Chat models from Meta. These models come in three different sizes: 7B, 13B, and 70B. All three models perform very well, but the 13B model is a good balance of performance and GPU Memory utilization.

Llama2-7B-Chat requires about 30GB of GPU memory.

Llama2-13B-Chat requires about 50GB of GPU memory.

Llama2-70B-Chat requires about 320GB of GPU memory.

Llama2-7B-Chat AWQ quantized requires about 25GB of GPU memory.

Nemotron-8B-Chat-SFT requires about 100GB of GPU memory.

These resources can be provided by multiple GPUs on the same machine.

To perform retrieval augmentation, another model must be hosted. This model is much smaller and is called an embedding model. It is responsible for converting a sequence of words to a representation in the form of a vector of numbers. This model requires an additional 2GB of GPU memory.

In this workflow, Milvus was selected as the Vector Database. It was selected because Milvus has implemented the NVIDIA RAFT libraries that enable GPU acceleration of vector searches. For the Milvus database, allow an additional 4GB of GPU Memory.

# CPU and Memory Requirements
For development purposes, we recommend that at least 10 CPU Cores and 64 GB of RAM are available.

# Storage Requirements
There are two main drivers for storage consumption in retrieval augmented generation. The model weights and the documents in the vector database. The file size of the model varies on how large the model is.

Llama2-7B-Chat requires about 30GB of storage.

Llama2-13B-Chat requires about 50GB of storage.

Llama2-70B-Chat requires about 150GB of storage.

Nemotron-8B-Chat-SFT requires about 50GB of storage.

The file space needed for the vector database varies by how many documents it will store. For development purposes, allocating 10 GB is plenty.

You will need additionally about 60GB of storage for docker images.
