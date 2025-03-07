import os
from openai import OpenAI
import re
from dotenv import load_dotenv

def clean_response(response):
    cleaned_response = re.sub(r'^\W+', '', response)
    return cleaned_response

def request_nvidia_llama(messages, pdf_context):
    load_dotenv()
    NV_API_KEY = os.getenv("NV_API_KEY")
    print(NV_API_KEY)
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NV_API_KEY
    )
    
    if pdf_context != "":
        messages.append({"role": "system", "content": f"Consider this to be the document uploaded as the context for the question: {pdf_context['text']}"})
    
    messages.append({"role": "system", "content": "Answer the last question of this conversation in as little words as possible. Extra explanation is not necessary unless asked in the question."})

    try:
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct",
            messages=messages,
            temperature=0.5,
            top_p=1,
            max_tokens=1024,
            stream=False
        )
        return clean_response(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error: {e}")
        return "NVIDIA API temporarily down :( Please try again in a while."
