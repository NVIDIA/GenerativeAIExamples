#!/bin/bash
export THIS_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
export DEPLOY_DIR="${THIS_DIR}/.."
source ${DEPLOY_DIR}/compose.env

# If using X-forwarding over SSH, uncomment below:
# xhost +local:root  # allows containers to open GUIs when X-forwarding

# Prevents issues with loopback packet transmit from GNURadio to SDR
rmem_max_val=50000000
if [ "$(sysctl -n net.core.rmem_max)" -lt $rmem_max_val ]; then
  echo "Resetting net.core.rmem_max = $rmem_max_val"
  sudo sysctl -w net.core.rmem_max=$rmem_max_val
fi

# Start NIMs
echo "Deploying NIMs..."
declare -A nims
nims=(
    ["asr-nim"]="$ASR_URL,$ASR_PORT"
    ["llm-nim"]="$LLM_URL,$LLM_PORT"
    ["embed-nim"]="$RERANK_URL,$RERANK_PORT"
    ["rerank-nim"]="$EMBED_URL,$EMBED_PORT"
)

SSH_USER=$(whoami) # assume all remote deployments have same user name

# Check if a NIM is up and running
nim_running() {
    local nim_ip=$1
    local nim_port=$2

    curl -s "http://${nim_ip}:${nim_port}/v1/health/ready" > /dev/null
    exit_code=$?
    if [ $exit_code -ne 7 ]; then
        echo 1
    else
        echo 0
    fi
}

# This is a nice function for deploying a NIM either on a remote machine or locally
# NOTE: If the NIM IP is empty, it will not be deployed!
start_nim() {
    local nim_name=$1
    local nim_ip=$2
    local nim_port=$3

    # Skip if IP is empty
    if [ -z "${nim_ip}" ]; then
        echo "No IP provided for ${nim_name}, skipping..."
        return
    elif [ $(nim_running $nim_ip $nim_port) -eq 1 ]; then
        echo "${nim_name} is already running on ${nim_ip}:${nim_port}, skipping..."
        return
    fi

    nim_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-nims.yaml up -d ${nim_name}"
    if [[ ${nim_ip} == "localhost" || ${nim_ip} == "0.0.0.0" ]]; then
        echo "Starting ${nim_name} locally..."
        $nim_cmd
    else
        echo "Starting ${nim_name} on remote machine (${nim_ip})..."
        DOCKER_HOST="ssh://${SSH_USER}@${nim_ip}" $nim_cmd
    fi
}
for nim in "${!nims[@]}"; do
    nim_info=${nims[$nim]}
    IFS=',' read -r nim_ip nim_port <<< "$nim_info"

    start_nim "$nim" "$nim_ip" "$nim_port"
done

# Wait for NIMs
for nim in "${!nims[@]}"; do
    nim_info=${nims[$nim]}
    IFS=',' read -r nim_ip nim_port <<< "$nim_info"

    wait_sec=5
    while true; do
        if [ -z "${nim_ip}" ]; then
            echo "Not running ${nim}."
            break
        elif [ $(nim_running $nim_ip $nim_port) -eq 1 ]; then
            echo "Service $nim is healthy! (exit code: $exit_code)"
            break
        else
            echo "Waiting for $nim, retrying in ${wait_sec}s..."
            sleep $wait_sec  # Wait for wait_sec seconds before retrying
        fi
    done
done

# Start Milvus
milvus_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-milvus.yaml up -d"
if [[ ${MILVUS_STANDALONE_URI} == "localhost" || ${MILVUS_STANDALONE_URI} == "0.0.0.0" ]]; then
    echo "Starting Milvus locally..."
    $milvus_cmd
else
    echo "Starting Milvus on remote machine (${MILVUS_STANDALONE_URI})..."
    DOCKER_HOST="ssh://${SSH_USER}@${MILVUS_STANDALONE_URI}" $milvus_cmd
fi

# Start remaining containers
echo "Deploying SDR, GNU Radio, chain server, and frontend..."
docker compose -f ${DEPLOY_DIR}/docker-compose.yaml up --build