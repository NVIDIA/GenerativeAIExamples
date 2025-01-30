from utils import automation
class Edge:
    def decide_to_generate(state):
        """
        Determines whether to generate an answer, or re-generate a question.

        Returns:
            str: Binary decision for next node to call
        """

        print("ASSESS GRADED DOCUMENTS")
        state["question"]
        filtered_documents = state["documents"]

        if not filtered_documents:
            print(
                "DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY"
            )
            return "transform_query"
        print("---DECISION: GENERATE---")
        return "generate"
        
    def grade_generation_vs_documents_and_question(state):
        """
        Determines whether the generation is grounded in the document and answers question.

        Returns:
            str: Decision for next node to call
        """

        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]

        print("GRADE GENERATED vs QUESTION")
        score = automation.answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("DECISION: GENERATION ADDRESSES QUESTION")
            return "useful"
        print("DECISION: GENERATION DOES NOT ADDRESS QUESTION")
        return "not useful"