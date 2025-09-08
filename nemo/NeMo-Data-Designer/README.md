# 🎨 NeMo Data Designer Tutorial Notebooks

This directory contains the tutorial notebooks for getting started with NeMo Data Designer.

## 📚 Table of Contents

### 🚀 Intro Tutorials

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [1-the-basics.ipynb](./intro-tutorials/1-the-basics.ipynb) | Learn the basics of Data Designer by generating a simple product review dataset |
| [2-structured-outputs-and-jinja-expressions.ipynb](./intro-tutorials/2-structured-outputs-and-jinja-expressions.ipynb) | Explore advanced data generation using structured outputs and Jinja expressions |
| [3-seeding-with-a-dataset.ipynb](./intro-tutorials/3-seeding-with-a-dataset.ipynb) | Discover how to seed synthetic data generation with an external dataset         |
| [4-custom-model-configs.ipynb](./intro-tutorials/4-custom-model-configs.ipynb) | Master creating and using custom model configurations                           |

### 🎯 Advanced Tutorials

#### 🧑‍🤝‍🧑 Person Samplers

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [person-sampler-tutorial.ipynb](./advanced/person-samplers/person-sampler-tutorial.ipynb) | Master the Person Sampler to generate realistic personal information            |

#### 🏥 Healthcare Datasets

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [clinical-trials.ipynb](./advanced/healthcare-datasets/clinical-trials.ipynb) | Build synthetic clinical trial datasets with realistic PII for testing data protection |
| [insurance-claims.ipynb](./advanced/healthcare-datasets/insurance-claims.ipynb) | Create synthetic insurance claims datasets with realistic claim data and processing information |
| [physician-notes-with-realistic-personal-details.ipynb](./advanced/healthcare-datasets/physician-notes-with-realistic-personal-details.ipynb) | Generate realistic patient data and physician notes with embedded personal information |

#### 🧾 Forms & Documents

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [w2-dataset.ipynb](./advanced/forms/w2-dataset.ipynb) | Generate synthetic W-2 tax form datasets with realistic employee and employer information |

#### 💬 Conversational AI

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [multi-turn-conversation.ipynb](./advanced/multi-turn-chat/multi-turn-conversation.ipynb) | Build synthetic conversational data with realistic person details and multi-turn dialogues |

#### 🖼️ Multimodal

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [visual-question-answering-using-vlm.ipynb](./advanced/multimodal/visual-question-answering-using-vlm.ipynb) | Create visual question answering datasets using Vision Language Models          |

#### ❓ Q&A Generation

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [product-question-answer-generator.ipynb](./advanced/qa-generation/product-question-answer-generator.ipynb) | Build product information datasets with corresponding questions and answers     |

#### 🔍 RAG & Retrieval

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [generate-rag-evaluation-dataset.ipynb](./advanced/rag-examples/generate-rag-evaluation-dataset.ipynb) | Generate diverse RAG evaluation datasets for testing retrieval-augmented generation systems |

#### 🧠 Reasoning

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [reasoning-traces.ipynb](./advanced/reasoning/reasoning-traces.ipynb) | Build synthetic reasoning traces to demonstrate step-by-step problem-solving processes |

#### 💻 Text-to-Code

| Notebook                                          | Description                                                                      |
|---------------------------------------------------|----------------------------------------------------------------------------------|
| [text-to-python.ipynb](./advanced/text-to-code/text-to-python.ipynb) | Generate Python code from natural language instructions with validation and evaluation |
| [text-to-python-evol.ipynb](./advanced/text-to-code/text-to-python-evol.ipynb) | Build advanced Python code generation with evolutionary improvements and iterative refinement |
| [text-to-sql.ipynb](./advanced/text-to-code/text-to-sql.ipynb) | Create SQL queries from natural language descriptions with validation and testing |

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
