from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
from nv_mm_ingest_docs.url_import import process_urls_and_save
from nv_mm_document_qa.chain import chain_metadata
from langchain_openai import ChatOpenAI



llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=3000)

def import_urls(input_data: dict) -> dict:
    # _input_data = json.loads(input_data)
    urls_list = input_data.get("urls_list")
    # chapter_indices = _input_data.get("best_docs")
    collection_name = input_data.get("collection_name")
    backend_llm = input_data.get("backend_llm")
    imported_documents = process_urls_and_save(urls_list, collection_name, backend_llm)
    # print(context)
    return {"imported_documents": imported_documents, "collection_name": collection_name, "backend_llm": backend_llm}

# if you update this, you MUST also update ../pyproject.toml
# with the new `tool.langserve.export_attr`
chain = RunnableLambda(import_urls)

# result = chain.invoke({"urls_list": ["https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai/"], "collection_name": "blogs", "backend_llm": "openai"})
# print(result)

