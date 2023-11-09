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

"""This module contains the logic for exporting a Llama model in PyTorch format to TensorRT."""
import logging
import os
import subprocess
import sys
import typing

from ..errors import ModelServerException, UnsupportedFormatException
from ..model import Model
from . import ConversionOptions

_CONVERSION_SCRIPTS = "/opt/conversion_scripts/llama"

_CHECKPOINT_ARGS_FLAGS = {"PYTORCH": "--meta_ckpt_dir", "HUGGINGFACE": "--model_dir"}
_LOGGER = logging.getLogger(__name__)


def convert(model: Model, opts: ConversionOptions) -> None:
    """Convert a llama model."""
    _LOGGER.debug("Running Llama model conversion.")

    # construct builder executable path
    cwd = _CONVERSION_SCRIPTS
    exe = [sys.executable, "build.py"]

    # construct builder env variables
    env = os.environ

    # construct builder arguments
    try:
        raw_args: typing.List[str] = [
            "--max_input_len",
            str(opts.max_input_length),
            "--max_output_len",
            str(opts.max_output_length),
            "--dtype",
            "float16",
            "--use_gpt_attention_plugin",
            "float16",
            "--use_inflight_batching",
            "--paged_kv_cache",
            "--remove_input_padding",
            "--use_gemm_plugin",
            "float16",
            "--output_dir",
            model.engine_dir,
            "--world_size",
            str(model.world_size),
            "--tp_size",
            str(opts.tensor_parallelism),
            "--pp_size",
            str(opts.pipline_parallelism),
            "--vocab_size",
            str(opts.vocab_size),
            _CHECKPOINT_ARGS_FLAGS[model.format.name],
            model.model_dir,
        ]
    except KeyError as err:
        raise UnsupportedFormatException(
            model.format.name, ["PyTorch", "Hugging Face"]
        ) from err

    # start the builder
    _LOGGER.debug(
        "Starting Llama exporter with the command: %s", " ".join(exe + raw_args)
    )
    _LOGGER.debug("Starting Llama exporter with the env vars: %s", repr(env))
    with subprocess.Popen(exe + raw_args, env=env, cwd=cwd) as proc:
        try:
            retcode = proc.wait()
        except KeyboardInterrupt:
            proc.kill()
        except Exception as err:
            raise ModelServerException(
                "Error running TensorRT model conversion."
            ) from err
        else:
            if retcode != 0:
                raise ModelServerException(
                    "TensorRT conversion returned a non-zero exit code."
                )
