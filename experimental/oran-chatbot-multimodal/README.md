# Multimodal O-RAN RAG Chatbot with NVIDIA NeMo
This repository is designed to make it extremely easy to set up your own retrieval-augmented generation chatbot for ORAN techncial specifications and processes. The backend here calls the NVIDIA NeMo Service, which makes it very easy to deploy on a thin client or Virtual Machine (ie, without a GPU setup).

# Implemented Features
- [RAG in 5 minutes Chatbot Video](https://youtu.be/N_OOfkEWcOk) Setup with NVIDIA AI Playground components
- This bot uses augmented retrieval methods like augmented query, query rewriting, cross encoder reranking and others.
- Source references with options to download the source document
- Analytics through Streamlit at ```/?analytics=on```
- Added user feedback and integrated with Google Sheets or other database
- Fact-check verification of results through a second LLM API call
- Multimodal parsing of documents - images, tables, text through multimodal LLM APIs
- Added simple conversational history with memory and summarization

# Setup O-RAN RAG Chatbot

Before running the pipeline, please ensure that you have the following prerequisites:
- Python version 3.10.12
- <TODO: verify if GPU is necessary> GPU-enabled machine
- NVIDIA API Key

If you do not have a NVIDIA API Key, please follow the steps 1-4 mentioned [here](https://github.com/NVIDIA/GenerativeAIExamples/blob/main/docs/rag/aiplayground.md#prepare-the-environment) to get your key.

The following describes how you can have this chatbot up-and-running in less than 5 minutes.

### Step 1: Create and activate python virtual environment
   ```
   pip install virtualenv 	## if you don't already have virtualenv installed
   python3 -m virtualenv oranbot
   source oranbot/bin/activate
   ```
### Step 2. Clone this repository to a Linux machine

   ```
   git clone <TODO: PUBLIC REPO LINK>
   ```
   Once you have tested this on a local machine, you can [request a VM from IT](https://itss.nvidia.com/) and deploy it there so it can run all the time.
   
   Currently, we are using the internal gitlab repository, which can be downloaded using following command:
   ```
   git clone -b multimodal_oran https://gitlab-master.nvidia.com/sae-industry/telco/ai-workflows/rag/oran_chatbot.git
   ```


### Step 3. Install the requirements
   Goto the root of the oran_chatbot repository, and install the requirements in the virtual environment.
   ```
   pip install -r requirements.txt
   ```

<!-- #5. Follow instructions available [here](https://milvus.io/docs/install_standalone-docker.md#Install-Milvus-standalone-using-Docker-Compose). -->

### Step 4. Setup PowerPoint parsing
If you want to use the PowerPoint parsing feature, you will need LibreOffice. On Ubuntu Linux systems, use the following command to install it.
   ```
   sudo apt install libreoffice
   ```

### Step 5. (Optional) Setup Feedback feature
If you would like to use the "Feedback" feature, you will need a service account for Google Sheets. 
Save your service account credentials file as `service.json` inside the `oran_chatbot` folder.

### Step 6. Setup your NVIDIA API key 
   <!-- <TODO: Check if these API keys are being used internally.> -->
   <!-- We needFollow the steps 1-4 mentioned [here](https://github.com/NVIDIA/GenerativeAIExamples/blob/main/docs/rag/aiplayground.md#prepare-the-environment) to get your NVIDIA API key. -->
   To access NeMo services and language model, we will export the NVIDIA API key to the environment using the following command:
   
   ```
   export NVIDIA_API_KEY="nvapi-b**************"
   ```
   <!-- Now, we will generate an NVIDIA GPU Cloud (NGC) API Key for the NeMo service. You can request/get access for yourself or your team by reading instructions available [here](https://nvidia.sharepoint.com/sites/NemoService/SitePages/Team.aspx). For using this repository, you will need to export the NGC API KEY as an environment variable as shown below.
   
   ```
   export NGC_API_KEY="Y2c2Nm**************"
   ``` -->

<!-- ### Step 7: Download ORAN documents
   <!-- <TODO: Are we using google drive for this? update this section> -->
   <!-- Download the official O-RAN documentations from [here](https://www.o-ran.org/specifications). These documents should be placed inside the `vectorstore/oran` folder. --> 

   <!-- Download these documents in the `vectorstore/oran` file. -->

### Step 7. Run the chatbot using streamlit
   Go to the `oran_chatbot` folder to run the O-RAN RAG chatbot using streamlit.
   ```
   streamlit run Multimodal_Assistant.py --server.port 8011
   ```
   The resulting server can be launched on the the web browser through specified port, i.e., `localhost:8011`. If your machine has ports being forwarded on the public IP, it can be accessed by other people who can use `<IP_ADDR>:<PORT>` to access the chatbot.

   If you are using a remote machine to run this application, you can do port forwarding to your local browser:
   ```
   sudo ufw allow PORT
   ```

   To ssh with port forwarding:
   ```
   ssh -L PORT:IP_ADDR:PORT localhost
   ```

   <!-- To setup the vector database, use the `Create vector DB` button under the `Evaluation Metrics` tab.   
   You can click on `Browse Files` and select your knowledge source. After selecting, click on `Upload!` button to complete the ingestion process. -->

### Step 8. Adding documents and creating vector database

   Before you can run the chatbot, we need to upload our documents to the bot and create a vector database.

   The official O-RAN documentations are available [here](https://www.o-ran.org/specifications). 

   To upload these documents to O-RAN bot, you can use either of the following method:
   - Using streamlit UI, you can navigate to the `Knowledge Base` tab. Select the files using the `Browse Files` button and click on `Upload!` button.
   - Alternatively, you can upload the documents through the backend using following steps:

      - Make a directory named `oran` inside the vectorstore folder using command 
      ```mkdir vectorstore/oran```
      - Move your O-RAN documents inside this folder using `cp /path/to/oran_document /vectorstore/oran`, or `cp /path/to/oran_folder/* /vectorstore/oran`. If you are running the bot through a remote server, you can use `scp` to upload the documents from your local machine to the server.

   Once the documents are uploaded, navigate to the `Evaluation Metrics` tab and click on the `Create vector DB` button. This indexes all the uploaded documents into a vector database.

   You are all set now! Try out queries pertinent to the knowledge base using text from the UI.

   #### Add or delete documents from knowledge base

   All the documents in the knowledge base are shown in the drop-down menu of `Knowledge Base` tab. 
   
   If you want to add more documents to your existing knowledge base, navigate to the `Knowledge Base` tab, select the files using the `Browse Files` button and click on `Upload!` button. Finally, click on the `Re-train Multimodal ORAN Assistant' button to complete the ingestion process.

   You can delete files from your knowledge base using the `Delete File` button. The default password to delete files is `avfleetengineering`, and can be changed using `1_Knowledge_Base.py` file inside `pages` folder.
  
   **Warning:** The `Create vector DB` button overwrites any existing vector database, and creates a new vector database using documents available in the `vectorstore/oran` folder. To upload additional documents to your database, always use the `Re-train Multimodal ORAN Assistant` button.


### Step 9. Evaluating the chatbot

   Once our chatbot is running, we can use the evaluation scripts to test its performance.
   
   The `Run synthetic data generation` button in `Evaluation Metrics` tab generates a test dataset using the files in knowledge base. Once the synthetic test set is generated, click on the `Generate evaluation metrics` button to see a comprehensive evaluation report for the RAG performance.
   <!-- <TODO: fill this. Mention about regenerating evals pkl file> -->


## Architecture Diagram

Here is how the system is designed:

```mermaid
graph LR
E(User Query) --> A(FRONTEND<br/>Chat UI<br/>Streamlit)
F(O-RAN pdf, ppt,<br/>doc/html) --> G(Image/Table<br>Extraction)
G --> H(Multimodal<br>Embeddings)
B --> D(Streaming<br/>Chat Output)
C(Vector DB) -- Augmented<br/> Prompt--> B((BACKEND<br/>NVIDIA AI Playground<br/>Mixtral 8x7B))
A --Retrieval--> C
H --> C
```

## Component Swapping

All components are designed to be swappable, meaning that it should be easy to replace with something more complex. Here are some options for the same (this repository may not support these, but we can point you to resources if it is something that would be useful for you):

### Frontend
The current implementation of the chatbot uses Streamlit, which makes it very easy to interact with via a WebUI. However, it requires direct access to the machine via the port on which it is streaming.

### Retrieval
This uses the NVIDIA NeMo Retriever model through NVIDIA AI Playground. This is a fine-tuned version of the E5-large-v2 embedding model, and it is commercially viable for use. This maps every user query into a 1024-dim embedding and uses cosine similarity to provide relevant matches. This can be swapped out for various types of retrieval models that can map to different sorts of embeddings, depending on the use case. They can also be fine-tuned further for the specific data being used.

### Vector DB
The vector database being used here is FAISS, a CPU-based embedding database. It can easily be swapped out for numerous other options like ChromaDB, Pinecone, Milvus and others. Some of the options are listed on the [LangChain docs here](https://python.langchain.com/docs/integrations/vectorstores/).

### Prompt Augmentation
<!-- <TODO: We can update this section> -->
Depending on the backend and model, you may need to modify the way in which you format your prompt and chat conversations to interact with the model. The current design considers each query independently. However, if you put the input as a set of user/assistant/user interactions, you can combine multi-turn conversations. This may also require periodic summarization of past context to ensure the chat does not exceed the context length of the model.

### Backend
- Cloud Hosted: The current implementation uses the NVIDIA AI Playground APIs to abstract away the details of the infrastructure through a simple API call. You can also swap this out quickly by deploying in DGX Cloud with NVIDIA GPUs and LLMs.
- On-Prem/Locally Hosted: If you would like to run a similar model locally, it is usually necessary to have significantly powerful hardware (Llama2-70B requires over 100GB of GPU memory) and various optimization toolkits to run inference (TRT-LLM and TensorRT). Smaller models (Llama2-7B, Mistral-7B, etc) are easier to run but may have worse performance.

## Pipeline Enhancement Opportunities:

<!-- <TODO: Do we want to keep this section? maybe reframe it better? maybe something like 'now that we have implemented this, you can try extending it's capabilities by xyz so that it looks more like learning opportunity for users rather than incomplete implementation> -->
### Multimodal Parsing:
Upgrade the current PyMuPDF-based PDF parsing with a more sophisticated parser for improved extraction of images and tables. Employ a high-quality Multimodal Language Model (MLLM) to enhance image descriptions and implement structured data analysis techniques like text2sql or text2pandas for efficient table summarization.

### Evaluation Complexity:
Evaluating multimodal RAG pipelines is intricate due to the independence of each modality (text, images, tables). For complex queries requiring information synthesis across modalities, refining response quality becomes a challenging task. Aim for a comprehensive evaluation approach that captures the intricacies of multimodal interactions.

### Guardrails Implementation:
Implementing robust guardrails for multimodal systems presents unique challenges. Explore the introduction of guardrails for both input and output, tailored to each modality. Identify and address potential vulnerabilities by developing innovative red-teaming methodologies and jailbreak detection mechanisms to enhance overall security and reliability.

### Function-calling Agents:
Empower the Language Model (LLM) by providing access to external APIs. This integration allows the model to augment response quality through structured interactions with existing systems and software, such as leveraging Google Search for enhanced depth and accuracy in replies.

