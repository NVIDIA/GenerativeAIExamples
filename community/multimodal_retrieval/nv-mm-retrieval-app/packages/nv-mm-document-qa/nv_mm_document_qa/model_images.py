from typing import Optional
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field

# class HashId(BaseModel):
#     image_hash: str = Field(description="Hash identifier of the image that contains the answer to the question")

# class ImageDescription(BaseModel):
#     image_description: str = Field(description="Description of the image that contains the answer to the question")

class Answer(BaseModel):
    answer: str = Field(description="The answer to the question asked by the user.")

class Image(BaseModel):
    image_hash: Optional[str] = Field(None, description="Hash identifier of the image relevant to the question in the document. Return this only if there is an image that contains the answer to the question.")
    image_description: Optional[str] = Field(None, description="Description of the relevant image in the document. Return this only if there is an image that contains the answer to the question.")
    answer: Answer = Field(description="Answer to the question asked by the user and found in the document.")


# image_description = 'The image depicts a diagram related to an InfiniBand network architecture, highlighting the components and their interconnections. Here’s a detailed description: 1. **Top Section**: - There are multiple blocks labeled "InfiniBand QP" and "SmartNIC." These represent the InfiniBand queue pairs (QPs) and Smart Network Interface Cards (SmartNICs) that facilitate high-speed data transfer. 2. **Middle Section**: - Below the SmartNICs, there are blocks labeled "IBConnections," "IBDevice," "IBResources," and "IBCfgs." - "IBConnections" likely represents the connections established for communication. - "IBDevice" refers to the actual hardware devices that handle the InfiniBand communication. - "IBResources" may denote the resources allocated for managing these devices. - "IBCfgs" suggests configuration settings for the InfiniBand devices. 3. **Connections**: - Arrows indicate the flow of connections and data between the components, showing how the SmartNICs connect to the IBConnections and subsequently to the IBDevices. 4. **Bottom Section**: - There are several blocks labeled "Buf," which likely represent buffers in memory used for data storage or transfer. 5. **Memory**: - The bottom part of the diagram indicates a memory section where the buffers are located, suggesting that data is temporarily stored here during processing. Overall, the diagram illustrates the architecture and relationships between various components in an InfiniBand network setup, emphasizing the role of SmartNICs and the configuration of IBDevices.'
#
#
# image_instance = Image(
#     image_hash="52d0108669c946e6ef028be3546373c9",  # Pass as HashId instance
#     image_description=image_description,  # Pass as ImageDescription instance
#     answer=Answer(answer="The image does not provide information about the person's hair...")  # Pass as Answer instance
# )
# #
# image_hash_value = image_instance.image_hash
# image_description_value = image_instance.image_description
# answer_value = image_instance.answer.answer
# #
# # Print the extracted values
# print(f"Image Hash: {image_hash_value}")
# print(f"Image Description: {image_description_value}")
# print(f"Answer: {answer_value}")
