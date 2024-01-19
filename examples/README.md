# Standalone examples

This directory contains standalone examples which has their own seperate end to end workflow like UI, deployment methodologies and tools showcasing different usecases.


## RAG in 5 minutes example

This is a simple standalone implementation showing a a minimalistic RAG pipeline using models available in [Nvidia AI playground.](https://catalog.ngc.nvidia.com/ai-foundation-models)
**NVIDIA AI Foundation** lets developers to experience state of the art LLMs accelerated by NVIDIA. Developers get **free credits for 10K requests** to any of the available models.
It uses [connectors available in Langchain to build the workflow.](https://python.langchain.com/docs/integrations/providers/nvidia) These open source connectors are maintained and tested by NVIDIA engineers.
This example leverages a simple [Streamlit](https://streamlit.io/) based UI and has a one file implementation. This example does not need any GPU to run.

### Steps
1. Create a python virtual environment and activate it
   ```
   python3 -m virtualenv genai
   source genai/bin/activate
   ```

2. Goto the root of this repository `GenerativeAIExamples` and execute below command to install the requirements
   ```
   pip install -r examples/5_mins_rag_no_gpu/requirements.txt
   ```

3. Set your NVIDIA_API_KEY. Follow the steps 1-4 mentioned [here](../docs/rag/aiplayground.md#prepare-the-environment) to get this.
   ```
   export NVIDIA_API_KEY="provide_your_key"
   ```

4. Run the example using streamlit
```
streamlit run examples/5_mins_rag_no_gpu/main.py
```

5. Finally to test the deployed example, goto the URL `http://<host_ip>:8501` in a web browser. Click on `browse files` and select your knowledge source. After selecting click on `Upload!` button to complete the ingestion process.

6. You are all set now! Try out queries pertinent to the knowledge base using text from the UI.
