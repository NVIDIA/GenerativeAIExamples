# NeMo Framework Inference Server

We use [NeMo Framework Inference Server](https://docs.nvidia.com/nemo-framework/user-guide/latest/deployingthenemoframeworkmodel.html) container which help us to create optimized LLM using TensorRT LLM and deploy using NVIDIA Triton Server for high-performance, cost-effective, and low-latency inference. Within this workflow, We use Llama2 models and LLM Inference Server container contains modules and script required for TRT-LLM conversion of the Llama2 models and deployment using NVIDIA Triton Server.


# Running the LLM Inference Server

To convert Llama2 to TensorRT and host it on Triton Model Server for development purposes, run the following commands:

- Download Llama2 Chat Model Weights from [Meta](https://ai.meta.com/resources/models-and-libraries/llama-downloads/) or [HuggingFace](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf/). You can check [support matrix](../docs/support_matrix.md) for GPU requirements for the deployment.

- Update [compose.env](../deploy/compose.env) with MODEL_DIRECTORY as Llama2 model downloaded path and other model parameters as needed.

- Build the llm inference server container from source
```
  cd deploy/
  source compose.env
  docker compose build triton
```
- Run the container which will start the triton server with TRT-LLM optimized Llama2 model
```
  docker compose up triton
```

- Once the optimized Llama2 is deployed in Triton Server, clients can send HTTP/REST or gRPC requests directly to Triton Server. Example implmentation of the client can be found [here](../llm-inference-server/model_server_client/trt_llm.py).



**Note for checkpoint downloaded using Meta**:

    When downloading model weights from Meta, you can follow the instructions up to the point of downloading the models using ``download.sh``. Meta will download two additional files, namely tokenizer.model and tokenizer_checklist.chk, outside of the model checkpoint directory. Ensure that you copy these files into the same directory as the model checkpoint directory.