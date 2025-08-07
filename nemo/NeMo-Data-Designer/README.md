# 🎨 NeMo Data Designer Tutorial Notebooks

This directory contains the tutorial notebooks for getting started with NeMo Data Designer.

## 🐳 Deploy the NeMo Data Designer microservice locally

In order to run these notebooks, you must have the NeMo Data Designer microservice deployed locally via docker compose. See the [deployment guide](http://docs.nvidia.com/nemo/microservices/latest/set-up/deploy-as-microservices/data-designer/docker-compose.html) for more details.

## 📦 Set up the environment

We will use the `uv` package manager to set up our environment and install the necessary dependencies. If you don't have `uv` installed, you can follow the installation instructions from the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

Once you have `uv` installed, be sure you are in the `Nemo-Data-Designer` directory and run the following command:

```bash
uv sync
```

This will create a virtual environment and install the necessary dependencies. Activate the virtual environment by running the following command:

```bash
source .venv/bin/activate
```

Be sure to select this virtual environment as your kernel when running the notebooks.
