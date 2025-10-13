#!/bin/bash

# NVIDIA vGPU RAG System Stop Script
# This script cleanly shuts down all vGPU RAG system services

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

echo -e "${BLUE}🛑 NVIDIA vGPU RAG System Shutdown${NC}"
echo "====================================="
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

# Function to stop services
stop_services() {
    local compose_file=$1
    local service_name=$2
    
    if [ -f "$compose_file" ]; then
        print_info "Stopping $service_name..."
        cd "$PROJECT_ROOT"
        
        if docker compose -f "$compose_file" ps -q | grep -q .; then
            docker compose -f "$compose_file" down
            print_status "$service_name stopped"
        else
            print_warning "$service_name was not running"
        fi
    else
        print_warning "$compose_file not found, skipping $service_name"
    fi
}

# Function to stop and remove volumes (optional)
stop_with_volumes() {
    local compose_file=$1
    local service_name=$2
    
    if [ -f "$compose_file" ]; then
        print_info "Stopping $service_name and removing volumes..."
        cd "$PROJECT_ROOT"
        
        if docker compose -f "$compose_file" ps -q | grep -q .; then
            docker compose -f "$compose_file" down -v
            print_status "$service_name stopped with volumes removed"
        else
            print_warning "$service_name was not running"
        fi
    else
        print_warning "$compose_file not found, skipping $service_name"
    fi
}

# Function to cleanup containers and networks
cleanup_system() {
    print_info "Cleaning up Docker system..."
    
    # Remove vGPU bootstrap container if exists
    if docker ps -a --format "{{.Names}}" | grep -q "vgpu-bootstrap"; then
        docker rm -f vgpu-bootstrap 2>/dev/null || true
        print_status "Removed vGPU bootstrap container"
    fi
    
    # Clean up dangling images if requested
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        print_info "Removing dangling Docker images..."
        docker image prune -f
        print_status "Cleaned up dangling images"
    fi
    
    # Clean up networks
    if docker network ls | grep -q "nvidia-rag"; then
        # Only remove if no containers are using it
        if ! docker network inspect nvidia-rag -f '{{range .Containers}}{{.Name}} {{end}}' | grep -q .; then
            docker network rm nvidia-rag 2>/dev/null || true
            print_status "Removed nvidia-rag network"
        else
            print_warning "nvidia-rag network still in use by other containers"
        fi
    fi
}

# Function to show running containers
show_remaining_containers() {
    print_info "Checking for remaining containers..."
    
    local remaining=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(milvus|ingestor|rag|nim|nemo)" || true)
    
    if [ -n "$remaining" ]; then
        print_warning "Some containers are still running:"
        echo "$remaining"
        echo ""
        print_info "To force stop all containers: docker stop \$(docker ps -q)"
    else
        print_status "All vGPU RAG containers have been stopped"
    fi
}

# Main function
main() {
    # Parse arguments
    local remove_volumes=false
    local cleanup_images=false
    local force_cleanup=false
    
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
                force_cleanup=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --volumes         Remove Docker volumes as well"
                echo "  --cleanup-images  Remove dangling Docker images"
                echo "  --force          Force stop all containers"
                echo "  --help           Show this help message"
                echo ""
                echo "Example:"
                echo "  $0                    # Normal shutdown"
                echo "  $0 --volumes          # Shutdown and remove data"
                echo "  $0 --force            # Force stop everything"
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
    
    # Force stop all containers if requested
    if [ "$force_cleanup" = "true" ]; then
        print_warning "Force stopping all containers..."
        
        local containers=$(docker ps -q --filter "name=milvus" --filter "name=ingestor" --filter "name=rag" --filter "name=nim" --filter "name=nemo")
        if [ -n "$containers" ]; then
            docker stop $containers
            docker rm $containers
            print_status "Force stopped all containers"
        fi
        
        cleanup_system
        show_remaining_containers
        return
    fi
    
    # Stop services in reverse order
    print_info "Shutting down vGPU RAG services..."
    
    # Stop bootstrap if running
    stop_services "deploy/compose/docker-compose-bootstrap.yaml" "vGPU Bootstrap"
    
    # Stop RAG services
    if [ "$remove_volumes" = "true" ]; then
        stop_with_volumes "deploy/compose/docker-compose-rag-server.yaml" "RAG Services"
    else
        stop_services "deploy/compose/docker-compose-rag-server.yaml" "RAG Services"
    fi
    
    # Stop ingestion services
    if [ "$remove_volumes" = "true" ]; then
        stop_with_volumes "deploy/compose/docker-compose-ingestor-server.yaml" "Ingestion Services"
    else
        stop_services "deploy/compose/docker-compose-ingestor-server.yaml" "Ingestion Services"
    fi
    
    # Stop vector database
    if [ "$remove_volumes" = "true" ]; then
        stop_with_volumes "deploy/compose/vectordb.yaml" "Vector Database"
    else
        stop_services "deploy/compose/vectordb.yaml" "Vector Database"
    fi
    
    # Stop NIMs
    stop_services "deploy/compose/nims.yaml" "NVIDIA NIMs"
    
    # Stop any remaining services
    stop_services "deploy/compose/observability.yaml" "Observability Services"
    stop_services "deploy/compose/docker-compose-nemo-guardrails.yaml" "NeMo Guardrails"
    
    # Cleanup
    cleanup_system
    
    # Show status
    show_remaining_containers
    
    echo ""
    if [ "$remove_volumes" = "true" ]; then
        print_warning "All services stopped and data volumes removed"
        print_info "Note: vGPU documentation in ./vgpu_docs was preserved"
    else
        print_status "All services stopped successfully"
        print_info "Data volumes preserved. Use --volumes to remove them."
    fi
    
    echo ""
    print_info "To restart the system:"
    echo "  ./scripts/start_vgpu_rag.sh"
}

# Run main function
main "$@" 