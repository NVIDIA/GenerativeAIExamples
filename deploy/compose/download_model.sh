#!/bin/bash

mkdir -p /model-store/embedding/cache
mkdir -p /model-store/reranking/cache

mkdir -p $MODEL_DOWNLOAD_PATH
echo "Downloading model in $MODEL_DOWNLOAD_PATH $MODEL_PATH"

if [[ "$MODEL_PATH" == *"huggingface"* ]]; then

    if command -v git &> /dev/null; then
        if [[ $(find $MODEL_DOWNLOAD_PATH -name "config.json" | wc -l) -eq 0 ]]; then
            echo "Downloading from hf"
            GIT_CLONE_PROTECTION_ACTIVE=false git clone $MODEL_PATH $MODEL_DOWNLOAD_PATH
            pushd $MODEL_DOWNLOAD_PATH
            git lfs install --local
            git lfs pull
        fi

    fi

else
    if command -v ngc &> /dev/null; then
        if [[ $(find $MODEL_DOWNLOAD_PATH -name "config.json" | wc -l) -eq 0 ]]; then
            echo "Downloading from ngc"
            echo ngc registry model download-version --dest /model-store $MODEL_PATH
            ngc registry model download-version --dest /model-store $MODEL_PATH
        fi
    fi
fi
