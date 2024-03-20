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

import os
import logging
import faiss
import datetime
import numpy as np

from typing import List

from langchain_community.embeddings   import HuggingFaceInstructEmbeddings
from langchain_community.docstore     import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain.text_splitter          import RecursiveCharacterTextSplitter

LOG_LEVEL = logging.getLevelName(os.environ.get('CHAIN_LOG_LEVEL', 'WARN').upper())
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

EMBED_INSTRUCT = "Represent the sentence for retrieval: "
EMBED_QUERY = "Represent the question for retrieving supporting texts from the sentence: "

class TimeIndex:
    """ Manages database entry indices, tying the entry index to its timestamp
    """
    def __init__(self):
        self.index: List[int] = []
        self.tstamp: np.ndarray = np.array([], dtype=np.datetime64)

    def size(self):
        return len(self.index)

    def get(self, i):
        return self.index[i], self.tstamp[i]

    def get_range(self, start=None, stop=None):
        return self.index[start:stop], self.tstamp[start:stop]

    def reduce_to(self, start=None, stop=None):
        self.index, self.tstamp = self.get_range(start, stop)

    def append(self, new_id, new_tstamp):
        self.index.append(new_id)
        self.tstamp = np.append(self.tstamp, new_tstamp)

    def time_window(self, tstart=None, tend=None):
        if not tstart:
            tstart = self.tstamp[0]
        if not tend:
            tend = self.tstamp[-1]
        mask = (self.tstamp >= tstart) & (self.tstamp <= tend)
        return [self.index[i] for i in np.where(mask)[0]]

    def next_id(self):
        return self.index[-1] + 1 if self.size() > 0 else 0

class DatabaseManager:
    """ Self-managed FAISS database that ties entries to when they were added
    """
    def __init__(self, embedding_model, embedding_dim):
        self._timeindex = TimeIndex()
        self._db_index = faiss.IndexFlatL2(embedding_dim)
        self._db = FAISS(
            embedding_model,
            self._db_index,
            InMemoryDocstore({}),
            {}
        )

    def size(self):
        return self._timeindex.size()

    def pop_back(self):
        if self.size() == 0:
            return None

        # Get the last document and delete it
        idx, _ = self._timeindex.get(-1)
        doc = self._db.docstore._dict[idx]
        self._db.delete([self._db.index_to_docstore_id[idx]])

        # Adjust the indices and timestamps
        self._timeindex.reduce_to(stop=-1)
        return doc

    def pop_front(self):
        if self.size() == 0:
            return None

        # Get the document and delete it
        idx, _ = self._timeindex.get(0)
        doc = self._db.docstore._dict[idx]
        self._db.delete([self._db.index_to_docstore_id[idx]])

        # Adjust the indices and timestamps
        self._timeindex.reduce_to(start=1)
        return doc

    def push_back(self, entry, tstamp):
        # Add the entry to the database
        new_id = self._timeindex.next_id()
        self._db.add_texts(
            [entry], ids=[new_id], metadatas=[{'tstamp': tstamp.strftime("%Y-%m-%d %H:%M:%S")}]
        )
        self._timeindex.append(new_id, tstamp)

    def as_retriever(self, search_kwargs):
        return self._db.as_retriever(
            search_type='similarity_score_threshold',
            search_kwargs=search_kwargs
        )

    def get_by_time(self, tstart=None, tend=None):
        if self.size() == 0:
            return []
        indices = self._timeindex.time_window(tstart=tstart, tend=tend)
        return [self._db.docstore._dict[i] for i in indices]

class VectorStoreInterface:
    """ Manages interfacing with the vector store
    """
    def __init__(self, chunk_size=1024, chunk_overlap=200):
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        self._embed_model = HuggingFaceInstructEmbeddings(
            embed_instruction=EMBED_INSTRUCT,
            query_instruction=EMBED_QUERY
        )
        embedding_pool = self._embed_model.dict()['client'][1]
        self.embedding_dim = embedding_pool.get_config_dict()['word_embedding_dimension']
        self._db_mgr = DatabaseManager(self._embed_model, self.embedding_dim)

    def dbsize(self):
        return self._db_mgr.size()

    def store_text(self, text, tstamp):
        """ Split text into chunks and store in DB
        """
        new_entries = self._text_splitter.split_text(text)
        for entry in new_entries:
            self._db_mgr.push_back(entry, tstamp)
        return {
            "status":
                f"Added {len(new_entries)} entries.  " +
                f"Number of total database entries: {self.dbsize()}"
        }

    def store_streaming_text(self, text, tstamp):
        """ Assume last entry was short, delete it, append it to new text, and re-chunk
        """
        prev_doc = self._db_mgr.pop_back()
        if prev_doc:
            text = f"{prev_doc.page_content} {text}"
        return self.store_text(text, tstamp)

    def search(self, query, max_entries=4, score_threshold=0.65):
        """ Search DB for similar documents
        """
        search_kwargs = {'k': max_entries, 'score_threshold': score_threshold}
        retriever = self._db_mgr.as_retriever(search_kwargs)
        return [doc for doc in retriever.get_relevant_documents(query)]

    def recent(self, tstamp):
        """ Return all entries since tstamp
        """
        return self._db_mgr.get_by_time(tstart=tstamp)

    def past(self, tstamp, window=90):
        """ Return entries within 'window' seconds of tstamp
        """
        tstart = tstamp - datetime.timedelta(seconds=window)
        tend = tstamp + datetime.timedelta(seconds=window)
        return self._db_mgr.get_by_time(tstart=tstart, tend=tend)