# RAG in 5 Minutes

This implementation is tied to the [YouTube video on NVIDIA Developer](https://youtu.be/N_OOfkEWcOk).

This is a simple standalone implementation showing a minimal RAG pipeline that uses models available from [NVIDIA API Catalog](https://catalog.ngc.nvidia.com/ai-foundation-models).
The catalog enables you to experience state-of-the-art LLMs accelerated by NVIDIA.
Developers get free credits for 10K requests to any of the models.

The example uses an [integration package to LangChain](https://python.langchain.com/docs/integrations/providers/nvidia) to access the models.
NVIDIA engineers develop, test, and maintain the open source integration.
This example uses a simple [Streamlit](https://streamlit.io/) based user interface and has a one-file implementation.
Because the example uses the models from the NVIDIA API Catalog, you do not need a GPU to run the example.

### Steps

1. Create a python virtual environment and activate it:

   ```comsole
   python3 -m virtualenv genai
   source genai/bin/activate
   ```

1. From the root of this repository, `GenerativeAIExamples`, install the requirements:

   ```console
   pip install -r community/5_mins_rag_no_gpu/requirements.txt
   ```

1. Add your NVIDIA API key as an environment variable:

   ```console
   export NVIDIA_API_KEY="nvapi-*"
   ```

   If you don't already have an API key, visit the [NVIDIA API Catalog](https://build.ngc.nvidia.com/explore/), select on any model, then click on `Get API Key`.

1. Run the example using Streamlit:

   ```console
   streamlit run community/5_mins_rag_no_gpu/main.py
   ```

1. Test the deployed example by going to `http://<host_ip>:8501` in a web browser.

   Click **Browse Files** and select your knowledge source.
   After selecting, click **Upload!** to complete the ingestion process.

You are all set now! Try out queries related to the knowledge base using text from the user interface.
