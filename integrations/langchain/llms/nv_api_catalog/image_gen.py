"""Embeddings Components Derived from NVEModel/Embeddings"""
import base64
from io import BytesIO
from typing import Any, List, Optional

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import LLM
from langchain_core.pydantic_v1 import Field
from langchain_core.runnables import Runnable, RunnableLambda
from PIL import Image

from integrations.langchain.llms.nv_api_catalog._common import _NVIDIAClient


"""
## Image Generation Models

Due to the similarity of the underlying API, a selection of **Image Generation Models** can be supported using the LLM interface. One example is the [**Stable Diffusion XL**](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-foundation/models/sdxl/api) model, which expects a prompt and some other arguments as input and produces an image (passed back as a b64-encoded string). 

```
from integrations.langchain.llms.nv_api_catalog import ImageGenNVIDIA

ImageGenNVIDIA.get_available_models()  ## Only shows models supported by ImageGenNVIDIA

sdxl = ImageGenNVIDIA(model="sdxl")

out = sdxl.invoke("A picture of a cat, aesthetic")
out[:100] + "..."
```

To see the image, we can either convert it manually or use the built-in conversion utility ``

```
from integrations.langchain.llms.nv_api_catalog.image_gen import ImageParser

# from io import BytesIO
# from PIL import Image
# import base64

# Image.open(BytesIO(base64.decodebytes(bytes(out[10:], "utf-8"))))
ImageParser().invoke(out)  ## Runnable that does it all for you
```

In addition to the prompt, we can do a bit of hyperparameter tweaking and add some negative prompt components that we'd like to avoid. We will also use the `ImageParser` runnable automatically by calling the `.as_pil()` method.

```
sdxl = ImageGenNVIDIA(
    inference_steps = 100,
    negative_prompt = "ugly,bad eyes,low-res,crooked nose, smudged, painted",
)

sdxl.as_pil().invoke("A picture of a big green dog, futuristic cyberpunk")
```

Note that under the hood, `as_pil` returns a merger of the `ImageGenModel` object with the `ImageParser` output parser. As a result, you may have trouble interacting with the aggregation. Note that you can reference the first half of the pipeline via `.first` or similar.

## Example of image generation with OpenAI and DALL-E

```
from integrations.langchain.llms.nv_api_catalog import ImageGenNVIDIA
from getpass import getpass
import os

if not os.environ.get("OPENAI_API_KEY", "").startswith("sk-"):
    os.environ["OPENAI_API_KEY"] = getpass("Enter your OPENAI Key: ")

llm = ImageGenNVIDIA().mode("openai")
llm.available_models
```

```
from integrations.langchain.llms.nv_api_catalog import ImageGenNVIDIA

dalle = ImageGenNVIDIA().mode("openai", model="dall-e-3")

def payload_fn(d):
    if d:
        drop_keys = ["guidance_scale", "seed", "negative_prompt", "sampler"]
        d = {k: v for k, v in d.items() if k not in drop_keys}
    return d

dalle.client.payload_fn = payload_fn

dalle.as_pil().invoke("City skyline, neon green tint, aesthetic futuristic realistic")
print(dalle.client.last_inputs['json'])
dalle.client.last_response.json()
```
"""


def _get_pil_from_response(data: str) -> Image.Image:
    if data.startswith("url: "):
        body = requests.get(data[4:], stream=True).raw
    elif data.startswith("b64_json: "):
        body = BytesIO(base64.decodebytes(bytes(data[10:], "utf-8")))
    else:
        raise ValueError(f"Invalid response format: {str(data)[:100]}")
    return Image.open(body)


def ImageParser() -> RunnableLambda[str, Image.Image]:
    return RunnableLambda(_get_pil_from_response)


class ImageGenNVIDIA(_NVIDIAClient, LLM):
    """NVIDIA's AI Foundation Retriever Question-Answering Asymmetric Model."""

    _default_model: str = "sdxl"
    infer_endpoint: str = Field("{base_url}/images/generations")
    model: str = Field(_default_model, description="Name of the model to invoke")
    negative_prompt: Optional[str] = Field(description="Sampling temperature in [0, 1]")
    sampler: Optional[str] = Field(description="Sampling strategy for process")
    guidance_scale: Optional[float] = Field(description="The scale of guidance")
    seed: Optional[int] = Field(description="The seed for deterministic results")

    @property
    def _llm_type(self) -> str:
        """Return type of NVIDIA AI Foundation Model Interface."""
        return "nvidia-image-gen-model"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the Image Gen Model on the given prompt and input."""
        payload = {
            "prompt": prompt,
            "negative_prompt": kwargs.get("negative_prompt", self.negative_prompt),
            "sampler": kwargs.get("sampler", self.sampler),
            "guidance_scale": kwargs.get("guidance_scale", self.guidance_scale),
            "seed": kwargs.get("seed", self.seed),
        }
        if self.get_binding_model():
            payload["model"] = self.get_binding_model()
        response = self.client.get_req(
            model_name=self.model, payload=payload, endpoint="infer"
        )
        response.raise_for_status()
        out_dict = response.json()
        if "data" in out_dict:
            out_dict = out_dict.get("data")[0]
        if "url" in out_dict:
            output = "url: {}".format(out_dict.get("url"))
        elif "b64_json" in out_dict:
            output = "b64_json: {}".format(out_dict.get("b64_json"))
        else:
            output = str(out_dict)
        return output

    def as_pil(self, **kwargs: Any) -> Runnable:
        """Returns a model that outputs a PIL image by default"""
        return self | ImageParser(**kwargs)
