# Enable Self-Reflection

The RAG Blueprint supports self-reflection capabilities to improve response quality through two key mechanisms:

1. Context Relevance Check: Evaluates and potentially improves retrieved document relevance
2. Response Groundedness Check: Ensures generated responses are well-grounded in the retrieved context

## Configuration

Enable self-reflection by setting the following environment variables:

```bash
# Enable the reflection feature
ENABLE_REFLECTION=true

# Configure reflection parameters
MAX_REFLECTION_LOOP=3                    # Maximum number of refinement attempts (default: 3)
CONTEXT_RELEVANCE_THRESHOLD=1            # Minimum relevance score 0-2 (default: 1)
RESPONSE_GROUNDEDNESS_THRESHOLD=1        # Minimum groundedness score 0-2 (default: 1)
REFLECTION_LLM="mistralai/mixtral-8x22b-instruct-v0.1"  # Model for reflection (default)
REFLECTION_LLM_SERVERURL="nim-llm-mixtral-8x22b:8000"  # Default on-premises endpoint for reflection LLM

# GPU device assignment for reflection service
REFLECTION_MS_GPU_ID="0,1,2,3,4,5,6,7" # Comma-separated GPU device IDs for 8-GPU deployment
```

The reflection feature supports multiple deployment options:

## On-Premises Deployment (Recommended)

### Prerequisites

1. Ensure you have completed the [general prerequisites](quickstart.md#prerequisites) for the RAG Blueprint.

2. Verify you have sufficient GPU resources:
   - **Required**: 8x A100 80GB or H100 80GB GPUs for optimal latency-optimized deployment
   - For detailed GPU requirements and supported model configurations, refer to the [NVIDIA NIM documentation](https://docs.nvidia.com/nim/large-language-models/latest/supported-models.html#mixtral-8x22b-instruct-v0-1).


### Deployment Steps

1. Authenticate Docker with NGC using your NVIDIA API key:

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   echo "${NVIDIA_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
   ```

2. Create a directory to cache the models:

   ```bash
   mkdir -p ~/.cache/model-cache
   export MODEL_DIRECTORY=~/.cache/model-cache
   ```

3. Set the required environment variables:

   ```bash
   # Enable reflection feature
   export ENABLE_REFLECTION=true

   # Specify GPU devices to use (for 8-GPU deployment)
   export REFLECTION_MS_GPU_ID="0,1,2,3,4,5,6,7"
   ```

4. Start the Mixtral 8x22B model service:

   ```bash
    USERID=$(id -u) docker compose -f deploy/compose/nims.yaml --profile mixtral-8x22b up -d
   ```

5. Wait for the Mixtral service to become healthy (this may take up to 30 minutes on first run as the model is downloaded and cached):

   ```bash
   watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
   ```

   Expected output when ready:
   ```
   NAMES                    STATUS
   nim-llm-mixtral-8x22b    Up XX minutes (healthy)
   ```

6. Start the RAG server with reflection enabled:

   ```bash
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

7. Verify all services are running:

   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

8. Test the reflection capability:
   - Access the RAG playground UI at http://localhost:8090

## NVIDIA AI Playground (Alternative)

If you don't have sufficient GPU resources for on-premises deployment, you can use NVIDIA's hosted models:

### Prerequisites

1. Ensure you have completed the [general prerequisites](quickstart.md#prerequisites) for the RAG Blueprint.

2. [Obtain an NVIDIA API key](quickstart.md#obtain-an-api-key) for accessing the hosted models.

### Deployment Steps

1. Set your NVIDIA API key as an environment variable:

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   ```

2. Configure the environment to use NVIDIA hosted models:

   ```bash
   # Enable reflection feature
   export ENABLE_REFLECTION=true

   # Set empty server URL to use NVIDIA hosted API
   export REFLECTION_LLM_SERVERURL=""

   # Choose the reflection model (options below)
   export REFLECTION_LLM="mistralai/mixtral-8x22b-instruct-v0.1"  # Default option
   # export REFLECTION_LLM="meta/llama-3.1-405b-instruct"  # Alternative option
   ```

3. Start the RAG server:

   ```bash
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

4. Verify the service is running:

   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

5. Test the reflection capability:
   - Access the RAG playground UI at http://localhost:8090

[!NOTE]
When using NVIDIA AI Playground models, you must obtain an API key. See [Obtain an API Key](quickstart.md#obtain-an-api-key) for instructions.

## How It Works

### Context Relevance Check

1. The system retrieves initial documents based on the user query
2. A reflection LLM evaluates document relevance on a 0-2 scale:
   - 0: Not relevant
   - 1: Somewhat relevant
   - 2: Highly relevant
3. If relevance is below threshold and iterations remain:
   - The query is rewritten for better retrieval
   - The process repeats with the new query
4. The most relevant context is used for response generation

### Response Groundedness Check

1. The system generates an initial response using retrieved context
2. The reflection LLM evaluates response groundedness on a 0-2 scale:
   - 0: Not grounded in context
   - 1: Partially grounded
   - 2: Well-grounded
3. If groundedness is below threshold and iterations remain:
   - A new response is generated with emphasis on context adherence
   - The process repeats with the new response

## Best Practices

- Start with default thresholds (1) and adjust based on your use case
- Monitor `MAX_REFLECTION_LOOP` to balance quality vs. latency
- Use logging level INFO to observe reflection behavior:
  ```bash
  LOGLEVEL=INFO
  ```
- Feel free to customize the reflection prompts in `src/prompt.yaml`:
  ```yaml
  reflection_relevance_check_prompt: # Evaluates context relevance
  reflection_query_rewriter_prompt:  # Rewrites queries for better retrieval
  reflection_groundedness_check_prompt: # Checks response groundedness
  reflection_response_regeneration_prompt: # Regenerates responses for better grounding
  ```

## Limitations

- Each reflection iteration adds latency to the response
- Higher thresholds may result in more iterations
- Response streaming is not supported during response groundedness checks
- For on-premises deployment:
  - Requires significant GPU resources (8x A100/H100 GPUs recommended)
  - Initial model download time may very based on network bandwith

For more details on implementation, see the [reflection.py](../src/reflection.py) source code.