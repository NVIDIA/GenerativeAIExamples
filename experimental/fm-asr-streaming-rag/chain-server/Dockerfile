# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

ARG BASE_IMAGE_URL="nvcr.io/nvidia/pytorch"
ARG BASE_IMAGE_TAG="23.12-py3"

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

ENV TZ="America/New_York"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

RUN --mount=type=bind,source=requirements.txt,target=/opt/requirements.txt \
    pip install --no-cache-dir -r /opt/requirements.txt

COPY . /opt

# RUN apt-get update && apt-get install -y libpq-dev

RUN apt-get remove python3-pip

WORKDIR /opt
ENTRYPOINT ["uvicorn", "server:app"]