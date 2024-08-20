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

"""
This is an implementation of a time-informed FAISS database using Hugging Face
Instruct Embeddings. As text is streamed in, it is appended to the most recent
entry, re-chunked, and added to the database with an associated timestamp. This
allows for time-based entry retrieval for cases where recent entries or entries
from a specific point in time are requested.

Note that this style of implementation won't scale well when using many different
data sources or users querying the database - it is intended to be an example
implementation of what is possible with this sort of streaming workflow.
"""

import sqlite3
import datetime
import numpy as np

from common import get_logger
from datetime import datetime
from langchain.docstore.document import Document

logger = get_logger(__name__)

class TimestampDatabase:
    """ Use SQLite database to track time-based entries
    """
    def __init__(self):
        self.conn = sqlite3.connect('timeseries.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Create table
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                text TEXT,
                timestamp DATETIME,
                source_id TEXT
            )
            '''
        )
        self.conn.commit()

    def insert_docs(self, docs, source_id):
        tnow = datetime.now()
        self.cursor.executemany(
            '''
            INSERT INTO messages (text, timestamp, source_id) VALUES (?, ?, ?)
            ''',
            [(doc, tnow, source_id) for doc in docs]
        )
        self.conn.commit()

    def reformat(self, doc):
        return {'content': doc[1], 'timestamp': doc[2], 'source_id': doc[3]}

    def reformat(self, doc):
        return Document(
            page_content=doc[1],
            metadata={
                'tstamp': datetime.strptime(doc[2], "%Y-%m-%d %H:%M:%S.%f"),
                'source_id': doc[3]
            }
        )

    def recent(self, tstamp):
        """ Return all entries since tstamp
        """
        self.cursor.execute("SELECT * FROM messages WHERE timestamp >= ?", (tstamp,))
        docs = self.cursor.fetchall()
        return [self.reformat(doc) for doc in docs]

    def past(self, tstamp, window=90):
        """ Return entries within 'window' seconds of tstamp
        """
        tstart = tstamp - datetime.timedelta(seconds=window)
        tend = tstamp + datetime.timedelta(seconds=window)
        self.cursor.execute('SELECT * FROM messages WHERE timestamp BETWEEN ? AND ?', (tstart, tend))
        docs = self.cursor.fetchall()
        return [self.reformat(doc) for doc in docs]