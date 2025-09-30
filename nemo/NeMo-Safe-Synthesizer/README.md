#   NeMo Safe Synthesizer Example Notebooks


This directory contains the tutorial notebooks for getting started with NeMo Safe Synthesizer.

## 📦 Set Up the Environment

We will use the `uv` python management tool to set up our environment and install the necessary dependencies. If you don't have `uv` installed, you can follow the installation instructions from the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

Install the sdk as follows:

```bash
uv venv
source .venv/bin/activate
uv pip install nemo-microservices[safe-synthesizer]
```


Be sure to select this virtual environment as your kernel when running the notebooks.

## 🚀 Deploying the NeMo Safe Synthesizer Microservice

To run these notebooks, you'll need access to a deployment of the  NeMo Safe Synthesizer microservice. You have two deployment options:


### 🐳 Deploy the NeMo Safe Synthesizer Microservice Locally

Follow our quickstart guide to deploy the NeMo safe synthesizer microservice locally via Docker Compose.

### 🚀 Deploy NeMo Microservices Platform with Helm

Follow the helm installation guide to deploy the microservices platform.
