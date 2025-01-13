from typing import Optional, List
from pydantic import BaseModel, Field

class Summary(BaseModel):
    summary: str = Field(description="A summary of the document containing the main points of the document. Can be used to search this document among many others.")

class Entity(BaseModel):
    entity_name: str = Field(description="An entity mentioned in the document, which can be a device, a name, or any significant entity.")

class EntitiesList(BaseModel):
    entities: List[Entity] = Field(description="A list of entities mentioned in the document, such as devices, names, or other significant objects.")

class DocumentMetadata(BaseModel):
    summary: Summary = Field(description="Summary of the document.")
    # entities_list: EntitiesList = Field(description="List of entities mentioned in the document.")

# Example usage:
# doc_instance = DocumentMetadata(
#     summary=Summary(summary="This document discusses the architecture of a neural network..."),
#     entities_list=EntitiesList(
#         entities=[
#             Entity(entity_name="Neural Network"),
#             Entity(entity_name="Convolutional Layer"),
#             Entity(entity_name="Backpropagation")
#         ]
#     )
# )

# Accessing the values:
# summary_value = doc_instance.summary.summary
# entities_values = [entity.entity_name for entity in doc_instance.entities_list.entities]

# Print the extracted values
# print(f"Summary: {summary_value}")
# print(f"Entities: {entities_values}")
