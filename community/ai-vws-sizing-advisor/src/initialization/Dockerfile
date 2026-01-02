FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests \
    urllib3

# Copy bootstrap script
COPY bootstrap.py /app/bootstrap.py

# Make it executable
RUN chmod +x /app/bootstrap.py

# Create vGPU docs directory
RUN mkdir -p /app/vgpu_docs

# Set default environment variables
ENV ENABLE_VGPU_BOOTSTRAP=true
ENV VGPU_DOCS_PATH=/app/vgpu_docs
ENV BOOTSTRAP_TIMEOUT=300
ENV BOOTSTRAP_MAX_RETRIES=10
ENV BOOTSTRAP_RETRY_DELAY=30

# Run the bootstrap script
CMD ["python", "/app/bootstrap.py"] 