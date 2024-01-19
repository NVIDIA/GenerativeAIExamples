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

"""Model-Server converts LLMs to TensorRT engines and hosts them with Triton."""
import argparse
import logging
import os

from .conversion import ConversionOptions, convert
from .errors import ModelServerException
from .model import Model, ModelFormats
from .server import ModelServer

_LOGGER = logging.getLogger(__name__)


def _mk_symlink(source: str, dest: str) -> None:
    """Safely create a symbolic link."""
    if not os.path.exists(dest):
        os.symlink(source, dest)
        _LOGGER.debug("Creating symlink from %s to %s", source, dest)


def _azureml(source_directory: str) -> None:
    """Make accomodations for AzureML."""
    _LOGGER.info("Detected running on AzureML.")
    _LOGGER.debug("AZUREML_MODEL_DIR Variable is %s", source_directory)
    destination_directory = "/model"
    source_directory = os.path.abspath(source_directory)
    _LOGGER.debug("Azure Model Directory is now  %s", source_directory)
    _LOGGER.debug(
        "Azure model directory contents: %s", repr(os.listdir(source_directory))
    )

    # find the direct path to the model weights
    # $AZUREML_MODEL_DIR/model_name
    try:
        source_directory = os.path.join(
            source_directory, os.listdir(source_directory)[0]
        )
        _LOGGER.debug("Azure Model Directory is now  %s", source_directory)
        _LOGGER.debug(
            "Azure model directory contents: %s", repr(os.listdir(source_directory))
        )
    except IndexError:
        # pylint: disable-next=raise-missing-from
        raise ModelServerException("AzureML folder structure is not recognized.")

    # create links for the model files to the /models directory
    for root, dirs, files in os.walk(source_directory):
        root_destination = root.replace(source_directory, destination_directory)
        for fi in files:
            _mk_symlink(os.path.join(root, fi), os.path.join(root_destination, fi))
        for di in dirs:
            dest = os.path.join(root_destination, di)
            os.makedirs(dest, exist_ok=True)
            _LOGGER.debug("Creating directory %s", dest)


def _should_convert(args: argparse.Namespace, model: "Model") -> bool:
    """Determine if the conversion step should run."""
    if args.force_conversion:
        return True

    if args.no_conversion:
        return False

    return model.conversion_is_needed()


def main(args: argparse.Namespace) -> int:
    """Execute the model server."""
    # make accomidations for various ML platforms
    azureml_model_dir = os.environ.get("AZUREML_MODEL_DIR")
    if azureml_model_dir:
        _azureml(azureml_model_dir)

    # load the model directory
    _LOGGER.info("Reading the model directory.")
    model = Model(model_type=args.type, world_size=args.world_size)

    if model._format == ModelFormats.UNKNOWN:
        raise ModelServerException(
            f"""No known model formats detected in the provided MODEL_DIRECTORY.
            Supported formats are Pytorch(.pth or .pt), Huggingface (.bin) and Onnx (.onnx).
            Please check if the absolute path provided with the help of environment variable
            MODEL_DIRECTORY in compose.env file is correct and has been set properly."""
        )

    # calculate the default parallism parameters
    if not args.tensor_parallelism:
        args.tensor_parallelism = max(
            int(model.world_size / args.pipeline_parallelism), 1
        )
    if args.pipeline_parallelism * args.tensor_parallelism != model.world_size:
        raise ModelServerException(
            "Tensor Parallelism * Pipeline Parallelism must be equal to World Size"
        )

    conversion_opts = ConversionOptions(
        max_input_length=args.max_input_length,
        max_output_length=args.max_output_length,
        tensor_parallelism=args.tensor_parallelism,
        pipline_parallelism=args.pipeline_parallelism,
        quantization = args.quantization,
    )

    # print discovered model parameters
    _LOGGER.info("Model file format: %s", model.format.name)
    _LOGGER.info("World Size: %d", model.world_size)
    _LOGGER.info("Max input length: %s", args.max_input_length)
    _LOGGER.info("Max output length: %s", args.max_output_length)
    _LOGGER.info("Compute Capability: %s", model.compute_cap)
    _LOGGER.info("Quantization: %s", conversion_opts.quantization)

    # convert model
    if _should_convert(args, model):
        _LOGGER.info("Starting TensorRT Conversion.")
        convert(model, conversion_opts)
    else:
        _LOGGER.info("TensorRT Conversion not required. Skipping.")

    # host model
    if not args.no_hosting:
        _LOGGER.info("Starting Triton Inference Server.")
        inference_server = ModelServer(model, args.http)
        return inference_server.run()

    return 0
