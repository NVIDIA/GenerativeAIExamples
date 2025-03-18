# NVIDIA RAG Blueprint - API Interaction and Deployment Notebooks

## Overview
This repository contains Jupyter notebooks demonstrating the usage of NVIDIA RAG Blueprint APIs.

### Notebooks:
1. **`ingestion_api_usage.ipynb`**: Demonstrates how to interact with the NVIDIA RAG ingestion service, showcasing how to upload and process documents for retrieval-augmented generation (RAG).
2. **`retriever_api_usage.ipynb`**: Illustrates the use of the NVIDIA RAG retriever service, highlighting different querying techniques and retrieval strategies.
3. **`launchable.ipynb`**: A deployment-ready notebook intended for execution within the brev.dev environment.

## Setting Up the Environment
To run these notebooks in a Python virtual environment, follow the steps below:

### 1. Create and Activate a Virtual Environment
```bash
python3 -m virtualenv venv
source venv/bin/activate
```

### 2. Install Dependencies
Ensure you have JupyterLab and required dependencies installed:
```bash
pip3 install jupyterlab
```

### 3. Start JupyterLab
Run the following command to start JupyterLab, allowing access from any IP:
```bash
jupyter lab --allow-root --ip=0.0.0.0 --NotebookApp.token='' --port=8889 --no-browser
```

Once running, you can access JupyterLab by navigating to `http://<your-server-ip>:8889` in your browser.

## Running the Notebooks
- Open JupyterLab in your browser.
- Navigate to the desired notebook and run the cells sequentially.

## Deployment (Brev.dev)
For deploying `launchable.ipynb` in [brev.dev](https://console.brev.dev/environment/new), follow the platform's instructions for executing Jupyter notebooks within a cloud-based environment selected based on the hardware requirements specified in the launchable.

## Notes
- Ensure API keys and credentials are correctly set up before making API requests.
- Modify endpoints or request parameters as necessary to align with your specific use case.

