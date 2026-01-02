# 🎨 NeMo Data Designer Tutorial Notebooks

This directory contains tutorial notebooks for getting started with NeMo Data Designer.

## 📦 Set Up the Environment

We will use the `uv` package manager to set up our environment and install the necessary dependencies. If you don't have `uv` installed, follow the installation instructions from the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

Once you have `uv` installed, be sure you are in the `Nemo-Data-Designer` directory and run the following command:

```bash
uv sync
```

This will create a virtual environment and install the necessary dependencies. Activate the virtual environment by running the following command:

```bash
source .venv/bin/activate
```

Be sure to select this virtual environment as your kernel when running the notebooks.

## 🚀 Deploying the NeMo Data Designer Microservice

To run the tutorial notebooks in this repository, you'll need access to a running instance of the NeMo Data Designer microservice.

You have two deployment options:

### 🐳 Self-Hosted Deployment
Deploy the NeMo Data Designer microservice locally via Docker Compose.

Please see the [Installation Options](https://docs.nvidia.com/nemo/microservices/latest/design-synthetic-data-from-scratch-or-seeds/index.html#installation-options) section of the [NeMo Data Designer documentation](https://docs.nvidia.com/nemo/microservices/latest/design-synthetic-data-from-scratch-or-seeds/index.html) for more information.


### ⚙️ Managed Service
We have a [managed service of NeMo Data Designer](https://build.nvidia.com/nemo/data-designer) to help you get started quickly.

**Note**: This managed service can only be used to launch `preview` jobs. It can **not** be used to launch long-running jobs. If you need to launch long-running jobs please deploy an instance of NeMo Data Designer locally.


## 📚 Tutorial Directory

If you find yourself writing Data Designer tutorial notebooks (thank you 🫶), please check out the [TUTORIAL_STYLE_GUIDE.md](./TUTORIAL_STYLE_GUIDE.md) for best practices and style guidelines.

#### Self-hosted tutorials:

  - [Getting Started](./self-hosted-tutorials/getting-started): Learn the foundations of generating synthetic data with Data Designer.

  - [Community Contributions](./self-hosted-tutorials/community-contributions/): Explore diverse use cases and advanced features in community-contributed notebooks.
