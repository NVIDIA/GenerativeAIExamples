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

"""This module contains the code for converting any .nemo formatted model to TRT LLM."""
import logging
import os
from glob import glob
from tarfile import TarFile
from typing import IO, cast

import yaml

# pylint: disable-next=import-error
from nemo.export import TensorRTLLM  # type: ignore

from ..errors import ModelServerException
from ..model import Model
from . import ConversionOptions

_LOGGER = logging.getLogger(__name__)


def convert(model: Model, opts: ConversionOptions) -> None:
    """Convert a .nemo formatted model."""
    # find the .nemo model file
    model_files = glob(os.path.join(model.model_dir, "*.nemo"))
    if len(model_files) > 1:
        raise ModelServerException(
            "More than one NeMo checkpoint found in the model directory. "
            + "Please only include one NeMo checkpoint file."
        )

    # verify that the model parallelism matchines the
    config = {}
    with TarFile(model_files[0], "r") as archive:
        try:
            config_file = cast(IO[bytes], archive.extractfile("./model_config.yaml"))
        except KeyError:
            config_file = cast(IO[bytes], archive.extractfile("model_config.yaml"))
        config = yaml.safe_load(config_file)
        config_file.close()

    # run the nemo to trt llm conversion
    trt_llm_exporter = TensorRTLLM(model_dir=model.engine_dir)
    _LOGGER.info(".nemo to TensorRT Conversion started. This will take a few minutes.")
    _LOGGER.info(model.engine_dir)
    trt_llm_exporter.export(
        nemo_checkpoint_path=model_files[0],
        model_type=model.family,
        n_gpus=model.world_size,
        max_input_token=opts.max_input_length,
        max_output_token=opts.max_output_length
    )
