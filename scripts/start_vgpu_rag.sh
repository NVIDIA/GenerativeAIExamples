#!/bin/bash

# NVIDIA vGPU RAG System Startup Script
# This script automatically deploys the complete vGPU RAG system with pre-loaded documentation

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

# Default settings
ENABLE_BOOTSTRAP=${ENABLE_VGPU_BOOTSTRAP:-true}
SKIP_NIMS=${SKIP_NIMS:-false}
VGPU_DOCS_PATH=${VGPU_DOCS_VOLUME:-./vgpu_docs}
# Export VGPU_DOCS_VOLUME for docker-compose
export VGPU_DOCS_VOLUME=${VGPU_DOCS_PATH}

echo -e "${BLUE}🚀 NVIDIA vGPU RAG System Startup${NC}"
echo "=================================="
echo ""

# Function to print status
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

# Function to check prerequisites
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
        print_warning "NGC_API_KEY is not set. You may need to set it for NIM services."
        echo "export NGC_API_KEY=\"your_key_here\""
    fi
    
    print_status "Prerequisites check completed"
}

# Function to setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    # Create model cache directory
    mkdir -p ~/.cache/model-cache
    export MODEL_DIRECTORY=~/.cache/model-cache
    
    # Set user ID
    export USERID=$(id -u)
    
    # Source vGPU bootstrap environment
    if [ -f "$COMPOSE_DIR/vgpu_bootstrap.env" ]; then
        set -a  # Automatically export all variables
        source "$COMPOSE_DIR/vgpu_bootstrap.env"
        set +a
        print_status "Loaded vGPU bootstrap configuration"
    fi
    
    # Create vGPU docs directory
    mkdir -p "$VGPU_DOCS_PATH"
    print_status "Created vGPU documentation directory: $VGPU_DOCS_PATH"
    
    print_status "Environment setup completed"
}

# Function to start NIMs (optional)
start_nims() {
    if [ "$SKIP_NIMS" = "true" ]; then
        print_warning "Skipping NIMs deployment (SKIP_NIMS=true)"
        return
    fi
    
    print_info "Starting NVIDIA NIM services..."
    
    cd "$PROJECT_ROOT"
    
    # Pull and start NIMs
    docker compose -f deploy/compose/nims.yaml pull --quiet
    USERID=$(id -u) docker compose -f deploy/compose/nims.yaml up -d
    
    print_status "NIMs deployment initiated"
    print_info "Waiting for NIMs to become healthy (this may take up to 30 minutes)..."
    
    # Wait for key services
    wait_for_service "nemoretriever-embedding-ms" "Embedding Service"
    wait_for_service "nemoretriever-ranking-ms" "Ranking Service"
    
    if [ "$SKIP_LLM" != "true" ]; then
        wait_for_service "nim-llm-ms" "LLM Service"
    fi
    
    print_status "NIMs are ready"
}

# Function to wait for a service to be healthy
wait_for_service() {
    local service_name=$1
    local display_name=$2
    local max_attempts=60  # 30 minutes (30 seconds * 60)
    local attempt=0
    
    print_info "Waiting for $display_name to be healthy..."
    
    while [ $attempt -lt $max_attempts ]; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service_name" | grep -q "healthy"; then
            print_status "$display_name is healthy"
            return 0
        fi
        
        sleep 30
        ((attempt++))
        echo -n "."
    done
    
    print_error "$display_name failed to become healthy within timeout"
    return 1
}

# Function to start vector database
start_vectordb() {
    print_info "Starting vector database..."
    
    cd "$PROJECT_ROOT"
    
    docker compose -f deploy/compose/vectordb.yaml pull --quiet
    docker compose -f deploy/compose/vectordb.yaml up -d
    
    # Wait for Milvus to be ready
    print_info "Waiting for Milvus to be ready..."
    sleep 30
    
    local attempt=0
    local max_attempts=20
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:9091/healthz &> /dev/null; then
            print_status "Milvus is ready"
            break
        fi
        sleep 15
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Milvus failed to start within timeout"
        exit 1
    fi
    
    print_status "Vector database is ready"
}

