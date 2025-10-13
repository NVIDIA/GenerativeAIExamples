#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI vWS Sizing Tool - Backend Restart${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if rag-server container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^rag-server$"; then
    echo -e "${RED}Error: rag-server container not found${NC}"
    echo -e "${YELLOW}Please start the backend first using:${NC}"
    echo -e "  docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d"
    exit 1
fi

echo -e "${YELLOW}Restarting backend container...${NC}"
docker restart rag-server

echo ""
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
sleep 3

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^rag-server$"; then
    echo -e "${GREEN}✓ Backend container restarted successfully${NC}"
    echo ""
    
    # Show last few log lines
    echo -e "${BLUE}Recent logs:${NC}"
    docker logs rag-server 2>&1 | tail -10
    echo ""
    
    # Wait for health check
    echo -e "${YELLOW}Checking backend health...${NC}"
    for i in {1..30}; do
        if curl -sf http://localhost:8081/v1/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend is healthy and ready!${NC}"
            echo ""
            echo -e "${GREEN}Backend endpoints:${NC}"
            echo -e "  • RAG API: http://localhost:8081"
            echo -e "  • Health: http://localhost:8081/v1/health"
            echo -e "  • Models: http://localhost:8081/v1/available-models"
            echo ""
            exit 0
        fi
        sleep 1
    done
    
    echo -e "${YELLOW}Warning: Backend started but health check timeout${NC}"
    echo -e "${YELLOW}Check logs with: docker logs rag-server${NC}"
    exit 0
else
    echo -e "${RED}✗ Failed to restart backend container${NC}"
    echo -e "${YELLOW}Check logs with: docker logs rag-server${NC}"
    exit 1
fi

