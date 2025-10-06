from nemo_microservices.data_designer.essentials import Score


# General Scores ##
RelevanceScore = Score(
    name="Relevance",
    description="Adherence to INSTRUCTIONS and CONTEXT",
    options={
        "4": "Perfectly meets all specified requirements.",
        "3": "Meets most requirements with minor deviations.",
        "2": "Moderate deviation from the instructions.",
        "1": "Significant deviations from the instructions.",
        "0": "Does not adhere to the instructions.",
    },
)

# Python Scores ##
PythonicScore = Score(
    name="Pythonic",
    description="Pythonic Code and Best Practices (Does the code follow Python conventions and best practices?)",
    options={
        "4": "The code exemplifies Pythonic principles, making excellent use of Python-specific constructs, standard library modules and programming idioms; follows all relevant PEPs.",
        "3": "The code closely follows Python conventions and adheres to many best practices; good use of Python-specific constructs, standard library modules and programming idioms.",
        "2": "The code generally follows Python conventions but has room for better alignment with Pythonic practices.",
        "1": "The code loosely follows Python conventions, with several deviations from best practices.",
        "0": "The code does not follow Python conventions or best practices, using non-Pythonic approaches.",
    },
)

PythonReadabilityScore = Score(
    name="Readability",
    description="Readability and Maintainability (Is the Python code easy to understand and maintain?)",
    options={
        "4": "The code is excellently formatted, follows PEP 8 guidelines, is elegantly concise and clear, uses meaningful variable names, ensuring high readability and ease of maintenance; organizes complex logic well. Docstrings are given in a Google Docstring format.",
        "3": "The code is well-formatted in the sense of code-as-documentation, making it relatively easy to understand and maintain; uses descriptive names and organizes logic clearly.",
        "2": "The code is somewhat readable with basic formatting and some comments, but improvements are needed; needs better use of descriptive names and organization.",
        "1": "The code has minimal formatting, making it hard to understand; lacks meaningful names and organization.",
        "0": "The code is unreadable, with no attempt at formatting or description.",
    },
)

PythonEfficiencyScore = Score(
    name="Efficiency",
    description="Efficiency and Performance (Is the code optimized for performance?)",
    options={
        "4": "The solution is highly efficient, using appropriate data structures and algorithms; avoids unnecessary computations and optimizes for both time and space complexity.",
        "3": "The solution is efficient, with good use of Python's built-in functions and libraries; minor areas for optimization.",
        "2": "The solution is moderately efficient, but misses some opportunities for optimization; uses some inefficient patterns.",
        "1": "The solution shows poor efficiency, with notable performance issues; lacks effective optimization techniques.",
        "0": "The solution is highly inefficient; overlooks fundamental optimization practices, resulting in significant performance issues.",
    },
)

# SQL Scores ##
SQLReadabilityScore = Score(
    name="Readability",
    description="Readability and Maintainability (Is the SQL code easy to understand and maintain?)",
    options={
        "4": "The code is excellently formatted and thoroughly commented, uses meaningful aliases/variable names, ensuring high readability and ease of maintenance; organizes complex queries well.",
        "3": "The code is well-formatted and commented, making it relatively easy to understand and maintain; uses aliases and names with some organization of complex queries.",
        "2": "The code is somewhat readable with basic formatting and some comments, but improvements are needed; needs better use of aliases/names and organization.",
        "1": "The code has minimal formatting and few comments, making it hard to understand; lacks meaningful names and organization.",
        "0": "The code is unreadable, with no attempt at formatting or commenting.",
    },
)


SQLScalabilityScore = Score(
    name="Scalability",
    description="Scalability (Does the solution scale well with larger datasets or more complex queries?)",
    options={
        "4": "The solution is highly scalable, effortlessly handling large datasets and complex queries without performance degradation; avoids inefficient patterns like Cartesian joins.",
        "3": "The solution scales well, maintaining performance with increased data volumes and complexity; minor areas for optimization.",
        "2": "The solution is moderately scalable, handling larger datasets with some performance issues; misses some opportunities for using scalability practices.",
        "1": "The solution shows poor scalability, with notable performance degradation under increased load; lacks effective scalability techniques.",
        "0": "The solution does not scale; overlooks fundamental scalability practices, resulting in significant issues.",
    },
)


SQLStandardsScore = Score(
    name="Standards",
    description="Compliance with Standards (Does the SQL query follow SQL standards and best practices?)",
    options={
        "4": "The query strictly adheres to SQL standards and best practices, showcasing exemplary coding standards.",
        "3": "The query closely follows SQL standards and adheres to many best practices.",
        "2": "The query generally follows SQL standards but has room for better alignment with best practices.",
        "1": "The query loosely follows SQL standards, with several deviations from best practices.",
        "0": "The query does not follow SQL standards or best practices, using deprecated or non-standard syntax.",
    },
)

PYTHON_SCORES = [
    RelevanceScore,
    PythonicScore,
    PythonReadabilityScore,
    PythonEfficiencyScore,
]
SQL_SCORES = [
    RelevanceScore,
    SQLReadabilityScore,
    SQLScalabilityScore,
    SQLStandardsScore,
]


TEXT_TO_SQL_LLM_JUDGE_PROMPT_TEMPLATE = """\
You are a SQL data expert, bringing together expertise from across data analysis, data science and data engineering.\
You think about potential flaws and errors in the code. You are a tough critic, but a fair one.

Take a deep breath and use the data quality Score below to grade the quality of **Generated SQL** based on INSTRUCTIONS and CONTEXT.

#### INSTRUCTIONS
Generated SQL should be a valid response to the Natural Language Prompt and Database Context below

Natural Language Prompt:
{{ sql_prompt }}

Database Context:
{{ sql_context }}

Generated SQL:
```sql
{{ sql }}
```
"""

# Use string formatting to replace the Score in the original template
TEXT_TO_PYTHON_LLM_JUDGE_PROMPT_TEMPLATE = """\
You are an expert in Python programming, with specialized knowledge in software engineering, data science, and algorithmic problem-solving. \
You think about potential flaws and errors in the code. You are a tough critic, but a fair one.

Take a deep breath and use the Python Code Quality Score below to score the **Generated Python Code** based on the INSTRUCTIONS.

#### INSTRUCTIONS
The Generated Python Code should be a valid response to the Natural Language Prompt below

Natural Language Prompt:
{{ instruction }}

Generated Python Code
```python
{{ code_implementation }}
```
"""