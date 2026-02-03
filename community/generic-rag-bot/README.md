# Tutorial for a Generic RAG-Based Chatbot

This is a tutorial for how to build your own generic RAG chatbot. It is intended as a foundation for building more complex, domain-specific RAG-based assistants or tools. Note that no local GPU is needed to run this, as it is using NIMs from the NVIDIA NGC catalog.

## Acknowledgements

 - This implementation is based on [Rag in 5 Minutes](https://github.com/NVIDIA/GenerativeAIExamples/tree/main/community/5_mins_rag_no_gpu), with changes primarily made to the UI as well as updates to some outdated libraries, models, and dependencies. 
 - Alyssa Sawyer also contributed to updating and further developing this repo in her project, [Resume RAG Bot](https://github.com/alysawyer/resume-rag-nv).

## Steps

1. Create a python virtual environment and activate it:

   ```console
   python3 -m venv genai
   source genai/bin/activate
   ```

1. From the root of this folder, `generic-rag-chatbot`, install the requirements:

   ```console
   pip install -r requirements.txt
   ```

1. Add your NVIDIA API key as an environment variable:

   ```console
   export NVIDIA_API_KEY="nvapi-*"
   ```

   If you don't already have an API key, visit the NVIDIA API Catalog, select on any model, then click on **Get API Key**.

1. Run the example using Streamlit:

   ```console
   streamlit run main.py
   ```

1. Test the deployed example by going to `http://<host_ip>:8501` in a web browser.

   Click **Browse Files** and select the documents for your knowledge base.
   After selecting, click **Upload!** to complete the ingestion process.