from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from binary_score_models import GradeAnswer,GradeDocuments,GradeHallucinations
import os

import json

class Nodeoutputs:
    def __init__(self, api_key, base_url, model, prompts_file):
        os.environ["NVIDIA_API_KEY"] = api_key
        self.llm = ChatNVIDIA(base_url=base_url, api_key=api_key, model=model)
        self.prompts = self.load_prompts(prompts_file)
        self.setup_prompts()

    def load_prompts(self, prompts_file):
        with open(prompts_file, 'r') as file:
            return json.load(file)

    def setup_prompts(self):
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts["qa_system_prompt"]),
                ("user", self.prompts["qa_user_prompt"])
            ]
        )
        self.rag_chain = self.prompt | self.llm | StrOutputParser()

        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts["re_write_system"]),
                ("human", self.prompts["re_write_human"]),
            ]
        )
        self.question_rewriter = re_write_prompt | self.llm | StrOutputParser()

        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts["grade_system"]),
                ("human", self.prompts["grade_human"]),
            ]
        )
        self.retrieval_grader = grade_prompt | self.llm.with_structured_output(GradeDocuments)

        hallucination_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts["hallucination_system"]),
                ("human", self.prompts["hallucination_human"]),
            ]
        )
        self.hallucination_grader = hallucination_prompt | self.llm.with_structured_output(GradeHallucinations)

        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts["answer_system"]),
                ("human", self.prompts["answer_human"]),
            ]
        )
        self.answer_grader = answer_prompt | self.llm.with_structured_output(GradeAnswer)

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

# Usage
api_key = "<addd your api key>"
base_url = "<add your endpoint>"
model = "meta/llama-3.1-70b-instruct"
prompts_file = "prompt.json"
automation = Nodeoutputs(api_key, base_url, model, prompts_file)
