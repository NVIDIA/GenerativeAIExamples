#!/bin/bash

# Start Grafana and InfluxDB services
echo "Starting Grafana and InfluxDB services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
    echo "📊 Grafana is available at: http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: admin"
    echo "📈 InfluxDB is available at: http://localhost:8086"
    echo ""
    echo "🚀 You can now run the Streamlit app with Grafana integration!"
else
    echo "❌ Failed to start services. Check the logs with: docker-compose logs"
    exit 1
fi 