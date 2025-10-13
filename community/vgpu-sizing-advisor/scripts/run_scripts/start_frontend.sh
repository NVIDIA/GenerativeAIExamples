#!/bin/bash

# vGPU Sizing Advisor - Frontend Startup Script
# Starts the Next.js frontend application

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
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}🎨 vGPU Sizing Advisor - Starting Frontend${NC}"
echo "============================================"
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

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# Check if backend is running
print_info "Checking backend services..."
if ! curl -sf http://localhost:8081/v1/health > /dev/null 2>&1; then
    print_warning "Backend API is not responding on http://localhost:8081"
    echo ""
    print_info "Please start the backend first:"
    echo "  ./scripts/run_scripts/start_app.sh"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
print_info "Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

print_status "Dependencies installed"
echo ""

# Start dev server
print_info "Starting development server..."
print_status "Frontend will be available at: http://localhost:3000"
echo ""

npm run dev

