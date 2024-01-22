# NeMo Framework Inference Server

We use [NeMo Framework Inference Server](https://docs.nvidia.com/nemo-framework/user-guide/latest/deployingthenemoframeworkmodel.html) container which help us to create optimized LLM using TensorRT LLM and deploy using NVIDIA Triton Server for high-performance, cost-effective, and low-latency inference. Within this workflow, We use Llama2 models and LLM Inference Server container contains modules and script required for TRT-LLM conversion of the Llama2 models and deployment using NVIDIA Triton Server.

> ⚠️ **NOTE**: LLM inference server is used by examples which deploys the model on-prem. There are examples in this repository which uses [Nvidia AI foundation models](https://www.nvidia.com/en-in/ai-data-science/foundation-models/) from cloud and may not use this component.


# Running the LLM Inference Server

### Llama2 model deployment:

- Download Llama2 Chat Model Weights from [Meta](https://ai.meta.com/resources/models-and-libraries/llama-downloads/) or [HuggingFace](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf/). You can check [support matrix](support_matrix.md) for GPU requirements for the deployment.

- Update [compose.env](../../deploy/compose/compose.env) with MODEL_DIRECTORY as Llama2 model downloaded path and other model parameters as needed.

- Build the llm inference server container from source
```
  source deploy/compose/compose.env
  docker compose -f deploy/compose/docker-compose.yaml build llm
```
- Run the container which will start the triton server with TRT-LLM optimized Llama2 model
```
  source deploy/compose/compose.env
  docker compose -f deploy/compose/docker-compose.yaml up llm
```

- Once the optimized Llama2 is deployed in Triton Server, clients can send HTTP/REST or gRPC requests directly to Triton Server. Example implmentation of the client can be found [here](../../integrations/langchain/llms/triton_trt_llm.py).
