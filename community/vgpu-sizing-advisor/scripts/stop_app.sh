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
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
        
        # Always try to stop with sudo (may need elevated permissions)
        sudo -E docker compose -f "$compose_file" down 2>/dev/null || docker compose -f "$compose_file" down 2>/dev/null || true
        
        # Check if still running
        if docker compose -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
            print_warning "$service_name containers still running, trying force stop..."
            sudo -E docker compose -f "$compose_file" down --remove-orphans 2>/dev/null || true
        fi
        
        print_status "$service_name stopped"
    fi
}

# Stop with volumes
stop_service_with_volumes() {
    local compose_file=$1
    local service_name=$2
    
    if [ -f "$compose_file" ]; then
        print_info "Stopping $service_name (removing volumes)..."
        cd "$PROJECT_ROOT"
        
        # Always try to stop with sudo (may need elevated permissions)
        sudo -E docker compose -f "$compose_file" down -v 2>/dev/null || docker compose -f "$compose_file" down -v 2>/dev/null || true
        print_status "$service_name stopped (volumes removed)"
    fi
}

# Kill processes using specific ports
cleanup_ports() {
    print_info "Cleaning up ports..."
    
    # Ports used by the application
    local ports=(8081 8090 8000 3000 19530 9091)
    
    for port in "${ports[@]}"; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            print_warning "Killing processes on port $port: $pids"
            echo "$pids" | xargs -r kill -9 2>/dev/null || true
            sleep 0.5
            
            # Verify port is free
            if lsof -ti:$port >/dev/null 2>&1; then
                print_error "Failed to free port $port"
            else
                print_status "Port $port freed"
            fi
        fi
    done
}

# Cleanup system
cleanup_system() {
    print_info "Cleaning up..."
    
    # Remove bootstrap container if exists
    if docker ps -a --format "{{.Names}}" | grep -q "vgpu-bootstrap"; then
        docker rm -f vgpu-bootstrap 2>/dev/null || true
    fi
    
    # Clean up stopped containers
    print_info "Removing stopped containers..."
    docker container prune -f 2>/dev/null || true
    
    # Clean up dangling images if requested
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        print_info "Removing dangling images..."
        docker image prune -f
        print_status "Images cleaned"
    fi
    
    # Clean up unused volumes
    print_info "Removing unused volumes..."
    docker volume prune -f 2>/dev/null || true
    
    # Clean up networks
    print_info "Cleaning up networks..."
    docker network prune -f 2>/dev/null || true
    
    # Specifically handle nvidia-rag network
    if docker network ls | grep -q "nvidia-rag"; then
        if ! docker network inspect nvidia-rag -f '{{range .Containers}}{{.Name}} {{end}}' | grep -q . 2>/dev/null; then
            docker network rm nvidia-rag 2>/dev/null || true
        fi
    fi
    
    # Clean up build cache (if cleanup images requested)
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        print_info "Cleaning build cache..."
        docker builder prune -f 2>/dev/null || true
    fi
    
    print_status "Docker cleanup completed"
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
                echo "  --force           Force stop all containers (use if normal stop fails)"
                echo "  --help            Show this help message"
                echo ""
                echo "Note: This script automatically frees ports (8081, 8090, 8000, 3000, 19530, 9091)"
                echo ""
                echo "Examples:"
                echo "  $0                    # Normal shutdown"
                echo "  $0 --volumes          # Shutdown and remove data"
                echo "  $0 --force            # Force stop (if containers won't stop)"
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
    print_info "Stopping running services..."
    
    cd "$PROJECT_ROOT"
    
    # Check which services are actually running
    local running_containers=$(docker ps --format "{{.Names}}" 2>/dev/null || true)
    
    # Stop bootstrap if running
    if echo "$running_containers" | grep -q "vgpu-bootstrap"; then
        stop_service "deploy/compose/docker-compose-bootstrap.yaml" "Bootstrap"
    fi
    
    # Stop RAG services (rag-server, rag-playground)
    if echo "$running_containers" | grep -q "rag-"; then
        if [ "$remove_volumes" = "true" ]; then
            stop_service_with_volumes "deploy/compose/docker-compose-rag-server.yaml" "RAG Services"
        else
            stop_service "deploy/compose/docker-compose-rag-server.yaml" "RAG Services"
        fi
    fi
    
    # Stop Ingestion services
    if echo "$running_containers" | grep -q "ingestor"; then
        if [ "$remove_volumes" = "true" ]; then
            stop_service_with_volumes "deploy/compose/docker-compose-ingestor-server.yaml" "Ingestion Services"
        else
            stop_service "deploy/compose/docker-compose-ingestor-server.yaml" "Ingestion Services"
        fi
    fi
    
    # Stop Vector Database (milvus)
    if echo "$running_containers" | grep -q "milvus"; then
        if [ "$remove_volumes" = "true" ]; then
            stop_service_with_volumes "deploy/compose/vectordb.yaml" "Vector Database"
        else
            stop_service "deploy/compose/vectordb.yaml" "Vector Database"
        fi
    fi
    
    # Stop NIMs if running
    if echo "$running_containers" | grep -q "nim"; then
        stop_service "deploy/compose/nims.yaml" "NVIDIA NIMs"
    fi
    
    # Stop Observability if running
    if echo "$running_containers" | grep -q -E "(otel|prometheus|grafana)"; then
        stop_service "deploy/compose/observability.yaml" "Observability"
    fi
    
    # Stop NeMo Guardrails if running
    if echo "$running_containers" | grep -q "nemo"; then
        stop_service "deploy/compose/docker-compose-nemo-guardrails.yaml" "NeMo Guardrails"
    fi
    
    # If containers are still running, notify user
    local remaining=$(docker ps --format "{{.Names}}" | grep -E "(milvus|ingestor|rag|nim|nemo)" 2>/dev/null || true)
    if [ -n "$remaining" ]; then
        print_warning "Some containers are still running. Use --force to stop them:"
        echo "$remaining"
        echo ""
        print_info "Run: ./scripts/stop_app.sh --force"
    else
        print_status "All application containers stopped"
    fi
    
    cleanup_system
    
    # Clean up ports after stopping containers
    cleanup_ports
    
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
    print_info "To start again: ./scripts/start_app.sh"
}

main "$@"

