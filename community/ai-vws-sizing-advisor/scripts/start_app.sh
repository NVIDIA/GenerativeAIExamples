#!/bin/bash

# vGPU Sizing Advisor - Application Startup Script
# Prerequisites: NGC_API_KEY must be set in environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$PROJECT_ROOT/deploy/compose"

# Default settings - Skip NIMs by default
SKIP_NIMS=true
ENABLE_BOOTSTRAP=${ENABLE_VGPU_BOOTSTRAP:-true}
VGPU_DOCS_PATH=${VGPU_DOCS_VOLUME:-$PROJECT_ROOT/vgpu_docs}

echo -e "${BLUE}🚀 vGPU Sizing Advisor - Starting Application${NC}"
echo "================================================"
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

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose plugin is not installed"
        exit 1
    fi
    
    # Check NGC API Key
    if [ -z "$NGC_API_KEY" ]; then
        print_error "NGC_API_KEY is not set"
        echo ""
        echo "Please set your NGC API key:"
        echo "  export NGC_API_KEY=\"your_key_here\""
        echo ""
        exit 1
    fi
    
    print_status "Prerequisites validated (API key found)"
}

# Docker login
docker_login() {
    print_info "Logging into NVIDIA Container Registry..."
    
    echo "${NGC_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
    
    if [ $? -eq 0 ]; then
        print_status "Docker login successful"
    else
        print_error "Docker login failed"
        exit 1
    fi
}

# Setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    # Source centralized model configuration first (highest priority)
    if [ -f "$COMPOSE_DIR/model_config.env" ]; then
        set -a
        source "$COMPOSE_DIR/model_config.env"
        set +a
        print_status "Loaded centralized model configuration"
    fi
    
    # Source .env file
    if [ -f "$COMPOSE_DIR/.env" ]; then
        set -a
        source "$COMPOSE_DIR/.env"
        set +a
        print_status "Loaded environment from .env"
    fi
    
    # Create model cache directory
    mkdir -p ~/.cache/model-cache
    export MODEL_DIRECTORY=~/.cache/model-cache
    
    # Set user ID
    export USERID=$(id -u)
    
    # Export vGPU docs path
    export VGPU_DOCS_VOLUME="$VGPU_DOCS_PATH"
    
    # Source vGPU bootstrap environment
    if [ -f "$COMPOSE_DIR/vgpu_bootstrap.env" ]; then
        set -a
        source "$COMPOSE_DIR/vgpu_bootstrap.env"
        set +a
    fi
    
    # Create vGPU docs directory
    mkdir -p "$VGPU_DOCS_PATH"
    
    print_status "Environment configured"
}

# Wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local display_name=$2
    local max_attempts=60
    local attempt=0
    
    print_info "Waiting for $display_name..."
    
    while [ $attempt -lt $max_attempts ]; do
        if docker ps --format "{{.Names}}\t{{.Status}}" | grep "$service_name" | grep -q "healthy"; then
            print_status "$display_name is healthy"
            return 0
        fi
        sleep 30
        ((attempt++))
        [ $((attempt % 4)) -eq 0 ] && echo -n "."
    done
    
    print_error "$display_name failed to become healthy"
    return 1
}

# Start vector database
start_vectordb() {
    print_info "Starting vector database..."
    cd "$PROJECT_ROOT"
    
    sudo -E docker compose -f deploy/compose/vectordb.yaml pull --quiet
    sudo -E docker compose -f deploy/compose/vectordb.yaml up -d
    
    print_info "Waiting for Milvus..."
    sleep 30
    
    local attempt=0
    while [ $attempt -lt 20 ]; do
        if curl -f http://localhost:9091/healthz &> /dev/null; then
            print_status "Milvus ready"
            return 0
        fi
        sleep 15
        ((attempt++))
    done
    
    print_error "Milvus failed to start"
    exit 1
}

# Start ingestion services
start_ingestion() {
    print_info "Starting ingestion services..."
    cd "$PROJECT_ROOT"
    
    sudo -E docker compose -f deploy/compose/docker-compose-ingestor-server.yaml pull --quiet
    sudo -E docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d --build
    
    print_info "Waiting for ingestor server..."
    sleep 20
    
    local attempt=0
    while [ $attempt -lt 15 ]; do
        if curl -f http://localhost:8082/v1/health &> /dev/null; then
            print_status "Ingestor server ready"
            return 0
        fi
        sleep 10
        ((attempt++))
    done
    
    print_error "Ingestor server failed to start"
    exit 1
}

