#!/bin/bash

mkdir llama2-13b-chat

pip install -U "huggingface_hub[cli]"

huggingface-cli login --token=$HUGGINGFACE_TOKEN --add-to-git-credential

huggingface-cli download meta-llama/Llama-2-13b-chat-hf --local-dir llama2-13b-chat

python3 /opt/NeMo/scripts/nlp_language_modeling/convert_hf_llama_to_nemo.py --in-file=llama2-13b-chat --out-file=llama2-13b-chat.nemo

python3 /opt/NeMo/examples/nlp/language_modeling/megatron_gpt_eval.py gpt_model_file=./llama2-13b-chat.nemo trainer.devices=1 trainer.num_nodes=1 tensor_model_parallel_size=1 pipeline_model_parallel_size=1 server=True
