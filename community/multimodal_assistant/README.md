# Multimodal RAG Assistant with NVIDIA NeMo
Create a simple example to showcase multimodal RAG. It should be easy to adapt, easy to build on top of and uses NVIDIA AI Foundation Models.

# Implemented Features
- [RAG in 5 minutes Chatbot Video](https://youtu.be/N_OOfkEWcOk) Setup with NVIDIA AI Playground components
- Source references with options to download the source document
- Analytics through Streamlit at ```/?analytics=on```
- Added user feedback and integrated with Google Sheets or other database
- Add fact-check verification of results through a second LLM API call
- Multimodal parsing of documents - images, tables, text through multimodal LLM APIs
- Added simple conversational history with memory and summarization

## Setup Steps

The following describes how you can have this chatbot up-and-running in less than 5 minutes.

### Steps
1. Create a python virtual environment and activate it
   ```
   python3 -m virtualenv genai
   source genai/bin/activate
   ```

2. Goto the root of this repository `GenerativeAIExamples` and execute below command to install the requirements
   ```
   pip install -r community/multimodal_assistant/requirements.txt
   ```

3. Set your NVIDIA_API_KEY. Follow the steps mentioned [here](../../docs/ai-foundation-models.md#get-an-api-key-for-the-mixtral-8x7b-instruct-api-endpoint) to get this.
   ```
   export NVIDIA_API_KEY="provide_your_key"
   ```

4. NOTE: You will need to set up your own hosted Milvus vector database. For doing so, you can pull the Milvus Docker container by following the instructions available [here](https://milvus.io/docs/install_standalone-docker.md#Install-Milvus-standalone-using-Docker-Compose).

5. If you want to use the PowerPoint parsing feature, you will need LibreOffice. On Ubuntu Linux systems, use the command ```sudo apt install libreoffice``` to install it.

6. Note that if you would like to use the "Feedback" feature, you will need a service account for Google Sheets. Save the service account credentials file as service.json in the multimodal_assistant folder.

7. Go to the folder with this code and then run the example using streamlit
```
cd GenerativeAIExamples/community/multimodal_assistant && streamlit run Multimodal_Assistant.py
```

8. Finally to test the deployed example, goto the URL `http://<host_ip>:8501` in a web browser. Click on `browse files` and select your knowledge source. After selecting click on `Upload!` button to complete the ingestion process.

9. You are all set now! Try out queries pertinent to the knowledge base using text from the UI.

The resulting server will launch on a specified port, like localhost:8501. If your machine has ports being forwarded on the public IP, it can be accessed by other people who can use `<IP_ADDR>:<PORT>` to access the chatbot.

To do port forwarding from a remote machine:
```
sudo ufw allow PORT
```

TO ssh with port forwarding:
```
ssh -L PORT:IP_ADDR:PORT localhost
```

## Known Limitations

Once you add documents and re-create the vector database, it will show that it has successfully completed and you can now use it to answer questions. Since the chatbot needs to connect to the newly created connection, you may have to refresh the page, or else you will see a Milvus connection error. Once you refresh it should be able to connect to the collection.

## Architecture Diagram

Here is how the system is designed:

```mermaid
graph LR
E(User Query) --> A(FRONTEND<br/>Chat UI<br/>Streamlit)
F(PDF, PowerPoints,<br/>DOC/HTML) --> G(Image/Table<br>Extraction)
G --> H(Multimodal<br>Embeddings)
B --> D(Streaming<br/>Chat Output)
C(Vector DB) -- Augmented<br/> Prompt--> B((BACKEND<br/>NVIDIA AI Playground<br/>Mixtral 8x7B))
A --Retrieval--> C
H --> C
```

## Component Swapping

All components are designed to be swappable, meaning that it should be easy to replace with something more complex. Here are some options for the same (this repository may not support these, but we can point you to resources if it is something that would be useful for you):

### Frontend
- **Streamlit:** this is the current implementation of the chatbot, which makes it very easy to interact with via a WebUI. However, it requires direct access to the machine via the port on which it is streaming.

### Retrieval
This uses the NVIDIA NeMo Retriever model through NVIDIA AI Playground. This is a fine-tuned version of the E5-large-v2 embedding model, and it is commercially viable for use. This maps every user query into a 1024-dim embedding and uses cosine similarity to provide relevant matches. This can be swapped out for various types of retrieval models that can map to different sorts of embeddings, depending on the use case. They can also be fine-tuned further for the specific data being used.

### Vector DB
The vector database being used here is Milvus, an AI-native and GPU-accelerated embedding database. It can easily be swapped out for numerous other options like ChromaDB, Pinecone, FAISS and others. Some of the options are listed on the [LangChain docs here](https://python.langchain.com/docs/integrations/vectorstores/).

### Prompt Augmentation
Depending on the backend and model, you may need to modify the way in which you format your prompt and chat conversations to interact with the model. The current design considers each query independently. However, if you put the input as a set of user/assistant/user interactions, you can combine multi-turn conversations. This may also require periodic summarization of past context to ensure the chat does not exceed the context length of the model.

### Backend
- Cloud Hosted: The current implementation uses the NVIDIA AI Playground APIs to abstract away the details of the infrastructure through a simple API call. You can also swap this out quickly by deploying in DGX Cloud with NVIDIA GPUs and LLMs.
- On-Prem/Locally Hosted: If you would like to run a similar model locally, it is usually necessary to have significantly powerful hardware (Llama2-70B requires over 100GB of GPU memory) and various optimization toolkits to run inference (TRT-LLM and TensorRT). Smaller models (Llama2-7B, Mistral-7B, etc) are easier to run but may have worse performance.

## Pipeline Enhancement Opportunities:

### Multimodal Parsing:
Upgrade the current PyMuPDF-based PDF parsing with a more sophisticated parser for improved extraction of images and tables. Employ a high-quality Multimodal Language Model (MLLM) to enhance image descriptions and implement structured data analysis techniques like text2sql or text2pandas for efficient table summarization.

### Evaluation Complexity:
Evaluating multimodal RAG pipelines is intricate due to the independence of each modality (text, images, tables). For complex queries requiring information synthesis across modalities, refining response quality becomes a challenging task. Aim for a comprehensive evaluation approach that captures the intricacies of multimodal interactions.

### Guardrails Implementation:
Implementing robust guardrails for multimodal systems presents unique challenges. Explore the introduction of guardrails for both input and output, tailored to each modality. Identify and address potential vulnerabilities by developing innovative red-teaming methodologies and jailbreak detection mechanisms to enhance overall security and reliability.

### Function-calling Agents:
Empower the Language Model (LLM) by providing access to external APIs. This integration allows the model to augment response quality through structured interactions with existing systems and software, such as leveraging Google Search for enhanced depth and accuracy in replies.

