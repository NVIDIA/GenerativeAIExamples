
# NV Ingest imports
from nv_ingest_client.client import Ingestor
from nv_ingest_client.util.file_processing.extract import extract_file_content
from nv_ingest_client.util.milvus import create_nvingest_collection, write_to_nvingest_collection

# LangChain imports
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, NVIDIARerank, ChatNVIDIA
from langchain_milvus import Milvus
from dotenv import load_dotenv

import os


def vectordb_indexer(generated_metadata):
    # Embedding, Storage, Saving to a VectorDB
    sparse = False
    COLLECTION_NAME="nv_ingest_collection"
    print("[INFO] Create Collection", flush=True)
    schema = create_nvingest_collection(COLLECTION_NAME, f"http://milvus:19530", sparse=sparse, dense_dim=1024)
    print("[INFO] Writing to VectorDB Collection Started", flush=True)
    write_to_nvingest_collection(generated_metadata, COLLECTION_NAME, sparse=sparse, milvus_uri=f"http://milvus:19530", minio_endpoint="minio:9000")
    print("[INFO] Writing to VectorDB Complete", flush=True)
    # Should probably return something


   
def ingestor(pdfPath):
    # Takes a PDF file and ingests it, retrives metadata.
    # Logging TBD
    print("[INFO] Ingestion Started for: ", pdfPath, flush=True)
    file_content, file_type = extract_file_content(pdfPath)
    ingestor = (
        Ingestor(message_client_hostname="172.17.0.1", message_client_port=7670)
            .files(pdfPath)
            .extract(
                extract_text=True,
                extract_tables=True,
                extract_charts=True,
                extract_images=True,
            ).split(
                split_by="word",
                split_length=300,
                split_overlap=10,
                max_character_length=5000,
                sentence_window_size=0,
            ).embed( # whether to compute embeddings
                text=True, tables=True
            )
    )
    print("[INFO] Created Ingestion class", flush=True)
    print("[INFO] Getting Metadata: ", pdfPath, flush=True)
    generated_metadata = ingestor.ingest()

    print("[INFO] PDF metadata extracted successfully. Now writing to VectorDB...", flush=True)
    vectordb_indexer(generated_metadata)
    # Should probably return something


    

def rag_chain(user_prompt):
    # Retrieve relevant data from VectorDB and use as context for RAG. 

    # Ensure NVIDIA_API_KEY is set in .env properly
    # key = os.getenv("NVIDIA_API_KEY")
    # print("[INFO] NVIDIA API KEY", key,  flush=True)

    COLLECTION_NAME="nv_ingest_collection" # Should probably be a UDV
    load_dotenv()
    embedding = NVIDIAEmbeddings(model="nvidia/nv-embedqa-e5-v5")

    reranker = NVIDIARerank(model="nvidia/nv-rerankqa-mistral-4b-v3")

    llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct")


    vectorstore = Milvus(
        embedding_function=embedding,
        collection_name=COLLECTION_NAME,
        primary_field = "pk",
        vector_field = "vector",
        text_field="text",
        connection_args={"uri": "http://172.17.0.1:19530"},
    )

    retriever = vectorstore.as_retriever()

    print("[INFO] Retrieval from DB Done")

    template = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Keep the answer concise."
        "\n\n"
        "{context}"
        "Question: {question}"
    )

    prompt = PromptTemplate.from_template(template)

    raga_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    print("User prompt: ",user_prompt)
    response=raga_chain.invoke(user_prompt)
    print("[INFO] RAG Call Complete")

    return response
