# Building and Deploying LLM Assistants in Cloud

This application implements a GPU-accelerated Retrieval-Augmented Generation (RAG) based Question-Answering system using NVIDIA Inference Microservices (NIMs) and the LlamaIndex framework. It allows users to upload documents, process them, and then ask questions about the content.

## Features

- Document loading and processing
- Vector storage and retrieval using Milvus
- Question-answering capabilities using NIMs
- Interactive chat interface built with Gradio

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/NVIDIA/GenerativeAIExamples.git
   cd GenerativeAIExamples/community/llm_video_series/video_1_llm_assistant_cloud_app
   ```

2. Create a virtual environment (using Python 3.9 as an example):
   - Using `venv`:
      ```
      python3.9 -m venv venv
      source venv/bin/activate
      ```
   - Using `conda`:
      ```
      conda create -n llm-assistant-env python=3.9
      conda activate llm-assistant-env
      ```

3. Install the required Python libraries using the requirements.txt file:
   ```
   pip install -r requirements.txt
   ```

4. Set up your NVIDIA API Key:
   - Sign up for an NVIDIA API Key on [build.nvidia.com](build.nvidia.com) if you haven't already.
   - Set the API key as an environment variable:
     ```
     export NVIDIA_API_KEY='your-api-key-here'
     ```
   - Alternatively, you can directly edit the script and add your API key to the line:
     ```python
     os.environ["NVIDIA_API_KEY"] = 'nvapi-XXXXXXXXXXXXXXXXXXXXXX' #Add NVIDIA API Key
     ```

## Usage

1. Run the script:
   ```
   python app.py
   ```

2. Open the provided URL in your web browser to access the Gradio interface.

3. Use the interface to:
   - Upload document files
   - Load and process the documents
   - Ask questions about the loaded documents

## How It Works

1. **Document Loading**: Users can upload multiple document files through the Gradio interface.

2. **Document Processing**: The application uses LlamaIndex to read and process the uploaded documents, splitting them into chunks.

3. **Embedding and Indexing**: The processed documents are embedded using NVIDIA's embedding model and stored in a Milvus vector database.

4. **Question Answering**: Users can ask questions through the chat interface. The application uses NIM with Llama 3 70B Instruct hosted on cloud to generate responses based on the relevant information retrieved from the indexed documents.

## Customization

You can customize various aspects of the application:

- Change the chunk size for text splitting
- Use different NVIDIA or open-source models for embedding or language modeling
- Adjust the number of similar documents retrieved for each query

## Troubleshooting

If you encounter any issues:

1. Ensure your NVIDIA API Key is correctly set.
2. Check that all required libraries are installed correctly.
3. Verify that the Milvus database is properly initialized.