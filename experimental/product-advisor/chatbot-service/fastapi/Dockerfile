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

# Use the specified Python slim image
FROM python:3.10.12-slim

RUN apt-get -y update
RUN apt-get -y install python3-pip

COPY ./chatbot-service/fastapi/requirements.txt /
WORKDIR /
RUN pip3 install -r requirements.txt

COPY ./nvretail /nvretail
RUN cd /nvretail && pip3 install .

WORKDIR /app/

# Run the application
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5001"]
