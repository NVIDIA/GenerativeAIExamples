# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

FROM python:3.13-slim
WORKDIR /usr/src/app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire nv-ingest directory
COPY nv-ingest /usr/src/app/nv-ingest

# Install nv-ingest client
RUN pip install -e /usr/src/app/nv-ingest/client
RUN pip install --no-cache-dir -r /usr/src/app/nv-ingest/client/requirements.txt

# Copy and install main requirements
COPY webapp/src/main/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY webapp/src/main/backend .
#COPY webapp/src/main/backend/.certs /usr/src/app/.certs
COPY webapp/src/main/backend/audio_outputs /usr/src/app/audio_outputs
COPY webapp/src/main/backend/uploads /usr/src/app/uploads

EXPOSE 5050
CMD ["python", "-m", "marshaler.chat_io_service"]
