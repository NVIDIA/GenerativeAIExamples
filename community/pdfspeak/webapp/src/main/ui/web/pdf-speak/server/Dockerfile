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

FROM node:12.22.9 as build
WORKDIR /app


COPY server/package*.json ./
RUN npm install


#COPY .certs /app/.certs
COPY server/env.txt ./env.txt


COPY server .


RUN rm -rf node_modules
RUN npm install --force
RUN npm install dotenv --save


EXPOSE 8090
CMD ["npm", "start"]
