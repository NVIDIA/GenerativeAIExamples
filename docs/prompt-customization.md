<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customize Prompts

Each example uses a `prompt.yaml` file that defines prompts for different contexts.
These prompts guide the RAG model in generating appropriate responses.
You can customize these prompts to fit your specific needs and achieve desired responses from the models.



## Example: Access a Prompt

The [`prompt.yaml`](../src/prompt.yaml) file is loaded as a Python dictionary in the application.
To access this dictionary, use the [`get_prompts()`](../src/utils.py#L150) function provided by the [`utils`](../src/utils.py) module.

For example, if we have the following `prompt.yaml` file:

```yaml
chat_template: |
    You are a helpful, respectful and honest assistant.
    Always answer as helpfully as possible, while being safe.
    Please ensure that your responses are positive in nature.

rag_template: |
    You are a helpful AI assistant named Envie.
    You will reply to questions only based on the context that you are provided.
    If something is out of context, you will refrain from replying and politely decline to respond to the user.
```

Use the following code to access the chat_template:

```python3
from .utils import get_prompts

prompts = get_prompts()

chat_template = prompts.get("chat_template", "")
```



## Example: Add a Pirate Template

Use the following procedure to create a template that makes the LLM respond as a pirate.

1. Add a new template to [`prompt.yaml`](../src/prompt.yaml):

   ```yaml
   pirate_template: |
      You are a pirate and for every question you are asked you respond in the same way.
   ```

2. Update the [`llm_chain`](../src/chains.py#L130) method in [`chains.py`](../src/chains.py) and use `pirate_template` to generate responses.

   ```python3
    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `false`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
        """

        logger.info("Using llm to generate response directly without knowledge base.")
        prompt = prompts.get("pirate_template", "")

        logger.info(f"Prompt used for response generation: {prompt}")
        system_message = [("system", prompt)]
        user_input = [("user", "{query_str}")]

        prompt_template = ChatPromptTemplate.from_messages(system_message + user_input)

        llm = get_llm(**kwargs)

        # Simple langchain chain to generate response based on user's query
        chain = prompt_template | llm | StrOutputParser()
        return chain.stream({"query_str": query})
   ```

3. Restart the service by running the following code.

   ```console
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d --build
   ```
