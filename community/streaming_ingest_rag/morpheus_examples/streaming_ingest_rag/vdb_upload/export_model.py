# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import inspect
import logging
import os
import typing

import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from transformers.models.auto.modeling_auto import AutoModel
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.bert.modeling_bert import BertModel
from tritonclient.grpc.model_config_pb2 import DataType
from tritonclient.grpc.model_config_pb2 import ModelConfig
from tritonclient.grpc.model_config_pb2 import ModelInput
from tritonclient.grpc.model_config_pb2 import ModelOptimizationPolicy
from tritonclient.grpc.model_config_pb2 import ModelOutput
from tritonclientutils import np_to_triton_dtype

try:
    import onnx
except ImportError as exc:
    raise RuntimeError("Please install onnx to use this feature. Run `mamba install -c conda-forge onnx`") from exc

logger = logging.getLogger(__name__)


class CustomTokenizer(torch.nn.Module):
    # pylint: disable=abstract-method
    def __init__(self, model_name: str):
        super().__init__()

        self.inner_model = AutoModel.from_pretrained(model_name)

        if (isinstance(self.inner_model, SentenceTransformer)):
            self._output_dim = self.inner_model.get_sentence_embedding_dimension()
        elif (isinstance(self.inner_model, BertModel)):
            self._output_dim = self.inner_model.config.hidden_size

        sig = inspect.signature(self.inner_model.forward)

        ordered_list_keys = list(sig.parameters.keys())
        if ordered_list_keys[0] == "self":
            ordered_list_keys = ordered_list_keys[1:]

        # Save the idx of the attention mask because exporting prefers arguments over kwargs
        self._attention_mask_idx = ordered_list_keys.index("attention_mask")

        # Wrap the original function so the export can find the original signature
        @functools.wraps(self.inner_model.forward)
        def forward(*args, **kwargs):
            return self._forward(*args, **kwargs)

        self.forward = forward

    @property
    def output_dim(self):
        return self._output_dim

    # Mean Pooling - Take attention mask into account for correct averaging
    def mean_pooling(self, model_output, attention_mask):
        # Adapted from https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
        # First element of model_output contains all token embeddings
        last_hidden_state = model_output["last_hidden_state"]  # [batch_size, seq_length, hidden_size]

        alternate = True

        if (alternate):
            last_hidden = last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
            return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

        # Transpose to make broadcasting possible
        last_hidden_state = torch.transpose(last_hidden_state, 0, 2)  # [hidden_size, seq_length, batch_size]

        input_mask_expanded = torch.transpose(attention_mask.unsqueeze(-1).float(), 0, 2)  # [1, seq_length, batch_size]

        num = torch.sum(last_hidden_state * input_mask_expanded, 1)  # [hidden_size, batch_size]
        denom = torch.clamp(input_mask_expanded.sum(1), min=1e-9)  # [1, batch_size]

        return torch.transpose(num / denom, 0, 1)  # [batch_size, hidden_size]

    def normalize(self, embeddings):

        alternate = False

        if (alternate):
            return F.normalize(embeddings, p=2, dim=1)

        # Use the same trick here to broadcast to avoid using the expand operator which breaks dynamic axes
        denom = torch.transpose(embeddings.norm(2, 1, keepdim=True).clamp_min(1e-12), 0, 1)

        return torch.transpose(torch.transpose(embeddings, 0, 1) / denom, 0, 1)

    def _forward(self, *args, **kwargs):

        if ("attention_mask" in kwargs):
            attention_mask = kwargs["attention_mask"]
        elif (len(args) > self._attention_mask_idx):
            # Lookup from positional
            attention_mask = args[self._attention_mask_idx]
        else:
            raise RuntimeError("Cannot determine attention mask")

        model_outputs = self.inner_model(*args, **kwargs)

        sentence_embeddings = self.mean_pooling(model_outputs, attention_mask)

        sentence_embeddings = self.normalize(sentence_embeddings)

        return sentence_embeddings


def _save_model(model, sample_input: dict, output_model_path: str):

    # Ensure our input is a dictionary, not a batch encoding
    args = (dict(sample_input.items()), )

    inspect.signature(model.forward)

    torch.onnx.export(
        model,
        args,
        output_model_path,
        opset_version=13,
        input_names=['input_ids', 'attention_mask'],
        output_names=['output'],
        dynamic_axes={
            'input_ids': {
                0: 'batch_size',
                1: "seq_length",
            },  # variable length axes
            'attention_mask': {
                0: 'batch_size',
                1: "seq_length",
            },
            'output': {
                0: 'batch_size',
            }
        },
        verbose=False)

    onnx_model = onnx.load(output_model_path)

    onnx.checker.check_model(onnx_model)


def build_triton_model(model_name, model_seq_length, max_batch_size, triton_repo, output_model_name):

    if (output_model_name is None):
        output_model_name = model_name

    device = torch.device("cuda")

    model_name = f'{model_name}'

    model = CustomTokenizer(model_name)
    model.to(device)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    test_texts = [
        "This is text one which is longer",
        "This is text two",
    ]

    sample_input = tokenizer(test_texts,
                             max_length=model_seq_length,
                             padding="max_length",
                             truncation=True,
                             return_token_type_ids=False,
                             return_tensors="pt").to(device)

    test_output = model(**(sample_input.to(device))).detach()

    output_model_dir = os.path.join(triton_repo, output_model_name)

    # Make sure we create the directory if it does not exist
    os.makedirs(output_model_dir, exist_ok=True)

    # Make the config file
    config: typing.Any = typing.cast(typing.Any, ModelConfig())

    config.name = output_model_name
    config.platform = "onnxruntime_onnx"
    config.max_batch_size = max_batch_size

    # pylint: disable=no-member
    for input_name, input_data in sample_input.data.items():

        config.input.append(
            ModelInput(
                name=input_name,
                data_type=DataType.Value(f"TYPE_{np_to_triton_dtype(input_data.cpu().numpy().dtype)}"),
                dims=[input_data.shape[1]],
            ))

    config.output.append(
        ModelOutput(
            name="output",
            data_type=DataType.Value(f"TYPE_{np_to_triton_dtype(test_output.cpu().numpy().dtype)}"),
            dims=[test_output.shape[1]],
        ))

    def _powers_of_2(max_val: int):
        val = 1

        while (val <= max_val):
            yield val
            val *= 2

    config.dynamic_batching.preferred_batch_size.extend(x for x in _powers_of_2(max_batch_size))
    config.dynamic_batching.max_queue_delay_microseconds = 50000

    config.optimization.execution_accelerators.gpu_execution_accelerator.extend([
        ModelOptimizationPolicy.ExecutionAccelerators.Accelerator(name="tensorrt",
                                                                  parameters={
                                                                      "precision_mode": "FP16",
                                                                      "max_workspace_size_bytes": "2147483648",
                                                                  })
    ])

    config_path = os.path.join(output_model_dir, "config.pbtxt")

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(str(config))

    model_version_dir = os.path.join(output_model_dir, "1")

    os.makedirs(model_version_dir, exist_ok=True)

    output_model_path = os.path.join(model_version_dir, "model.onnx")

    _save_model(model, sample_input, output_model_path=output_model_path)

    logger.info("Created Triton Model at %s", output_model_dir)
