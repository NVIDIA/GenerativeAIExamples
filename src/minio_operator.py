# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Minio operator Module to store metadata"""

import os
import json
import logging
from typing import Dict, List
from io import BytesIO

from minio import Minio

logger = logging.getLogger(__name__)

class MinioOperator:
    """Minio operator Class to store metadata using Minio-client"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        default_bucket_name: str = "default-bucket"
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.default_bucket_name = default_bucket_name
        self._make_bucket(bucket_name=self.default_bucket_name)

    def _make_bucket(self, bucket_name: str):
        """Create new bucket if doesn't exists"""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def put_payload(
        self,
        payload: dict,
        object_name: str
    ):
        """Put dictionary to S3 storage using minio client"""
        # Convert payload dictionary to JSON bytes
        json_data = json.dumps(payload).encode("utf-8")

        # Upload JSON data to MinIO
        self.client.put_object(
            self.default_bucket_name,
            object_name,
            BytesIO(json_data),
            len(json_data),
            content_type="application/json"
        )

    def get_payload(
        self,
        object_name: str
    ) -> Dict:
        """Get dictionary from S3 storage using minio client"""
        # Retrieve JSON from MinIO

        try:
            response = self.client.get_object(self.default_bucket_name, object_name)

            # Read and decode the JSON data
            retrieved_data = json.loads(response.read().decode("utf-8"))
            return retrieved_data
        except Exception as e:
            logger.warning(f"Error while getting object from Minio: {e}. Citations or image captions may not be set to true.")
            return {}
    
    def list_payloads(
        self,
        prefix: str = ""
    ) -> List[str]:
        """List payloads from S3 storage using minio client"""
        list_of_objects = list()
        for obj in self.client.list_objects(self.default_bucket_name, prefix=prefix, recursive=True):
            list_of_objects.append(obj.object_name)
        return list_of_objects

    def delete_payloads(
        self,
        object_names: List[str]
    ) -> None:
        """Delete payloads from S3 storage using minio client"""
        for object_name in object_names:
            self.client.remove_object(self.default_bucket_name, object_name)
