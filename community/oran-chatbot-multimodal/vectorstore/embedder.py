import os
import requests
import json

def nvolve_embedding(content, type="passage"):
    """
    Fetches embeddings for the given content using NVIDIA's API.

    Parameters:
    content (list): A list of strings for which embeddings are required.

    Returns:
    dict: A dictionary containing the response data with embeddings or an error message.
    """
    # API configuration
    api_host = 'https://api.llm.ngc.nvidia.com/v1'
    model_id = 'nre-002-' + type
    url = f'{api_host}/embeddings/{model_id}'
    
    # Authentication
    NGC_API_KEY = os.getenv("NGC_API_KEY")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NGC_API_KEY}",
        "Organization-ID": "bwbg3fjn7she"
    }
    
    # Payload
    payload = {"content": content}
    
    # Making the POST request
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    # Check the response
    if response.status_code == 200:
        print("Successfully sent request.")
        return response.json()
    else:
        print(f"Failed to send request, status code: {response.status_code}")
        return {"error": response.content}

# # Example usage
# content = ["Hello world!", "Another string", "Embedding"]
# embeddings = nvolve_embedding(content)
# e = embeddings["embeddings"]
