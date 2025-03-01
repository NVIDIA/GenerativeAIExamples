# AI Podcast Assistant

A comprehensive toolkit for generating detailed notes, summary, and translation of podcast content using the Phi-4-Multimodal LLM with NVIDIA NIM Microservices.

## Overview

This repository contains a Jupyter notebook that demonstrates a complete workflow for processing podcast audio:

1. **Notes generation**: Convert spoken content from podcasts into detailed text notes
2. **Summarization**: Generate concise summaries of the transcribed content
3. **Translation**: Translate both the transcription and summary into different languages

The implementation leverages the powerful Phi-4-Multimodal LLM (5.6B parameters) through NVIDIA's NIM Microservices, enabling efficient processing of long-form audio content.

Learn more about the model [here](https://developer.nvidia.com/blog/latest-multimodal-addition-to-microsoft-phi-slms-trained-on-nvidia-gpus/).

## Features

- **Long Audio Processing**: Automatically chunks long audio files for processing
- **Detailed Notes Generation**: Creates well-formatted, detailed notes from audio content
- **Summarization**: Generates concise summaries capturing key points
- **Translation**: Translates content to multiple languages while preserving formatting
- **File Export**: Saves results as text files for easy sharing and reference

## Requirements

- Python 3.10+
- Jupyter Notebook or JupyterLab
- NVIDIA API Key
- Required Python packages:
  - requests
  - base64
  - pydub
  - Pillow (PIL)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/NVIDIA/GenerativeAIExamples.git
   cd GenerativeAIExamples/community/ai-podcast-assistant
   ```

2. Set up your NVIDIA API key:
   - Sign up for [NVIDIA NIM Microservices](https://build.nvidia.com/explore/discover?signin=true)
   - Generate an [API key](https://build.nvidia.com/microsoft/phi-4-multimodal-instruct?api_key=true)
   - Replace the placeholder in the notebook with your API key

## Usage

1. Open the Jupyter notebook:
   ```bash
   jupyter notebook ai-podcast-assistant-phi4-mulitmodal.ipynb
   ```

2. Update the `podcast_audio_path` variable with the path to your audio file.

3. Run the notebook cells sequentially to:
   - Process the audio file
   - Generate detailed notes
   - Create a summary
   - Translate the content (optional)
   - Save results to text files

## Example Output

The notebook generates:

1. **Detailed Notes**: Bullet-pointed notes capturing the main content of the podcast
2. **Summary**: A concise paragraph summarizing the key points
3. **Translation**: The notes and summary translated to your chosen language

All outputs are saved as text files for easy reference and sharing.

## Model Details

The Phi-4-Multimodal LLM used in this project has the following specifications:
- **Parameters**: 5.6B
- **Inputs**: Text, Image, Audio
- **Context Length**: 128K tokens
- **Training Data**: 5T text tokens, 2.3M speech hours, 1.1T image-text tokens
- **Supported Languages**: Multilingual text and audio (English, Chinese, German, French, etc.)


## Acknowledgments

- Microsoft for providing access to the Phi-4 multimodal
- NVIDIA for providing access to the NIM microservices preview 

## Contact

For questions, feedback, or collaboration opportunities, please open an issue in this repository.
