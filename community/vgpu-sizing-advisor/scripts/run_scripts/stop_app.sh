#!/bin/bash

# vGPU Sizing Advisor - Application Stop Script
# Cleanly shuts down all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo -e "${BLUE}🛑 vGPU Sizing Advisor - Stopping Application${NC}"
echo "==============================================="
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

# Stop services
stop_service() {
    local compose_file=$1
    local service_name=$2
    
    if [ -f "$compose_file" ]; then
        print_info "Stopping $service_name..."
        cd "$PROJECT_ROOT"
        
        if docker compose -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
            docker compose -f "$compose_file" down
            print_status "$service_name stopped"
        else
            print_warning "$service_name was not running"
        fi
    fi
}

# Stop with volumes
stop_service_with_volumes() {
    local compose_file=$1
    local service_name=$2
    
    if [ -f "$compose_file" ]; then
        print_info "Stopping $service_name (removing volumes)..."
        cd "$PROJECT_ROOT"
        
        if docker compose -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
            docker compose -f "$compose_file" down -v
            print_status "$service_name stopped (volumes removed)"
        else
            print_warning "$service_name was not running"
        fi
    fi
}

# Cleanup system
cleanup_system() {
    print_info "Cleaning up..."
    
    # Remove bootstrap container if exists
    if docker ps -a --format "{{.Names}}" | grep -q "vgpu-bootstrap"; then
        docker rm -f vgpu-bootstrap 2>/dev/null || true
    fi
    
    # Clean up dangling images if requested
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        print_info "Removing dangling images..."
        docker image prune -f
        print_status "Images cleaned"
    fi
    
    # Clean up networks
    if docker network ls | grep -q "nvidia-rag"; then
        if ! docker network inspect nvidia-rag -f '{{range .Containers}}{{.Name}} {{end}}' | grep -q . 2>/dev/null; then
            docker network rm nvidia-rag 2>/dev/null || true
        fi
    fi
}

# Show remaining containers
show_status() {
    local remaining=$(docker ps --format "{{.Names}}" | grep -E "(milvus|ingestor|rag|nim|nemo)" 2>/dev/null || true)
    
    if [ -n "$remaining" ]; then
        print_warning "Some containers are still running:"
        echo "$remaining"
        echo ""
        print_info "To force stop: docker stop \$(docker ps -q)"
    else
        print_status "All services stopped successfully"
    fi
}

# Main function
main() {
    local remove_volumes=false
    local cleanup_images=false
    local force_stop=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --volumes)
                remove_volumes=true
                shift
                ;;
            --cleanup-images)
                cleanup_images=true
                shift
                ;;
            --force)
                force_stop=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Stop the vGPU Sizing Advisor application"
                echo ""
                echo "Options:"
                echo "  --volumes         Remove Docker volumes (deletes data)"
                echo "  --cleanup-images  Remove dangling Docker images"
                echo "  --force           Force stop all containers"
                echo "  --help            Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                    # Normal shutdown"
                echo "  $0 --volumes          # Shutdown and remove data"
                echo "  $0 --force            # Force stop everything"
                echo ""
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    export CLEANUP_IMAGES=$cleanup_images
    
    # Force stop if requested
    if [ "$force_stop" = "true" ]; then
        print_warning "Force stopping all containers..."
        local containers=$(docker ps -q --filter "name=milvus" --filter "name=ingestor" --filter "name=rag" --filter "name=nim" --filter "name=nemo")
        if [ -n "$containers" ]; then
            docker stop $containers 2>/dev/null || true
            docker rm $containers 2>/dev/null || true
            print_status "Force stopped all containers"
        fi
        cleanup_system
        show_status
        return
    fi
    
    # Stop services in reverse order
    stop_service "deploy/compose/docker-compose-bootstrap.yaml" "Bootstrap"
    
    if [ "$remove_volumes" = "true" ]; then
        stop_service_with_volumes "deploy/compose/docker-compose-rag-server.yaml" "RAG Services"
        stop_service_with_volumes "deploy/compose/docker-compose-ingestor-server.yaml" "Ingestion Services"
        stop_service_with_volumes "deploy/compose/vectordb.yaml" "Vector Database"
    else
        stop_service "deploy/compose/docker-compose-rag-server.yaml" "RAG Services"
        stop_service "deploy/compose/docker-compose-ingestor-server.yaml" "Ingestion Services"
        stop_service "deploy/compose/vectordb.yaml" "Vector Database"
    fi
    
    stop_service "deploy/compose/nims.yaml" "NVIDIA NIMs"
    stop_service "deploy/compose/observability.yaml" "Observability"
    stop_service "deploy/compose/docker-compose-nemo-guardrails.yaml" "NeMo Guardrails"
    
    cleanup_system
    show_status
    
    echo ""
    if [ "$remove_volumes" = "true" ]; then
        print_warning "All services stopped and data removed"
        print_info "vGPU documentation preserved in: ./vgpu_docs"
    else
        print_status "All services stopped"
        print_info "Data preserved. Use --volumes to remove."
    fi
    
    echo ""
    print_info "To restart: ./scripts/run_scripts/start_app.sh"
}

main "$@"

