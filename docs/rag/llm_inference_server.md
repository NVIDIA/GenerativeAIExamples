# NeMo Framework Inference Server

We use [NeMo Framework Inference Server](https://docs.nvidia.com/nemo-framework/user-guide/latest/deployingthenemoframeworkmodel.html) container which help us to create optimized LLM using TensorRT LLM and deploy using NVIDIA Triton Server for high-performance, cost-effective, and low-latency inference. Within this workflow, We use Llama2 models and LLM Inference Server container contains modules and script required for TRT-LLM conversion of the Llama2 models and deployment using NVIDIA Triton Server.


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



### Quantized Llama2 model deployment

- Download Llama2 Chat Model Weights from [Meta](https://ai.meta.com/resources/models-and-libraries/llama-downloads/) or [HuggingFace](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf/). You can check [support matrix](support_matrix.md) for GPU requirements for the deployment.

- For quantization of the Llama2 model using AWQ, first clone the [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/tree/release/0.5.0) repository separately and checkout release/v0.5.0.

   - Also copy the Llama2 model directory downloaded earlier to the TensorRT-LLM repo

```
  git clone https://github.com/NVIDIA/TensorRT-LLM.git
  cp -r <path-to-Llama2-model-directory> TensorRT-LLM/
  cd TensorRT-LLM/
  git checkout release/0.5.0
```

- Now setup the TensorRT-LLM repo seprately using steps [here](https://github.com/NVIDIA/TensorRT-LLM/blob/release/0.5.0/docs/source/installation.md)

- Once the model is downloaded and TensorRT-LLM repo is setup, we can quantize the model using the TensorRT-LLM container.

  - Follow the steps from [here](https://github.com/NVIDIA/TensorRT-LLM/tree/v0.5.0/examples/llama#awq) to quantize using AWQ, run these commands inside the container.

  - While running the quantization script, make sure to point `--model_dir` to your downloaded Llama2 model directory

  - Once the quantization is completed, copy the generated PyTorch (.pt) file inside the model directory

  ```
   cp <quantized-checkpoint>.pt <model-dir>
  ```

- Now, we will come back our repository, follow the steps below to deploy this quantized model using the inference server.

  - Update [compose.env](../../deploy/compose/compose.env) with `MODEL_DIRECTORY` pointing to Llama2 model directory containing the quantized checkpoint.

  - Make sure the qantized PyTorch model (.pt) file generated using above steps is present inside the MODEL_DIRECTORY.



  - Uncomment the QUANTIZATION variable which specifies quantization as "int4_awq" inside the [compose.env](../../deploy/compose/compose.env).
  ```
    export QUANTIZATION="int4_awq"
  ```

**Note for checkpoint downloaded using Meta**:

*When downloading model weights from Meta, you can follow the instructions up to the point of downloading the models using ``download.sh``. Meta will download two additional files, namely `tokenizer.model` and `tokenizer_checklist.chk`, outside of the model checkpoint directory. Ensure that you copy these files into the same directory as the model checkpoint directory.*
