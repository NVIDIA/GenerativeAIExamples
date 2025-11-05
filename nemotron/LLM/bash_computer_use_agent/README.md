# Bash Computer Use Agent with Nemotron

This code contains the implementation of a simple Bash shell agent that can operate the computer. This agent
is implemented in two different ways:

1. **From-scratch implementation**: where we show how to build the agent in pure Python with just the `openai` package as the dependency.
2. **LangGraph implementation**: where we show how the implementation can be simplified by LangGraph. This implementation requires the `lanchain-openai` and `langgraph` packages.

# How to run?

> ⚠️ **DISCLAIMER**: This software can execute arbitrary Bash commands on your system. Use at your own risk. The authors and NVIDIA assume no responsibility for any damage, data loss, or security breaches resulting from its use. By using this software, you acknowledge and accept these risks.

## Step 1: LLM setup

Setup your LLM endpoint in `config.py`:

- `llm_base_url` should point at your NVIDIA Nemotron Nano 9B v2 provider's base URL (or your hosted endpoint, if self-hosting).
- `llm_model_name` should be your NVIDIA Nemotron Nano 9B v2 provider's name for the model (or your hosted endpoint model name, if self-hosting).
- `llm_api_key` should be the API key for your provider (not needed if self-hosting).
- `llm_temperature` and `llm_top_p` are the sampling settings for your model. These are set to reasonable defaults for Nemotron with reasoning on mode.

An example with [`build.nvidia.com`](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2) as the provider.

```
class Config:

    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_model_name: str = "nvidia/nvidia-nemotron-nano-9b-v2"
    llm_api_key: str = "nvapi-XYZ"
    ...
```

> NOTE - You will need to obtain an API key if you're not locally hosting this model. Instructions available on [this page](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2) for `build.nvidia.com` by clicking the `View Code` button.

Next, install the dependencies and run the code.

## Step2: Install the dependencies

Use your favorite package manager to install the dependencies. For example:

```bash
pip install -r requirements.txt
```

## Step 3: Execute!

Choose one to run your Bash Agent:

```bash
python main_from_scratch.py  # From-scratch implementation
```

or

```bash
python main_langgraph.py  # LangGraph implementation
```
