
# Chat Server
A sample fastapi based server is provided in the workflow so that you can test the chat system in an interactive manner.
This server wraps calls made to different components and orchestrates the entire flow.

This API endpoint allows for several actions:
- [Chat Server](#chat-server)
    - [Upload File Endpoint](#upload-file-endpoint)
    - [Answer Generation Endpoint](#answer-generation-endpoint)
    - [Document Search Endpoint](#document-search-endpoint)
- [Running the chain server](#running-the-chain-server)

The API server swagger schema can be visualized at ``host-ip:8081/docs``.
You can checkout the openapi standard compatible schema for the endpoints supported [here](../chain_server/openapi_schema.json).

The following sections describe the API endpoint actions further with relevant examples.

### Upload File Endpoint
**Summary:** Upload a file. This endpoint should accept a post request with the following JSON in the body:

```json
{
  "file": (file_path, file_binary_data, mime_type),
}
```

The response should be in JSON form. It should be a dictionary with a confirmation message:

```json
{"message": "File uploaded successfully"}
```

**Endpoint:** ``/uploadDocument``

**HTTP Method:** POST

**Request:**

- **Content-Type:** multipart/form-data
- **Schema:** ``Body_upload_file_uploadDocument_post``
- **Required:** Yes

**Request Body Parameters:**
- ``file`` (Type: File) - The file to be uploaded.

**Responses:**
- **200 - Successful Response**

  - Description: The file was successfully uploaded.
  - Response Body: Empty

- **422 - Validation Error**

  - Description: There was a validation error with the request.
  - Response Body: Details of the validation error.



### Answer Generation Endpoint
**Summary:** Generate an answer to a question. This endpoint should accept a post request with the following JSON content in the body:

```json
{
  "question": "USER PROMPT",  // A string of the prompt provided by the user
  "context": "Conversation context to provide to the model.",
  "use_knowledge_base": false,  // A boolean flag to toggle VectorDB lookups
  "num_tokens": 500,  // The maximum number of tokens expected in the response.
}
```

The response should in JSON form. It should simply be a string of the response.

```json
"LLM response"
```

The chat server must also handle responses being retrieved in chunks as opposed to all at once. The client code for response streaming looks like this:

```python
with requests.post(url, stream=True, json=data, timeout=10) as req:
    for chunk in req.iter_content(16):
        yield chunk.decode("UTF-8")
```

**Endpoint:** ``/generate``

**HTTP Method:** POST

**Operation ID:** ``generate_answer_generate_post``

**Request:**

- **Content-Type:** application/json
- **Schema:** ``Prompt``
- **Required:** Yes

**Request Body Parameters:**

-  ``question`` (Type: string) - The question you want to ask.
- ``context`` (Type: string) - Additional context for the question (optional).
- ``use_knowledge_base`` (Type: boolean, Default: true) - Whether to use a knowledge base.
- ``num_tokens`` (Type: integer, Default: 500) - The maximum number of tokens in the response.

**Responses:**

- **200 - Successful Response**

  - Description: The answer was successfully generated.
  - Response Body: An object containing the generated answer.

- **422 - Validation Error**

  - Description: There was a validation error with the request.
  - Response Body: Details of the validation error.

### Document Search Endpoint
**Summary:** Search for documents based on content. This endpoint should accept a post request with the following JSON content in the body:

```json
{
  "content": "USER PROMPT",  // A string of the prompt provided by the user
  "num_docs": "4",  // An integer indicating how many documents should be returned
}
```

The response should in JSON form. It should be a list of dictionaries containing the document score and content.

```json
[
  {
    "score": 0.89123,
    "content": "The content of the relevant chunks from the vector db.",
  },
  ...
]
```


**Endpoint:** ``/documentSearch``
**HTTP Method:** POST

**Operation ID:** ``document_search_documentSearch_post``

**Request:**

- **Content-Type:** application/json
- **Schema:** ``DocumentSearch``
- **Required:** Yes

**Request Body Parameters:**

- ``content`` (Type: string) - The content or keywords to search for within documents.
- ``num_docs`` (Type: integer, Default: 4) - The maximum number of documents to return in the response.

**Responses:**

- **200 - Successful Response**

  - Description: Documents matching the search criteria were found.
  - Response Body: An object containing the search results.

- **422 - Validation Error**

  - Description: There was a validation error with the request.
  - Response Body: Details of the validation error.


# Running the chain server
If the web frontend needs to be stood up manually for development purposes, run the following commands:

- Build the web UI container from source
```
  cd deploy/
  source compose.env
  docker compose build query
```
- Run the container which will start the server
```
  docker compose up query
```

- Open the swagger URL at ``http://host-ip:8081`` to try out the exposed endpoints.