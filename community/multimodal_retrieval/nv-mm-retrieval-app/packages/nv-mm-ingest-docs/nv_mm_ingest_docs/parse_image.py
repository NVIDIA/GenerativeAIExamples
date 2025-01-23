from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import requests
import base64

import os

nvidia_vision_model = os.environ["NVIDIA_VISION_MODEL"]
nvidia_text_model = os.environ["NVIDIA_TEXT_MODEL"]

system_template = """
Please describe this image in detail.
"""

def call_api_for_image(image_base64, system_template=system_template, backend_llm="openai"):
    """Calls the OpenAI API to extract text from the base64-encoded image."""
    # print("Parsing image %s" % len(image_base64))

    llm_openai = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    llm_nvidia = ChatNVIDIA(
        model=nvidia_vision_model,
        temperature=0,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )


    if backend_llm == "nvidia":
        llm = llm_nvidia
        # print("I am using the NVIDIA Model")
    elif backend_llm == "openai":
        llm = llm_openai
        # print("I am using the OpenAI Model")
    else:
        llm = None


    system_message = SystemMessage(content=system_template)

    human_message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
            },
        ]
    )

    messages = [system_message, human_message]

    # print(messages)


    response = llm.invoke(
        messages
    )

    # print(response.content)

    return response.content






def get_image_base64(image_url):
    try:
        # Send a GET request to the image URL
        response = requests.get(image_url)
        # Check if the request was successful
        if response.status_code == 200:
            # Encode the image content in base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return image_base64
        else:
            return f"Error: Unable to fetch image, status code {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():

# Example usage

    image_url = "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/cisco-550x-series-stackable-managed-switches/images/gss-cliupgrade-05102017-step5.png"
    image_base64 = get_image_base64(image_url)

    response = call_api_for_image(image_base64, system_template=system_template, backend_llm="openai")
    print(response)

if __name__ == "__main__":
    main()