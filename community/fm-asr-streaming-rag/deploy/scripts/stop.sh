#!/bin/bash
export THIS_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $THIS_DIR/../compose.env

docker compose -f ${DEPLOY_DIR}/docker-compose-nemo-retriever.yaml down
docker compose -f ${DEPLOY_DIR}/docker-compose-milvus-standalone.yaml down
docker compose -f ${DEPLOY_DIR}/docker-compose-nim-llm.yaml down
docker compose -f ${DEPLOY_DIR}/docker-compose-fm-asr.yaml down
docker compose -f ${DEPLOY_DIR}/docker-compose-file-replay.yaml down