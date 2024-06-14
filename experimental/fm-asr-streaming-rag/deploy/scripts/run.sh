#!/bin/bash
export THIS_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $THIS_DIR/../compose.env

# Reset
Red='\e[31m'
Yellow='\e[33m'
Cyan='\e[36m'
ResetColor='\e[0m'
logs() {
  echo -e "${Cyan}$1${ResetColor}"
}
info() {
  echo -e "${Yellow}$1${ResetColor}"
}
warn() {
  echo -e "${Red}$1${ResetColor}"
}

# Check NVIDIA_API_KEY
if [ -z "${NVIDIA_API_KEY}" ]; then
  warn "***** WARNING: NVIDIA_API_KEY is not set, NVIDIA Endpoints will not work *****"
fi

# Check for Riva
if [ -z $(docker ps --format '{{.Image}}' | grep "riva-speech") ]; then
  warn "***** WARNING: Riva container not detected, ASR may not be functional *****"
fi

# Retriever / Database
USE_NEMO_RETRIEVER=$(echo "$USE_NEMO_RETRIEVER" | tr '[:upper:]' '[:lower:]')
if [[ "$USE_NEMO_RETRIEVER" == "true" || "$USE_NEMO_RETRIEVER" == "1" ]]; then
  # Start NeMo Retriever Microservice
  retriever_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-nemo-retriever.yaml"
  logs "***** Starting NeMo Retriever Microservice *****"
  info "Use '${retriever_cmd} down' to stop"
  $retriever_cmd up --force-recreate -d
else
  # Start standalone Milvus DB
  retriever_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-milvus-standalone.yaml"
  logs "***** Not using NeMo Retriever Microservice, starting Milvus DB *****"
  info "Use '${retriever_cmd} down' to stop"
  $retriever_cmd up --force-recreate -d
fi

# NIM LLM
DEPLOY_LOCAL_NIM=$(echo "$DEPLOY_LOCAL_NIM" | tr '[:upper:]' '[:lower:]')
if [[ "$DEPLOY_LOCAL_NIM" == "true" || "$DEPLOY_LOCAL_NIM" == "1" ]]; then
  # Start NIM LLM locally
  nim_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-nim-llm.yaml"
  logs "***** Deploying local NIM LLM *****"
  info "Use '${nim_cmd} down' to stop"
  $nim_cmd up -d
else
  logs "***** Not deploying local NIM LLM *****"
fi

# Streaming FM ASR
fm_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-fm-asr.yaml"
logs "***** Starting streaming FM-ASR workflow *****"
info "Use '${fm_cmd} down' to stop"
$fm_cmd up --build -d

# File Replay
if [ -z "${REPLAY_FILE}" ]; then
  logs "***** No replay file provided, skipping *****"
else
  # Start replay
  replay_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-file-replay.yaml"
  logs "***** Starting file replay for file ${REPLAY_FILE} *****"
  info "Use '${replay_cmd} down' to stop"
  $replay_cmd up -d
fi