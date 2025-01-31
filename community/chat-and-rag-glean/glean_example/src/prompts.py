from langchain.prompts import PromptTemplate

PROMPT_GLEAN_QUERY_TEMPLATE = """ 

You are part of an agent graph. Your job is to take the user input message and construct a simple and optimized natural language query that will be passed to an API. The API expects a natural language query and returns documents that might answer that query. The documents are sourced from an internal knowledge base at a company.

Examples

User Query: how many days off do I get this year?
Suggested API Query: holiday benefit page

User Query: tell me about the company mission
Suggested API Query: company mission statement

Please reply with a Suggested API Query for the following User Query. Reply with only the suggested query, nothing else.

User Query: {query}
Suggested API Query: 

"""

PROMPT_GLEAN_QUERY = PromptTemplate.from_template(PROMPT_GLEAN_QUERY_TEMPLATE)

PROMPT_ANSWER_TEMPLATE = """

You are the final part of an agent graph. Your job is to answer the user's question based on the information below. Include a url citation in your answer.

Message History: {messages}

Glean Search: {glean_query}

All Supporting Documents from Glean: 

{glean_search_result_documents}

Content from the most relevant document that you should prioritize: 

{answer_candidate}

Answer: 

Citation Url: 

"""

PROMPT_ANSWER = PromptTemplate.from_template(PROMPT_ANSWER_TEMPLATE)
