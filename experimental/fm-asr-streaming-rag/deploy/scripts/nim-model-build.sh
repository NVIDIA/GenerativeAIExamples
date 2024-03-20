#!/bin/bash
export THIS_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $THIS_DIR/../compose.env

docker compose \
  -f ${DEPLOY_DIR}/docker-compose.yml \
  -f ${DEPLOY_DIR}/docker-compose-nim-build.yml up --build nim