# Function to start ingestion services
start_ingestion() {
    print_info "Starting ingestion services..."
    
    cd "$PROJECT_ROOT"
    
    docker compose -f deploy/compose/docker-compose-ingestor-server.yaml pull --quiet
    docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
    
    # Wait for ingestor server
    print_info "Waiting for ingestor server to be ready..."
    sleep 20
    
    local attempt=0
    local max_attempts=15
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8082/v1/health &> /dev/null; then
            print_status "Ingestor server is ready"
            break
        fi
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Ingestor server failed to start within timeout"
        exit 1
    fi
    
    print_status "Ingestion services are ready"
}

# Function to run vGPU bootstrap
run_bootstrap() {
    if [ "$ENABLE_BOOTSTRAP" != "true" ]; then
        print_warning "vGPU bootstrap disabled (ENABLE_VGPU_BOOTSTRAP=false)"
        return
    fi
    
    print_info "Running vGPU system bootstrap..."
    
    cd "$PROJECT_ROOT"
    
    # Build and run bootstrap
    docker compose -f deploy/compose/docker-compose-bootstrap.yaml build
    docker compose -f deploy/compose/docker-compose-bootstrap.yaml up
    
    # Check if bootstrap succeeded
    if [ $? -eq 0 ]; then
        print_status "vGPU bootstrap completed successfully"
    else
        print_error "vGPU bootstrap failed"
        exit 1
    fi
    
    # Clean up bootstrap container
    docker compose -f deploy/compose/docker-compose-bootstrap.yaml down
}

# Function to start RAG services
start_rag_services() {
    print_info "Starting RAG services..."
    
    cd "$PROJECT_ROOT"
    
    docker compose -f deploy/compose/docker-compose-rag-server.yaml pull --quiet
    docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
    
    # Wait for RAG server
    print_info "Waiting for RAG server to be ready..."
    sleep 15
    
    local attempt=0
    local max_attempts=10
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8081/v1/health &> /dev/null; then
            print_status "RAG server is ready"
            break
        fi
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "RAG server failed to start within timeout"
        exit 1
    fi
    
    print_status "RAG services are ready"
}

# Function to display final status
show_final_status() {
    echo ""
    echo -e "${GREEN}🎉 vGPU RAG System Deployment Complete!${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}ℹ️  Services Status:${NC}"
    docker compose -f "$COMPOSE_DIR/docker-compose-rag-server.yaml" ps --format "table {{.Name}}\t{{.Status}}"
    echo ""
    echo -e "${BLUE}ℹ️  Access URLs:${NC}"
    echo "  • RAG Playground: http://localhost:8090"
    echo "  • RAG API: http://localhost:8081"
    echo "  • Ingestor API: http://localhost:8082"
    echo "  • Milvus Console: http://localhost:9011"
    echo ""
    echo -e "${BLUE}ℹ️  vGPU Knowledge Base:${NC}"
    echo "  • Collection: vgpu_knowledge_base"
    echo "  • Status: All PDFs from $VGPU_DOCS_PATH are automatically loaded"
    echo "  • No manual collection selection needed!"
    echo ""
    echo -e "${BLUE}ℹ️  To add more vGPU documentation:${NC}"
    echo "  1. Place PDF files in: $VGPU_DOCS_PATH"
    echo "  2. Re-run bootstrap: docker compose -f $COMPOSE_DIR/docker-compose-bootstrap.yaml up"
    echo ""
    echo -e "${BLUE}ℹ️  To stop all services:${NC}"
    echo "  $SCRIPT_DIR/stop_vgpu_rag.sh"
}

# Main execution
main() {
    check_prerequisites
    setup_environment
    
    # Start services in order
    if [ "$SKIP_NIMS" != "true" ]; then
        start_nims
    fi
    
    start_vectordb
    start_ingestion
    
    # Run bootstrap after core services are ready
    run_bootstrap
    
    start_rag_services
    
    show_final_status
}

# Handle script arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-nims)
            SKIP_NIMS=true
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
            echo "Options:"
            echo "  --skip-nims       Skip NIM services deployment"
            echo "  --skip-bootstrap  Skip vGPU system bootstrap"
            echo "  --docs-path PATH  Custom path for vGPU documentation"
            echo "  --help           Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  NGC_API_KEY                NVIDIA NGC API key"
            echo "  ENABLE_VGPU_BOOTSTRAP     Enable bootstrap (default: true)"
            echo "  VGPU_DOCS_VOLUME          vGPU docs volume path (default: ./vgpu_docs)"
            echo "  SKIP_NIMS                 Skip NIMs deployment (default: false)"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main 