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
        transform_count = state.get("transform_count", 0)

        # If we've transformed too many times, force generation
        if transform_count >= 2:
            print("DECISION: MAX TRANSFORMS REACHED, FORCING GENERATION")
            return "generate"

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
        try:
            score_text = automation.answer_grader.invoke({"question": question, "generation": generation})
            if "yes" in score_text.lower():
                print("DECISION: GENERATION ADDRESSES QUESTION")
                return "useful"
            else:
                # Check if we've transformed too many times
                transform_count = state.get("transform_count", 0)
                if transform_count >= 2:
                    print("DECISION: MAX TRANSFORMS REACHED, ACCEPTING GENERATION")
                    return "useful"
                else:
                    print("DECISION: GENERATION DOES NOT ADDRESS QUESTION")
                    return "not useful"
        except:
            # If grading fails, assume generation is useful to avoid infinite loops
            print("DECISION: GRADING FAILED, ACCEPTING GENERATION")
            return "useful"