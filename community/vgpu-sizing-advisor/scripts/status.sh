#!/bin/bash

# vGPU Sizing Advisor - Status Check Script
# Shows current status of all services and ports

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 vGPU Sizing Advisor - System Status${NC}"
echo "========================================"
echo ""

# Helper functions
print_header() {
    echo -e "${CYAN}$1${NC}"
    echo "----------------------------------------"
}

check_port() {
    local port=$1
    local service=$2
    # Try with and without sudo, and also try netstat/ss as fallback
    local pid=$(sudo lsof -ti:$port 2>/dev/null || lsof -ti:$port 2>/dev/null || ss -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2)
    
    if [ -n "$pid" ]; then
        echo -e "${GREEN}✓${NC} Port $port - $service (PID: $pid)"
        return 0
    else
        # Double check with netstat
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "${GREEN}✓${NC} Port $port - $service (listening)"
            return 0
        else
            echo -e "${RED}✗${NC} Port $port - $service (not listening)"
            return 1
        fi
    fi
}

# Check Docker
print_header "Docker Status"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running"
    exit 1
fi
echo ""

# Check Containers
print_header "Running Containers"
containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(rag|milvus|ingestor|nim|nemo)" || echo "")

if [ -z "$containers" ]; then
    echo -e "${YELLOW}No application containers running${NC}"
else
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(rag|milvus|ingestor|nim|nemo)" | while IFS= read -r line; do
        if echo "$line" | grep -q "NAMES"; then
            echo -e "${CYAN}$line${NC}"
        elif echo "$line" | grep -qi "unhealthy"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -qi "starting"; then
            echo -e "${YELLOW}$line${NC}"
        else
            echo -e "${GREEN}$line${NC}"
        fi
    done
fi
echo ""

# Check Key Ports
print_header "Port Status"
check_port 8081 "RAG API"
check_port 8082 "Ingestor API"
check_port 3000 "Frontend (Dev)"
check_port 19530 "Milvus"
check_port 9091 "Milvus Health"
check_port 9011 "Milvus Console"
echo ""

# Check Services Health
print_header "Service Health Checks"

# RAG API
if curl -sf http://localhost:8081/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} RAG API - Healthy (http://localhost:8081)"
else
    echo -e "${RED}✗${NC} RAG API - Not responding"
fi

# Ingestor API
if curl -sf http://localhost:8082/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ingestor API - Healthy (http://localhost:8082)"
else
    echo -e "${RED}✗${NC} Ingestor API - Not responding"
fi

# Milvus
if curl -sf http://localhost:9091/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Milvus - Healthy (http://localhost:9091)"
else
    echo -e "${RED}✗${NC} Milvus - Not responding"
fi

# Frontend (Dev - npm run dev)
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend - Available (http://localhost:3000)"
else
    echo -e "${YELLOW}⚠${NC}  Frontend - Not running"
fi
echo ""

# Check Collections
print_header "Vector Database Collections"
if curl -sf http://localhost:8082/v1/collections > /dev/null 2>&1; then
    collections=$(curl -s http://localhost:8082/v1/collections | python3 -c "import sys, json; data = json.load(sys.stdin); print('\n'.join([c.get('collection_name', 'unknown') for c in data.get('collections', [])]))" 2>/dev/null || echo "")
    if [ -n "$collections" ]; then
        echo "$collections" | while read -r collection; do
            echo -e "${GREEN}•${NC} $collection"
        done
    else
        echo -e "${YELLOW}No collections found${NC}"
    fi
else
    echo -e "${YELLOW}Cannot query collections (ingestor not responding)${NC}"
fi
echo ""

# Summary
print_header "Quick Actions"
echo "Start backend:    ./scripts/start_app.sh"
echo "Stop backend:     ./scripts/stop_app.sh"
echo "Restart app:      ./scripts/restart_app.sh"
echo "View logs:        docker logs -f rag-server"
echo ""

# Overall Status
print_header "Overall Status"
if docker ps --format "{{.Names}}" | grep -q "^rag-server$" && \
   curl -sf http://localhost:8081/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running and healthy${NC}"
else
    echo -e "${RED}✗ Backend is not fully operational${NC}"
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is accessible at http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠ Frontend is not running${NC}"
    echo -e "${YELLOW}  Start with: cd frontend && npm run dev${NC}"
fi
echo ""

