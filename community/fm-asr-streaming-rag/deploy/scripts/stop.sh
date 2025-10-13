#!/bin/bash
export THIS_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $THIS_DIR/../compose.env

declare -A nims
nims=(
    ["asr-nim"]="$ASR_URL"
    ["llm-nim"]="$LLM_URL"
    ["embed-nim"]="$RERANK_URL"
    ["rerank-nim"]="$EMBED_URL"
)

nim_ips=()

# Function to check if an IP is already in the nim_ips array
is_ip_unique() {
    local ip=$1
    for existing_ip in "${nim_ips[@]}"; do
        if [[ "$existing_ip" == "$ip" ]]; then
            return 1  # IP already exists
        fi
    done
    return 0  # IP is unique
}

# Collect unique IPs
for nim in "${!nims[@]}"; do
    # Check if the IP is already in the nim_ips array
    ip="${nims[$nim]}"
    if [ -z $ip ]; then continue; fi
    if is_ip_unique $ip; then
        nim_ips+=($ip)
    fi
done

SSH_USER=$(whoami) # assume all remote deployments have same user name

# Shutdown NIMs on each IP
nim_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-nims.yaml down"
for ip in "${nim_ips[@]}"; do
    if [[ ${ip} == "localhost" || ${ip} == "0.0.0.0" ]]; then
        echo "Shutting down NIMs locally..."
        $nim_cmd
    else
        echo "Shutting down NIMs on ${ip}..."
        DOCKER_HOST="ssh://${SSH_USER}@${ip}" $nim_cmd
    fi
done

# Start Milvus
milvus_cmd="docker compose -f ${DEPLOY_DIR}/docker-compose-milvus.yaml down"
if [[ ${MILVUS_STANDALONE_URI} == "localhost" || ${MILVUS_STANDALONE_URI} == "0.0.0.0" ]]; then
    echo "Shutting down Milvus locally..."
    $milvus_cmd
else
    echo "Shutting down Milvus on remote machine (${MILVUS_STANDALONE_URI})..."
    DOCKER_HOST="ssh://${SSH_USER}@${MILVUS_STANDALONE_URI}" $milvus_cmd
fi

# Start remaining containers
echo "Deploying SDR, GNU Radio, chain server, and frontend..."
docker compose -f ${DEPLOY_DIR}/docker-compose.yaml down