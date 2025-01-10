from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes

from nv_mm_ingest_docs.chain import chain as ingest_docs_chain
from nv_mm_ingest_docs import chain as document_qa_chain
from nv_mm_images.main import router as images_routes
from nv_mm_document_qa.chain_sdg_qa import chain as sdgqa_chain

app = FastAPI()

add_routes(app, ingest_docs_chain, path="/ingest-docs")
add_routes(app, document_qa_chain, path="/document-qa")
add_routes(app, sdgqa_chain, path="/document-sdg")
app.include_router(images_routes)

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)