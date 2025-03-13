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

FROM node:18-alpine as build
WORKDIR /app

# Install build dependencies first
RUN apk add --no-cache python3 make g++ build-base

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy rest of the files
COPY env.txt .env
#COPY .certs /app/.certs
COPY . ./

# Force clean install of dependencies to avoid version conflicts
RUN rm -rf node_modules
RUN npm install --force
RUN npm run build

EXPOSE 3002
CMD ["npm", "start"]
