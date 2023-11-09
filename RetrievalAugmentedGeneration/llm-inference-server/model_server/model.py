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

"""This module contains the model class that represents the model mounted to the container."""
import glob
import hashlib
import logging
import os
import pathlib
import subprocess
import typing
from enum import Enum, auto, unique

from .errors import ModelServerException

DEFAULT_MODEL_DIR = "/model"
HASH_COMMAND = "sha1sum"
_LOGGER = logging.getLogger(__name__)


def _fast_hash_dir(dir_path: str) -> str:
    """
    Read the files in a directory and quickly create a hash.

    This hash IS NOT cryptographically secure, but it is designed to be computed as quickly as reasonably possible.
    This function will only hash top level files and will not traverse directories.
    """
    # create a threaded pool of workers to calculate individual hases
    workers = []
    for obj in os.listdir(dir_path):
        obj_path = os.path.join(dir_path, obj)
        if not os.path.isfile(obj_path):
            continue

        workers += [
            # pylint: disable-next=consider-using-with
            subprocess.Popen(
                [HASH_COMMAND, obj_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        ]

    # wait for workers to complete
    all_shas = b""
    for proc in workers:
        stdout, _ = proc.communicate()
        all_shas += stdout.split(b" ", maxsplit=1)[0]

    hasher = hashlib.sha1(usedforsecurity=False)
    hasher.update(all_shas)
    return hasher.hexdigest()


@unique
class ModelFormats(Enum):
    """A Enumerator containing all of the supported model types."""

    UNKNOWN = auto()
    ONNX = auto()
    PYTORCH = auto()
    HUGGINGFACE = auto()
    NEMO = auto()


@unique
class ModelTypes(Enum):
    """A enumerator of the supported model types."""

    LLAMA = auto()
    CODE_LLAMA = auto()
    GPTNEXT = auto()

    @property
    def family(self) -> str:
        """Return the family grouping of the model."""
        return ["llama", "llama", "gptnext"][self.value - 1]


class Model:
    """A representation of the mounted model."""

    def __init__(
        self,
        model_type: str,
        model_dir: typing.Optional[str] = None,
        world_size: typing.Optional[int] = None,
    ):
        """Initialize the model class."""
        try:
            self._type = ModelTypes[model_type.upper().replace("-", "_")]
        except KeyError as err:
            raise ModelServerException(f"Unrecognized model type {type}") from err

        self._model_dir = model_dir or DEFAULT_MODEL_DIR
        self._gpu_info = self._init_gpu_info(world_size=world_size)
        self._hash: typing.Optional[str] = None
        self._engine_dir = self._init_engine_dir()
        self._format = self._init_model_format()

    @classmethod
    def _init_gpu_info(
        cls,
        world_size: typing.Optional[int] = None,
    ) -> typing.Dict[str, typing.Union[str, int]]:
        """
        Get the product name and architecture for the first GPU in the system.

        Returns
        -------
        Tuple: A tuple of the product name and architecture.
        """
        query_cmd = ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"]
        gpu_info_raw = subprocess.check_output(query_cmd)
        compute_caps = [cap.decode() for cap in gpu_info_raw.strip().split(b"\n")]
        # FUTURE: convert this to use nvml instead

        # do basic error checking
        if len(compute_caps) == 0:
            raise ModelServerException("No GPUs attached to the container.")
        if len(set(compute_caps)) > 1:
            raise ModelServerException(
                "Attached GPUs are dissimilar. All GPUs must be of the same type."
            )
        if not world_size:
            world_size = len(compute_caps)

        return {"compute_cap": compute_caps[0], "world_size": world_size}

    def _init_engine_dir(self) -> str:
        """Create and return the path to the TensorRT cache directory for this model."""
        cache_dir = f"trt-w{self.world_size}-cc{self.compute_cap}"
        cache_path = os.path.join(self.model_dir, cache_dir)
        pathlib.Path(cache_path).mkdir(parents=True, exist_ok=True)
        return cache_path

    def _init_model_format(self) -> ModelFormats:
        """Determine the format of model that has been mounted."""
        # look for nemo checkpoints
        nemo_count = self._file_ext_count("nemo")
        if nemo_count == 1:
            return ModelFormats.NEMO
        if nemo_count > 1:
            raise ModelServerException(
                f"Only one nemo checkpoint file may be in the model directory. Found {nemo_count}",
            )

        # look for pytorch saved models
        pytorch_count = self._file_ext_count("pth") + self._file_ext_count("pt")
        if pytorch_count:
            return ModelFormats.PYTORCH

        # look for huggingface saved models
        hf_count = self._file_ext_count("bin")
        if hf_count:
            return ModelFormats.HUGGINGFACE

        # look for onnx models
        onnx_count = self._file_ext_count("onnx")
        if onnx_count:
            return ModelFormats.ONNX

        return ModelFormats.UNKNOWN

    def _file_ext_count(self, extension: str) -> int:
        """Count the files in a directory with a given extension."""
        path = os.path.join(self.model_dir, f"*.{extension}")
        return len(glob.glob(path))

    @property
    def type(self) -> ModelTypes:
        """Return the type of the model."""
        return self._type

    @property
    def family(self) -> str:
        """Return the model family grouping."""
        return self._type.family

    @property
    def model_dir(self) -> str:
        """Return the stored model directory."""
        return self._model_dir

    @property
    def engine_dir(self) -> str:
        """Return the stored engine directory."""
        return self._engine_dir

    @property
    def world_size(self) -> int:
        """Return the world size."""
        ws = self._gpu_info["world_size"]
        return typing.cast(int, ws)

    @property
    def compute_cap(self) -> str:
        """Return the compute capability version."""
        cc = self._gpu_info["compute_cap"]
        return typing.cast(str, cc)

    @property
    def format(self) -> ModelFormats:
        """Return the format of the model."""
        return self._format

    @property
    def hash(self) -> str:
        """Return the hash of the model."""
        if not self._hash:
            _LOGGER.info("Calculating model hash.")
            self._hash = _fast_hash_dir(self.model_dir)
        return self._hash

    @property
    def _last_hash_path(self) -> str:
        """Return the path to the last known hash file."""
        return os.path.join(self.engine_dir, "hash")

    def conversion_is_needed(self) -> bool:
        """Determine if the engine conversion is required."""
        if not os.path.isfile(self._last_hash_path):
            _LOGGER.debug("No engine file exists. Will generate an engine file.")
            return True
        with open(self._last_hash_path, "r", encoding="ASCII") as hash_file:
            last_hash = hash_file.read()
        if last_hash != self.hash:
            _LOGGER.debug("Change in model hash detected. Will regnerate engine file.")
            return True
        _LOGGER.debug("Existing engine file found.")
        return False

    def write_hash(self) -> None:
        """Write the model hash to the engine directory."""
        with open(self._last_hash_path, "w", encoding="ASCII") as hash_file:
            hash_file.write(self.hash)