# Run bootstrap
run_bootstrap() {
    if [ "$ENABLE_BOOTSTRAP" != "true" ]; then
        print_warning "Bootstrap disabled (ENABLE_VGPU_BOOTSTRAP=false)"
        return
    fi
    
    print_info "Running vGPU system bootstrap..."
    cd "$PROJECT_ROOT"
    
    sudo -E docker compose -f deploy/compose/docker-compose-bootstrap.yaml build
    sudo -E docker compose -f deploy/compose/docker-compose-bootstrap.yaml up
    
    if [ $? -eq 0 ]; then
        print_status "Bootstrap completed"
    else
        print_error "Bootstrap failed"
        exit 1
    fi
    
    sudo -E docker compose -f deploy/compose/docker-compose-bootstrap.yaml down
}

# Start RAG services
start_rag_services() {
    print_info "Starting RAG services..."
    cd "$PROJECT_ROOT"
    
    sudo -E docker compose -f deploy/compose/docker-compose-rag-server.yaml pull --quiet
    sudo -E docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d --build
    
    print_info "Waiting for RAG server..."
    sleep 15
    
    local attempt=0
    while [ $attempt -lt 10 ]; do
        if curl -f http://localhost:8081/v1/health &> /dev/null; then
            print_status "RAG server ready"
            return 0
        fi
        sleep 10
        ((attempt++))
    done
    
    print_error "RAG server failed to start"
    exit 1
}

# Display final status
show_status() {
    echo ""
    echo -e "${GREEN}🎉 Backend Services Started Successfully!${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}📊 Backend Services:${NC}"
    echo "  • RAG API:      http://localhost:8081"
    echo "  • Ingestor API: http://localhost:8082"
    echo "  • Milvus:       http://localhost:9011"
    echo ""
    echo -e "${BLUE}🤖 AI Models:${NC}"
    echo "  • Chat/LLM:     ${APP_LLM_MODELNAME:-nvidia/llama-3.3-nemotron-super-49b-v1}"
    echo "  • Embedding:    ${APP_EMBEDDINGS_MODELNAME:-nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1}"
    echo "  • Config File:  deploy/compose/model_config.env"
    echo ""
    echo -e "${BLUE}📚 Knowledge Base:${NC}"
    echo "  • Collection: vgpu_knowledge_base"
    echo "  • Location:   ./vgpu_docs"
    echo "  • Status:     Auto-loaded"
    echo ""
    echo -e "${GREEN}✨ Next Steps - Start the Frontend:${NC}"
    echo ""
    echo "  1. Open a new terminal"
    echo "  2. Navigate to frontend directory and run:"
    echo ""
    echo -e "${YELLOW}     cd frontend${NC}"
    echo -e "${YELLOW}     npm install${NC}"
    echo -e "${YELLOW}     npm run dev${NC}"
    echo ""
    echo "  3. Then open your browser to: http://localhost:3000"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • Status:          ./scripts/status.sh"
    echo "  • Stop Backend:    ./scripts/stop_app.sh"
    echo "  • Restart App:     ./scripts/restart_app.sh"
    echo "  • Logs:            docker logs -f rag-server"
    echo "  • Change Models:   Edit deploy/compose/model_config.env"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    docker_login
    setup_environment
    
    start_vectordb
    start_ingestion
    run_bootstrap
    start_rag_services
    
    show_status
}

# Handle arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-nims)
            SKIP_NIMS=false
            shift
            ;;
        --skip-bootstrap)
            ENABLE_BOOTSTRAP=false
            shift
            ;;
        --docs-path)
            VGPU_DOCS_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Start the vGPU Sizing Advisor application"
            echo ""
            echo "Options:"
            echo "  --with-nims        Include NIM services (not used by default)"
            echo "  --skip-bootstrap   Skip vGPU system bootstrap"
            echo "  --docs-path PATH   Custom path for vGPU documentation"
            echo "  --help             Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  NGC_API_KEY               NVIDIA NGC API key (required)"
            echo "  ENABLE_VGPU_BOOTSTRAP     Enable bootstrap (default: true)"
            echo "  VGPU_DOCS_VOLUME          vGPU docs path (default: ./vgpu_docs)"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

main
