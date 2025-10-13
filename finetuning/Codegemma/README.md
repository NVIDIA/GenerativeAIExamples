# Codegemma

[CodeGemma](https://ai.google.dev/gemma/docs/codegemma) is a family of decoder-only, text-to-text large language models for programming, built from the same research and technology used to create the [Gemini models](https://blog.google/technology/ai/google-gemini-ai/). CodeGemma models have open weights and offer pre-trained variants and instruction-tuned variants. These models are well-suited for a variety of code generation tasks. Their relatively small size makes it possible to deploy them in environments with limited resources such as a laptop, desktop, or your own cloud infrastructure, democratizing access to state-of-the-art AI models and helping foster innovation for everyone.
For more details, refer the the [CodeGemma model card](https://ai.google.dev/gemma/docs/codegemma/model_card) released by Google.


## Customizing CodeGemma with NeMo Framework

CodeGemma models are compatible with [NeMo Framework](https://docs.nvidia.com/nemo-framework/user-guide/latest/index.html). In this repository we have a notebook that covers steps for customizing CodeGemma.

### Paramater Efficient Fine-Tuning with LoRA

[LoRA tuning](https://arxiv.org/abs/2106.09685) is a parameter efficient method for fine-tuning models, where we freeze the base model parameters and update an auxilliary "adapter" with many fewer weights. At inference time, the adapter weights are combined with the base model weights to produce a new model, customized for a particular use case or dataset. Because this adapter is so much smaller than the base model, it can be trained with far fewer resources than it would take to fine-tune the entire model. In this example, we'll show you how to LoRA-tune small models like the CodeGemma models on a single GPU.

[Get Started Here](./lora.ipynb)

### Supervised Fine-Tuning for Instruction Following (SFT)

Supervised Fine-Tuning (SFT) is the process of fine-tuning all of a model’s parameters on supervised data of inputs and outputs. It teaches the model how to follow user specified instructions and is typically done after model pre-training. This example will describe the steps involved in fine-tuning CodeGemma for instruction following. CodeGemma was released with a checkpoint already fine-tuned for instruction-following, but here we'll learn how we can tune our own model starting with the pre-trained checkpoint to acheive a similar outcome.

Full fine-tuning is more resource intensive than Low Rank adaptation, so for SFT we'll need multiple GPUs, as opposed to the single GPU used for LoRA.

[Get Started Here](./)

## Download the base model

For all of our customization and deployment processes, we'll need to start off with a pre-trained version of CodeGemma in the `.nemo` format. You can download the base model in `.nemo` format from the NVIDIA GPU Cloud, or convert checkpoints from another framework into a `.nemo` file. You can choose to use the 2B parameter or 7B parameter CodeGemma models for this notebook -- the 2B model will be faster to customize, but the 7B model will be more capable.

You can download either model from the NVIDIA NGC Catalog, using the NGC CLI. The instructions to install and configure the NGC CLI can be found [here](https://ngc.nvidia.com/setup/installers/cli).

To download the model, execute one of the following commands, based on which model you want to use:

```bash
ngc registry model download-version "nvidia/nemo/codegemma_2b_base:1.0"
```

or

```bash
ngc registry model download-version "nvidia/nemo/codegemma_7b_base:1.0"
```

## Getting NeMo Framework

NVIDIA NeMo Framework is a generative AI framework built for researchers and PyTorch developers working on large language models (LLMs), multimodal models (MM), automatic speech recognition (ASR), and text-to-speech synthesis (TTS). The primary objective of NeMo is to provide a scalable framework for researchers and developers from industry and academia to more easily implement and design new generative AI models by being able to leverage existing code and pretrained models.

You can pull a container that includes the version of NeMo Framework and all dependencies needed for these notebooks with the following:

```bash
docker pull nvcr.io/nvidia/nemo:24.03.codegemma
```

The best way to run this notebook is from within the container. You can do that by launching the container with the following command

```bash
docker run -it --rm --gpus all --ipc host --network host -v $(pwd):/workspace nvcr.io/nvidia/nemo:24.03.codegemma
```

Then, from within the container, start the jupyter server with

```bash
jupyter lab --no-browser --port=8080 --allow-root --ip 0.0.0.0
```
