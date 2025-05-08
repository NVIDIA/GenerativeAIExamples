# Use NVIDIA's AI Workbench base image
FROM nvcr.io/nvidia/ai-workbench/python-cuda120:1.0.3

# Set the working directory in the container
WORKDIR ./

# Copy the application code into the container (optional)
# COPY ./app_code ./app

# Update and install additional system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl  \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/* 

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8888

# ADD entrypoint.sh /usr/local/bin
# ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
