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

"""The custom errors raised by the model server."""
import typing


class ModelServerException(Exception):
    """The base class for any custom expections."""


class UnsupportedFormatException(ModelServerException):
    """An error that indicates the model format is not supported for the provided type."""

    def __init__(self, model_type: str, supported: typing.List[str]):
        """Initialize the exception."""
        super().__init__(
            "Unsupported model type and format combination. "
            + f"{model_type} models are supported in the following formats: {str(supported)}"
        )
