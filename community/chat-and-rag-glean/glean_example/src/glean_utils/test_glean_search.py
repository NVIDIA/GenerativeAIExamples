import os
from glean_example.src.glean_utils.utils import (
    glean_search,
    documents_from_glean_response,
)

api_key =  os.getenv("GLEAN_API_KEY")
base_url = "https://nvidia-be.glean.com/rest/api/v1"

response = glean_search(
    query="us holidays",
    api_key=api_key,
    base_url=base_url,
)

documents = documents_from_glean_response(response)

print(documents)
