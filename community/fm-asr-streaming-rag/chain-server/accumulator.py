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

from common import get_logger
from database import TimestampDatabase
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = get_logger(__name__)

#todo: Multi-thread to handle multiple concurrent streams
#todo: Add time-triggered embedding (i.e. embed after N seconds if no updates)
class TextAccumulator:
    def __init__(self, db_interface, chunk_size=1024, chunk_overlap=200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        self.accumulators = {}
        self.timestamp_db = TimestampDatabase()
        self.db_interface = db_interface

    def update(self, source_id, text):
        """ Update this source ID's accumulator and embed if necessary
        """
        if source_id not in self.accumulators:
            self.accumulators[source_id] = ""

        # Add new text, then chunk using text splitter. If chunking results in
        # more than 1 document, embed the full-sized chunks.
        docs = self.splitter.split_text(f"{self.accumulators[source_id]} {text}")
        self.accumulators[source_id], new_docs = docs[-1], docs[:-1]
        self.timestamp_db.insert_docs(new_docs, source_id)
        self.db_interface.add_docs(new_docs, source_id)

        return {"status": f"Added {len(new_docs)} entries"}