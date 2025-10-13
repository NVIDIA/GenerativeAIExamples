# NVIDIA Dynamo Proxy

A lightweight proxy server for the NVIDIA Dynamo LLM server that handles CORS and request forwarding.

## Prerequisites

- Python 3.8 or higher
- Network access to NVIDIA Dynamo server

## Setup

For Unix/macOS:
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

For Windows:
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The proxy can be configured through configuration File (`config.yaml`):
```yaml
# NVIDIA Dynamo Server Configuration
llm:
  # IP will be provided by frontend via X-LLM-IP header
  port: "8000"

# Proxy Configuration
proxy:
  port: "8002"
  cors:
    allow_origins: ["http://localhost:3000"]
    allow_credentials: true
    allow_methods: ["*"]
    allow_headers: ["*", "X-LLM-IP"]

# Server configuration
server:
  # IP will be provided by environment variable or user input
  port: 8002 
```

## Running the Proxy

For Unix/macOS:
```bash
# Make sure you're in the llm-proxy directory
cd backend-dynamo/llm-proxy

# Activate the virtual environment if not already activated
source venv/bin/activate

# Start the proxy server
python proxy.py
```

For Windows:
```bash
# Make sure you're in the llm-proxy directory
cd backend-dynamo\llm-proxy

# Activate the virtual environment if not already activated
.\venv\Scripts\activate

# Start the proxy server
python proxy.py
```

The proxy will start on http://localhost:8003 by default.

## API Endpoints

- `POST /v1/chat/completions`: Forwards chat completion requests to the NVIDIA Dynamo server