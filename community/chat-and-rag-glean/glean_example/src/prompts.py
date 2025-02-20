from langchain.prompts import PromptTemplate

PROMPT_GLEAN_QUERY_TEMPLATE = """ 

You are part of an agent graph. Your job is to take the user input message and decide if access to a company knowledge base is needed to answer the question.

Examples

User Query: how many days off do I get this year?
Answer: Yes

User Query: tell me about the company mission
Answer: Yes

User Query: tell me a funny joke
Answer: No

Reply with only Yes or No, nothing else.

User Query: {query}
Answer:

"""

PROMPT_GLEAN_QUERY = PromptTemplate.from_template(PROMPT_GLEAN_QUERY_TEMPLATE)

PROMPT_ANSWER_TEMPLATE = """

You are the final part of an agent graph. Your job is to answer the user's question based on the information below. Include a url citation in your answer.

Message History: {messages}

All Supporting Documents from Glean: 

{glean_search_result_documents}

Content from the most relevant document that you should prioritize: 

{answer_candidate}

Answer: 

Citation Url: 

"""

PROMPT_ANSWER = PromptTemplate.from_template(PROMPT_ANSWER_TEMPLATE)
