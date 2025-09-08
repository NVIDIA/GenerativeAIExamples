# 🎨 NeMo Data Designer Tutorial Notebooks

This directory contains the tutorial notebooks for getting started with NeMo Data Designer.

## 🚀 Deploying the NeMo Data Designer Microservice

To run these notebooks, you'll need the NeMo Data Designer microservice. You have two deployment options:

### ⚙️ Using the NeMo Data Designer Managed Service
We have a [managed service of NeMo Data Designer](https://build.nvidia.com/nemo/data-designer) to help you get started quickly.

Please refer to the [intro-tutorials](./intro-tutorials/) notebooks to learn how to connect to this service.

**Note**: This managed service of NeMo Data Designer is intended to only help you get started. As a result, it can only be used to launch `preview` jobs. It can **not** be used to launch long running jobs. If you need to launch long-running jobs please deploy an instance of [NeMo Data Designer locally](#-deploy-the-nemo-data-designer-microservice-locally)


### 🐳 Deploy the NeMo Data Designer Microservice Locally

Alternatively, you can deploy the NeMo Data Designer microservice locally via Docker Compose.

To run the tutorial notebooks in the [advanced](./advanced/), you will need to have NeMo Data Designer deployed locally. Please see the [deployment guide](http://docs.nvidia.com/nemo/microservices/latest/set-up/deploy-as-microservices/data-designer/docker-compose.html) for more details.

## 📦 Set Up the Environment

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
