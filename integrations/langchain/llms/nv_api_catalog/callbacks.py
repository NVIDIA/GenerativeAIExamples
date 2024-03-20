"""Callback Handler that prints to std out."""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Generator, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.tracers.context import register_configure_hook

logger = logging.getLogger(__name__)

## This module contains output parsers for OpenAI tools. Set here for version control

"""
### **Usage/Cost Tracking**

For tracking model usage and , you can use the `get_usage_callback` context manager to track token information similar to `get_openai_callback`. Additionally, you can specify custom price mappings as necessary (`price_map` argument), or provide a custom callback manager for advanced use-cases (`callback` argument).

**NOTE:** This feature is currently not supported in streaming modes, but works fine for non-streaming `invoke/ainvoke` queries.

```
from integrations.langchain.llms.nv_api_catalog import ChatNVIDIA, NVIDIAEmbeddings
from integrations.langchain.llms.nv_api_catalog.callbacks import get_usage_callback

## Assume a price map per 1K tokens for a particular deployment plan
price_map = {
    "mixtral_8x7b": 0.00060,
    "gemma_7b": 0.0002,
    "nvolveqa_40k": 0.000016,
}

llm_large = ChatNVIDIA(model="mixtral_8x7b", temperature=0.1)
llm_small = ChatNVIDIA(model="gemma_2b", temperature=0.1)
embedding = NVIDIAEmbeddings(model="nvolveqa_40k")
models = [llm_large, llm_small, embedding]

with get_usage_callback(price_map=price_map) as cb:
    ## Reset either at beginning or end. Statistics will run until cleared
    cb.reset()

    llm_large.invoke("Tell me a joke")
    print(cb, end="\n\n")
    # llm_large.invoke("Tell me a short joke")
    # print(cb, end="\n\n")
    # ## Tracking through streaming coming soon
    # [_ for _ in llm_small.stream("Tell me a joke")]
    # print(cb, end="\n[Should not change yet]\n\n")
    ## Tracking for streaming supported
    embedding.embed_query("What a nice day :D")
    print(cb, end="\n\n")
    # ## Sanity check. Should still be tracked fine
    # llm_small.invoke("Tell me a long joke")
    # print(cb, end="\n\n")

## Out of scope. Will not be tracked
llm_small.invoke("Tell me a short joke")
print(cb, end="\n[Should not change ever]\n\n")
cb.model_usage
```
"""


DEFAULT_MODEL_COST_PER_1K_TOKENS: Dict[str, float] = {}


def standardize_model_name(
    model_name: str,
    price_map: dict = {},
    is_completion: bool = False,
) -> str:
    """
    Standardize the model name to a format that can be used in the OpenAI API.

    Args:
        model_name: Model name to standardize.
        is_completion: Whether the model is used for completion or not.
            Defaults to False.

    Returns:
        Standardized model name.

    """
    model_name = model_name.lower()
    if ".ft-" in model_name:
        model_name = model_name.split(".ft-")[0] + "-azure-finetuned"
    if ":ft-" in model_name:
        model_name = model_name.split(":")[0] + "-finetuned-legacy"
    if "ft:" in model_name:
        model_name = model_name.split(":")[1] + "-finetuned"
    if model_name.startswith("playground_"):
        model_name = model_name.replace("playground_", "")
    if (
        is_completion
        and model_name + "-completion" in price_map
        and (
            model_name.startswith("gpt-4")
            or model_name.startswith("gpt-3.5")
            or model_name.startswith("gpt-35")
            or ("finetuned" in model_name and "legacy" not in model_name)
        )
    ):
        return model_name + "-completion"
    else:
        return model_name


def get_token_cost_for_model(
    model_name: str, num_tokens: int, price_map: dict, is_completion: bool = False
) -> float:
    """
    Get the cost in USD for a given model and number of tokens.

    Args:
        model_name: Name of the model
        num_tokens: Number of tokens.
        price_map: Map of model names to cost per 1000 tokens.
            Defaults to AI Foundation Endpoint pricing per https://www.together.ai/pricing.
        is_completion: Whether the model is used for completion or not.
            Defaults to False.

    Returns:
        Cost in USD.
    """
    model_name = standardize_model_name(
        model_name,
        price_map,
        is_completion=is_completion,
    )
    if model_name not in price_map:
        raise ValueError(
            f"Unknown model: {model_name}. Please provide a valid model name."
            "Known models are: " + ", ".join(price_map.keys())
        )
    return price_map[model_name] * (num_tokens / 1000)


