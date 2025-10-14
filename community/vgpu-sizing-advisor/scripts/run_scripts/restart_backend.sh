#!/bin/bash

# vGPU Sizing Advisor - Backend Restart Script
# Quickly restarts only the RAG backend service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 vGPU Sizing Advisor - Restarting Backend${NC}"
echo "============================================="
echo ""

# Helper functions
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check Docker
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running"
    exit 1
fi

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^rag-server$"; then
    print_error "RAG server container not found"
    echo ""
    print_info "Please start the backend first:"
    echo "  ./scripts/run_scripts/start_app.sh"
    echo ""
    exit 1
fi

# Restart container
print_info "Restarting RAG backend..."
docker restart rag-server

print_info "Waiting for backend to initialize..."
sleep 5

# Check if running
if ! docker ps --format '{{.Names}}' | grep -q "^rag-server$"; then
    print_error "Failed to restart backend"
    echo ""
    print_info "Check logs:"
    echo "  docker logs rag-server"
    echo ""
    exit 1
fi

print_status "Backend container restarted"

# Wait for health check
print_info "Checking backend health..."
for i in {1..30}; do
    if curl -sf http://localhost:8081/v1/health > /dev/null 2>&1; then
        echo ""
        print_status "Backend is healthy and ready!"
        echo ""
        echo -e "${GREEN}Backend Endpoints:${NC}"
        echo "  • API:     http://localhost:8081"
        echo "  • Health:  http://localhost:8081/v1/health"
        echo "  • Models:  http://localhost:8081/v1/available-models"
        echo ""
        echo -e "${BLUE}Recent logs:${NC}"
        docker logs rag-server 2>&1 | tail -10
        echo ""
        exit 0
    fi
    sleep 1
    [ $((i % 5)) -eq 0 ] && echo -n "."
done

echo ""
print_warning "Backend started but health check timeout"
echo ""
print_info "The backend may still be initializing. Check logs:"
echo "  docker logs -f rag-server"
echo ""
exit 1