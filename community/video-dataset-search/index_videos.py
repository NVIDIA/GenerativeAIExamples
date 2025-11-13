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

from utils import setup_qdrant, index_videos
from config import COLLECTION_NAME

if __name__ == "__main__":
    print("Setting up Qdrant...")
    client = setup_qdrant()
    
    print("\nIndexing videos...")
    indexed_count = index_videos(client=client)
    
    print(f"\nIndexing complete: {indexed_count} videos indexed")
    
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' now has {collection_info.points_count} points")

