# Developer RAG Chatbot Notebook

## Prerequisites
Before proceeding with this guide, make sure you meet the following prerequisites:

- You should have at least one NVIDIA GPU.

    - NVIDIA driver version 535 or newer. To check the driver version run: ``nvidia-smi --query-gpu=driver_version --format=csv,noheader``.
    - If you are running multiple GPUs they must all be set to the same mode (ie Compute vs. Display). You can check compute mode for each GPU using
    ``nvidia-smi -q -d compute``

### Setup the following

- Docker and Docker-Compose are essential. Please follow the [installation instructions](https://docs.docker.com/engine/install/ubuntu/).

        Note:
            Please do **not** use Docker that is packaged with Ubuntu as the newer version of Docker is required for proper Docker Compose support.

            Make sure your user account is able to execute Docker commands.


- NVIDIA Container Toolkit is also required. Refer to the [installation instructions](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).


- NGC Account and API Key

    - Please refer to [instructions](https://docs.nvidia.com/ngc/gpu-cloud/ngc-overview/index.html) to create an account

    Once your account has been created:

    * Navigate to https://build.nvidia.com/meta/llama3-70b?api-key=true
    * Click "Get API Key" and follow the instructions to generate your API key

- git-lfs
    - Make sure you have [git-lfs](https://git-lfs.github.com) installed.


### Using Nvdia Cloud based LLM's

#### Step 1: Sign up for an NGC Account to access the endpoint

- Follow the above instructions to get access to an API key.

#### Step 2: Set Environment Variables

- Modify ``compose.env`` to set your environment variables. The following variable is required.

    export NVIDIA_API_KEY="nvapi-*"


#### Step 3: Build and Start Containers
- Pull lfs files. This will pull large files from repository.
    ```
        git lfs pull
    ```
- Run the following command to build containers.
    ```
        source community/rag-developer-chatbot/compose.env;   docker compose -f community/rag-developer-chatbot/docker-compose-dev-rag.yaml build
    ```

- Run the following command to start containers.
    ```
         source community/rag-developer-chatbot/compose.env;   docker compose -f community/rag-developer-chatbot/docker-compose-dev-rag.yaml up -d
    ```
    > ⚠️ **NOTE**: It will take a few minutes for the containers to come up. Adding the `-d` flag will have the services run in the background. ⚠️

#### Step 4: Run the notebooks
The notebooks will run on a local JupyterServer on port 8888 (http://localhost:8888)

[Developer RAG Chatbot](../../rapids/notebooks/rapids_notebook.ipynb) is the Developer RAG Chatbot notebook