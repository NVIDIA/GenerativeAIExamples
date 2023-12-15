# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module contains the logic for doing model conversions to TensorRT."""
from dataclasses import dataclass
from typing import Optional

from ..errors import ModelServerException
from ..model import Model, ModelFormats, ModelTypes


@dataclass
class ConversionOptions:
    """Class containing the options used in TRT conversion."""

    max_input_length: int
    max_output_length: int
    pipline_parallelism: int
    tensor_parallelism: int
    vocab_size: Optional[int] = None
    quantization: Optional[str] = ""


def convert(model: Model, opts: ConversionOptions) -> None:
    """
    Convert the provided model to TensorRT.

    Supported types and formats:
    +----------+---------+---------+---------+---------+---------+
    |          | NEMO    | PYTORCH | ONNX    | HFACE   | UNKNOWN |
    +----------+---------+---------+---------+---------+---------+
    | LLAMA    |    ✅   |    ✅    |    ❌   |    ✅   |    ❌   |
    | GPTNEXT  |    ✅   |    ❌    |    ❌   |    ❌   |    ❌   |
    +----------+---------+---------+---------+---------+---------+
    """
    if model.format == ModelFormats.NEMO:
        # pylint: disable-next=import-outside-toplevel  # preventing circular imports
        from . import nemo

        nemo.convert(model, opts)

    elif model.type == ModelTypes.LLAMA:
        # pylint: disable-next=import-outside-toplevel  # preventing circular imports
        from . import llama

        opts.vocab_size = 32000
        llama.convert(model, opts)

    elif model.type == ModelTypes.CODE_LLAMA:
        # pylint: disable-next=import-outside-toplevel  # preventing circular imports
        from . import llama

        opts.vocab_size = 32016
        llama.convert(model, opts)

    else:
        supported_types = [e.name for e in ModelTypes]
        raise ModelServerException(
            f"Unsupported model type. Conversion is supported for the following types: {supported_types}"
        )

    model.write_hash()
