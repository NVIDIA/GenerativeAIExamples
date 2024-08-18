#!/bin/bash
MODEL_DIR=/path/to/llm/models/
MODEL_PATH="${MODEL_DIR}/mistralai/Mistral-7B-Instruct-v0.2"            # HuggingFace Directory (git cloned)
NIM_MODEL_PATH="${MODEL_DIR}/nim/mistralai/Mistral-7B-Instruct-v0.2"    # where i store my trt files.  this is output of model_repo_gnerator
IMG=nvcr.io/ohlfw0olaadg/ea-participants/nemollm-inference-ms:24.02.rc3
YAML=./configs/mistral-7b-config.yaml

docker run --rm -it --gpus '"device=0"' \
  -v $NIM_MODEL_PATH:/model-store \
  -v $YAML:/model_config.yaml \
  -v $MODEL_PATH:/huggingface-dir \
   $IMG model_repo_generator llm --verbose --yaml_config_file=/model_config.yaml

docker run --rm -it --shm-size=4g --gpus '"device=0"' \
  -v $NIM_MODEL_PATH:/model-store \
  -p 9999:9999 -p 9998:9998 \
   $IMG \
   nemollm_inference_ms --model mistral-7b-chat --openai_port="9999" --nemo_port="9998" --num_gpus=1