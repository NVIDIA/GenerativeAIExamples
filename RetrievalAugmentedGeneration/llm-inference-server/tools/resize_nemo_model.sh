#!/bin/bash
set -x

MODEL_STORE="$1"
MODEL_IN="$2"
MODEL_IN_DIR=$(cd $(dirname "$MODEL_IN"); pwd)
MODEL_OUT="$3"
MODEL_OUT_DIR=$(cd $(dirname "$MODEL_OUT"); pwd)
TARGET_SIZE="$4"

TRAINING_CONTAINER="nvcr.io/nvaie/nemo-framework-training:23.08.03"

# init
echo $MODEL_IN " -> " $MODEL_OUT
cd "$MODEL_STORE"
mkdir -p "$MODEL_OUT_DIR"

# find tokenizer
tar xvf $MODEL_IN model_config.yaml
mv model_config.yaml "$MODEL_OUT_DIR"
tokenizer=$(grep "tokenizer_model" gpt_8b_strict_skua_bf16_nemo_yi_dong_us_v1.0-tp1/model_config.yaml | awk -F: '{
 print $3 }')
tar xvf $MODEL_IN $tokenizer
mv $tokenizer $MODEL_OUT_DIR

# run conversion
docker run --rm -it --gpus all --ipc host \
    -v $MODEL_STORE:$MODEL_STORE \
    -w $MODEL_STORE \
    $TRAINING_CONTAINER \
    /usr/bin/python3 \
    /opt/NeMo/examples/nlp/language_modeling/megatron_change_num_partitions.py \
    --model_file $MODEL_IN \
    --target_file $MODEL_OUT \
    --tensor_model_parallel_size=-1 \
    --target_tensor_model_parallel_size=$TARGET_SIZE \
    --pipeline_model_parallel_size=-1 \
    --target_pipeline_model_parallel_size=1 \
    --precision=bf16 \
    --tokenizer_model_path $MODEL_OUT_DIR/$tokenizer
