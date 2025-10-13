<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customizing Prompts

<!-- TOC -->

* [About the Prompt File](#about-the-prompt-file)
* [Accessing Prompts](#accessing-prompts)
* [Example: Adding a Mathematical Operation Prompt](#example-adding-a-mathematical-operation-prompt)

<!-- /TOC -->

## About the Prompt File

Each example uses a `prompt.yaml` file that defines prompts for different contexts.
These prompts guide the RAG model in generating appropriate responses.
You can tailor these prompts to fit your specific needs and achieve desired responses from the models.

## Accessing Prompts
The prompts are loaded as a Python dictionary within the application.
To access this dictionary, you can use the `get_prompts()` function provided by the `utils` module.
This function retrieves the complete dictionary of prompts.

Consider we have following `prompt.yaml` file:

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

You can access the chat_template using following the code in your chain server:

```python3
from RAG.src.chain_server.utils import get_prompts

prompts = get_prompts()

chat_template = prompts.get("chat_template", "")
```

After you update the prompt, you can restart the service by performing the following steps:

1. Move to example directory:

   ```console
   cd RAG/examples/basic_rag/llamaindex
   ```

2. Start the chain server microservice:

   ```console
   docker compose down
   docker compose up -d --build
   ```

3. Go to `http://<ip>:<port>` to interact with the example.


## Example: Adding a Pirate Prompt

Let's create a prompt that will make llm respond in a way that resonse is coming from a pirate.

1. Add the prompt to `prompt.yaml`:
 
   ```yaml
   pirate_prompt: |
      You are a pirate and for every question you are asked you respond in the same way.
   ```

2. Update the `llm_chain` method in `chains.py` and use `pirate_prompt` to generate responses:

   ```python3
    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `False`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
        """

        logger.info("Using llm to generate response directly without knowledge base.")
        prompt = prompts.get("pirate_prompt", "")

        logger.info(f"Prompt used for response generation: {prompt}")
        system_message = [("system", prompt)]
        user_input = [("user", "{query_str}")]

        prompt_template = ChatPromptTemplate.from_messages(system_message + user_input)

        llm = get_llm(**kwargs)

        # Simple langchain chain to generate response based on user's query
        chain = prompt_template | llm | StrOutputParser()
        return chain.stream({"query_str": query}, config={"callbacks": [self.cb_handler]},)   
   ```

3. Change directory to an example:

   ```console
   cd RAG/examples/basic_rag/llamaindex
   ```

4. Start the chain server microservice:

   ```console
   docker compose down
   docker compose up -d --build
   ```

5. Go to `http://<ip>:<port>` to interact with example.
