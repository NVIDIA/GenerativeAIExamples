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

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*



# Copy the entire nv-ingest directory
COPY nv-ingest /app/nv-ingest

# Install nv-ingest client
RUN pip install -e /app/nv-ingest/client
RUN pip install --no-cache-dir -r app/nv-ingest/client/requirements.txt
RUN pip install --no-cache-dir langchain-nvidia-ai-endpoints==0.3.9



# Install Python packages
RUN pip install --no-cache-dir \
    jupyterlab \
    nvidia-riva-client \
    numpy \
    sounddevice \
    soundfile \
    ipython 

# Create working directories
WORKDIR /app
RUN mkdir -p /app/notebooks-examples /app/data && \
    git clone https://github.com/nvidia-riva/python-clients.git /app/notebooks-examples/riva-examples
# Set environment variables
ENV JUPYTER_ENABLE_LAB=yes

# Expose JupyterLab port
EXPOSE 8888

# Start JupyterLab
CMD cp -r /app/notebooks-examples/* /app/notebooks/ && \
    jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.notebook_dir=/app/notebooks

