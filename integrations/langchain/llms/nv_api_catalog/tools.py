"""OpenAI chat wrapper."""

from __future__ import annotations

import logging
from operator import itemgetter
from typing import (
    Any,
    Callable,
    Dict,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers.base import OutputParserLike
from langchain_core.output_parsers.openai_tools import (
    JsonOutputKeyToolsParser,
    PydanticToolsParser,
)
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import Runnable, RunnableMap, RunnablePassthrough
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool

logger = logging.getLogger(__name__)

_BM = TypeVar("_BM", bound=BaseModel)


## Directly Inspired by OpenAI/MistralAI's server-side support.
## Moved here for versioning/additional integration options.


"""
## Agentic Behavior

```
%pip install --upgrade --quiet langchain numexpr langchainhub
```

### Example Usage Within Conversation Chains

Like any other integration, ChatNVIDIA is fine to support chat utilities like conversation buffers by default. Below, we show the [LangChain ConversationBufferMemory](https://python.langchain.com/docs/modules/memory/types/buffer) example applied to the `mixtral_8x7b` model.

```
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

chat = ChatNVIDIA(model="mixtral_8x7b", temperature=0.1, max_tokens=100, top_p=1.0)

conversation = ConversationChain(llm=chat, memory=ConversationBufferMemory())

messages = [
    "Hi there!",
    "I'm doing well! Just having a conversation with an AI.",
    "Tell me about yourself.",
]

for message in messages:
    conversation.invoke("Hi there!")["response"]
```

### Simple Usage With Tooled ReACT Agent

You can also use some of the more powerful LLM models for agentic behavior as described in [HuggingFace's Open-source LLMs as LangChain Agents](https://huggingface.co/blog/open-source-llms-as-agents) blog.

```
from langchain import hub
from langchain.agents import AgentExecutor, load_tools
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import (
    ReActJsonSingleInputOutputParser,
)
from langchain.tools.render import render_text_description

# setup tools
llm = ChatNVIDIA(model="mixtral_8x7b", temperature=0.1)
tools = load_tools(["wikipedia"], llm=llm)

# setup ReAct style prompt
prompt = hub.pull("hwchase17/react-json")
prompt = prompt.partial(
    tools=render_text_description(tools),
    tool_names=", ".join([t.name for t in tools]),
)

## Add some light prompt engineering/llm guiding enforcement
prompt[1].prompt.template += "\nThought: "
chat_model_with_stop = llm.bind(stop=["\nObservation"])

history = []

def add_to_history(x, history, i=0):
  history += [[i, x]]
  return x

# define the agent
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
    }
    | prompt
    # | partial(add_to_history, history=history, i=1)
    | chat_model_with_stop
    # | partial(add_to_history, history=history, i=2)
    | ReActJsonSingleInputOutputParser()
    # | partial(add_to_history, history=history, i=3)
)

# instantiate AgentExecutor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

agent_executor.invoke(
    {
        "input": "Are there any new LLM news from NVIDIA to be aware of in 2024?'"
    }
)
```

If an endpoint supports server-side function/tool calling (AKA the model API itself accepts a tooling message), then you can pull in the experimental `ServerToolsMixin` class as follows:

```
from integrations.langchain.llms.nv_api_catalog import ChatNVIDIA, ServerToolsMixin

class TooledChatNVIDIA(ServerToolsMixin, ChatNVIDIA):
    pass

try:
    tools = load_tools(["wikipedia", "llm-math"], llm=llm)
    llm = TooledChatNVIDIA(model="mixtral_8x7b")
    tooled_llm = llm.bind_tools(tools)
    tooled_llm.invoke("Hello world!!")
except Exception as e:
    print(e)

llm.client.last_inputs["json"]
```

This feature is intended for experimental purposes to help users support and develop tool-calling interfaces. It's also a simple example of how to support and experiment with custom methods via Mixin incorporation.
"""


class ServerToolsMixin(Runnable):
    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]],
        tool_arg: str = "tools",
        conversion_fn: Callable = convert_to_openai_tool,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tool-like objects to this chat model.

        Assumes model is compatible with OpenAI tool-calling API.

        Args:
            tools: A list of tool definitions to bind to this chat model.
                Can be  a dictionary, pydantic model, callable, or BaseTool. Pydantic
                models, callables, and BaseTools will be automatically converted to
                their schema dictionary representation.
            **kwargs: Any additional parameters to pass to the
                :class:`~langchain.runnable.Runnable` constructor.

        EXPERIMENTAL: This method is intended for future support. Invoked in a class:
        ```
        class TooledChatNVIDIA(ChatNVIDIA, ToolsMixin):
            pass

        llm = TooledChatNVIDIA(model="mixtral_8x7b")
        tooled_llm = llm.bind_tools(tools)
        tooled_llm.invoke("Hello world!!")
        ```

        ```
        from integrations.langchain.llms.nv_api_catalog import ChatNVIDIA, ServerToolsMixin
        from langchain_core.pydantic_v1 import BaseModel, Field

        # Note that the docstrings here are crucial, as they will be passed along
        # to the model along with the class name.
        class Multiply(BaseModel):
            "Multiply two integers together."
            a: int = Field(..., description="First integer")
            b: int = Field(..., description="Second integer")

        class TooledChatNVIDIA(ServerToolsMixin, ChatNVIDIA):
            pass

        llm = TooledChatNVIDIA().mode("openai", model="gpt-3.5-turbo-0125")
        llm.bind_tools([Multiply]).invoke("Multiply for me please?")
        llm.client.last_response.json()
        ```

        See langchain-mistralal/openai's implementation for more documentation.
        """
        formatted_tools = [conversion_fn(tool) for tool in tools]
        tool_kw = {tool_arg: formatted_tools}
        return super().bind(**tool_kw, **kwargs)

    def with_structured_output(
        self,
        schema: Union[Dict, Type[BaseModel]],
        *,
        include_raw: bool = False,
        tool_arg: str = "tools",
        conversion_fn: Callable = convert_to_openai_tool,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, Union[Dict, BaseModel]]:
        """Model wrapper that returns outputs formatted to match the given schema.

        Args:
            schema: The output schema as a dict or a Pydantic class. If a Pydantic class
                then the model output will be an object of that class. If a dict then
                the model output will be a dict. With a Pydantic class the returned
                attributes will be validated, whereas with a dict they will not be. If
                `method` is "function_calling" and `schema` is a dict, then the dict
                must match the OpenAI function-calling spec.
            include_raw: If False then only the parsed structured output is returned. If
                an error occurs during model output parsing it will be raised. If True
                then both the raw model response (a BaseMessage) and the parsed model
                response will be returned. If an error occurs during output parsing it
                will be caught and returned as well. The final output is always a dict
                with keys "raw", "parsed", and "parsing_error".

        Returns:
            A Runnable that takes any ChatModel input and returns as output:

                If include_raw is True then a dict with keys:
                    raw: BaseMessage
                    parsed: Pydantic BaseModel or Dictionary
                    parsing_error: Optional[BaseException]

                If include_raw is False then just BaseModel/Dictionary is returned
                (depending on schema type).

        EXPERIMENTAL: This method is intended for future support. Invoked in a class:
        ```
        class TooledChatNVIDIA(ChatNVIDIA, ToolsMixin):
            pass
        ```

        See langchain-mistralal/openai's implementation for more documentation.
        """
        if kwargs:
            raise ValueError(f"Received unsupported arguments {kwargs}")
        is_pydantic_schema = isinstance(schema, type) and issubclass(schema, BaseModel)
        llm = self.bind_tools([schema], tool_arg=tool_arg, conversion_fn=conversion_fn)
        if is_pydantic_schema and isinstance(schema, BaseModel):
            schema_cls: Type[BaseModel] = schema
            output_parser: OutputParserLike = PydanticToolsParser(
                tools=[schema_cls], first_tool_only=True
            )
        else:
            key_name = conversion_fn(schema)["function"]["name"]
            output_parser = JsonOutputKeyToolsParser(
                key_name=key_name, first_tool_only=True
            )

        if include_raw:
            parser_assign = RunnablePassthrough.assign(
                parsed=itemgetter("raw") | output_parser, parsing_error=lambda _: None
            )
            parser_none = RunnablePassthrough.assign(parsed=lambda _: None)
            parser_with_fallback = parser_assign.with_fallbacks(
                [parser_none], exception_key="parsing_error"
            )
            return RunnableMap(raw=llm) | parser_with_fallback
        else:
            return llm | output_parser
