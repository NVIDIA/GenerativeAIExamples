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
_QUANTIZATIONS = ["int4_awq"]

_LOGGER = logging.getLogger(__name__)

def find_pt_file(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".pt"):
                return os.path.join(root, file)
    return None

def convert(model: Model, opts: ConversionOptions) -> None:
    """Convert a llama model."""
    _LOGGER.debug("Running Llama model conversion.")
    _LOGGER.info(f"Model Format: {model.format.name}")

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
        ]

        if opts.quantization:
            if opts.quantization == "int4_awq" and model.format.name == "PYTORCH":
                ckpt_dir = find_pt_file(model.model_dir)
                raw_args.extend([
                    "--use_weight_only",
                    "--weight_only_precision",
                    "int4_awq",
                    "--per_group",
                    "--quant_ckpt_path",
                    str(ckpt_dir),
                ])
            else:
                raise Exception(
                    "Unsupported quantization or model format, " \
                    + f"supported quantizations: {_QUANTIZATIONS}, " \
                    + "with format: PYTORCH"
                )
        else:
            raw_args.extend([
                _CHECKPOINT_ARGS_FLAGS[model.format.name],
                model.model_dir,
            ])

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