class UsageCallbackHandler(BaseCallbackHandler):
    """Callback Handler that tracks OpenAI info."""

    ## Per-model statistics
    _model_usage: defaultdict = defaultdict(
        lambda: {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "successful_requests": 0,
            "total_cost": 0.0,
        }
    )

    llm_output: dict = {}
    price_map: dict = {k: v for k, v in DEFAULT_MODEL_COST_PER_1K_TOKENS.items()}

    ## Aggregate statistics, compatible with OpenAICallbackHandler
    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self._model_usage["total"]["total_tokens"]

    @property
    def prompt_tokens(self) -> int:
        """Prompt tokens used."""
        return self._model_usage["total"]["prompt_tokens"]

    @property
    def completion_tokens(self) -> int:
        """Completion tokens used."""
        return self._model_usage["total"]["completion_tokens"]

    @property
    def successful_requests(self) -> int:
        """Total successful requests."""
        return self._model_usage["total"]["successful_requests"]

    @property
    def total_cost(self) -> float:
        """Total cost in USD."""
        return self._model_usage["total"]["total_cost"]

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.total_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"Successful Requests: {self.successful_requests}\n"
            f"Total Cost (USD): ${self.total_cost:.8g}"
        )

    @property
    def model_usage(self) -> dict:
        """Whether to call verbose callbacks even if verbose is False."""
        return dict(self._model_usage)

    def reset(self) -> None:
        """Reset the model usage."""
        with self._lock:
            self._model_usage.clear()

    @property
    def always_verbose(self) -> bool:
        """Whether to call verbose callbacks even if verbose is False."""
        return True

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        if not response.llm_output:
            response.llm_output = {}
        if not self.llm_output:
            self.llm_output = {}

        response.llm_output = {**self.llm_output, **response.llm_output}
        self.llm_output = {}

        if not response.llm_output:
            return None

        # compute tokens and cost for this request
        token_usage = response.llm_output.get(
            "token_usage", response.llm_output.get("usage", {})
        )
        completion_tokens = token_usage.get("completion_tokens", 0)
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        model_name = response.llm_output.get("model_name", "")
        if model_name in self.price_map:
            completion_cost = get_token_cost_for_model(
                model_name, completion_tokens, self.price_map, is_completion=True
            )
            prompt_cost = get_token_cost_for_model(
                model_name, prompt_tokens, self.price_map
            )
        else:
            completion_cost = 0
            prompt_cost = 0

        # update shared state behind lock
        with self._lock:
            for base in (self._model_usage["total"], self._model_usage[model_name]):
                base["total_tokens"] += token_usage.get("total_tokens", 0)
                base["prompt_tokens"] += prompt_tokens
                base["completion_tokens"] += completion_tokens
                base["total_cost"] += prompt_cost + completion_cost
                base["successful_requests"] += 1
                for key in base.keys():
                    base[key] = round(base[key], 10)

    def __copy__(self) -> "UsageCallbackHandler":
        """Return a copy of the callback handler."""
        return self

    def __deepcopy__(self, memo: Any) -> "UsageCallbackHandler":
        """Return a deep copy of the callback handler."""
        return self


## get_usage_callack variable construction, registration, management

usage_callback_var: ContextVar[Optional[UsageCallbackHandler]] = ContextVar(
    "usage_callback", default=None
)

register_configure_hook(usage_callback_var, True)


@contextmanager
def get_usage_callback(
    price_map: dict = {},
    callback: Optional[UsageCallbackHandler] = None,
) -> Generator[UsageCallbackHandler, None, None]:
    """Get the OpenAI callback handler in a context manager.
    which conveniently exposes token and cost information.

    Returns:
        OpenAICallbackHandler: The OpenAI callback handler.

    Example:
        >>> with get_openai_callback() as cb:
        ...     # Use the OpenAI callback handler
    """
    if not callback:
        callback = UsageCallbackHandler()
    if hasattr(callback, "price_map"):
        if hasattr(callback, "_lock"):
            with callback._lock:
                callback.price_map.update(price_map)
        else:
            callback.price_map.update(price_map)
    usage_callback_var.set(callback)
    yield callback
    usage_callback_var.set(None)
