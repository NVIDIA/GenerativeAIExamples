from typing import Any, Dict, List

# from pydantic import BaseModel, Field
from pydantic import BaseModel, Field

class Document(BaseModel):
    """
    Find the best document id and its corresponding summary answer the provided question
    """
    id: str = Field(..., description="Hash identifier of the document")
    summary: str = Field(..., description="The summary of the document as is")

class BestDocuments(BaseModel):
    """
    List of the best ducoments to answer the question and their corresponding summaries
    """
    documents: List[Document] = Field(..., description="List of best documents")


class Answer(BaseModel):
    answer: str = Field(..., description="Answer to the question posed by the user")