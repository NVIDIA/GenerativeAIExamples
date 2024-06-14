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

from typing import Union
from copy import copy
from datetime import datetime, timedelta
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

from accumulator import TextAccumulator
from retriever import NemoRetrieverInterface, NvidiaApiInterface
from common import get_logger, LLMConfig, TimeResponse, UserIntent
from utils import get_llm, classify
from prompts import RAG_PROMPT, INTENT_PROMPT, RECENCY_PROMPT, SUMMARIZATION_PROMPT

logger = get_logger(__name__)

# Maximum number of times to attempt recursive summarization (if enabled)
MAX_SUMMARIZATION_ATTEMPTS = 3

class RagChain:
    def __init__(
        self,
        config: LLMConfig,
        text_accumulator: TextAccumulator,
        retv_interface: Union[NemoRetrieverInterface, NvidiaApiInterface]
    ):
        self.config = config
        self.text_accumulator = text_accumulator
        self.timestamp_db = text_accumulator.timestamp_db
        self.retv_interface = retv_interface
        self.llm = get_llm(config)
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_PROMPT),
            ("user", "Transcript: '{context}'\nUser: '{input}'\nAI:"),
        ])
        self.chain = self.rag_prompt | self.llm | StrOutputParser()

    def get_chat_chain(self, template):
        prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("user", "{input}"),
        ])
        return prompt | self.llm | StrOutputParser()

    def generate(self, docs):
        generator = self.chain.stream(
            {"context": "\n".join(d.page_content for d in docs),
             "input": self.config.question}
        )
        for tok in generator:
            yield tok

    def answer(self):
        if not self.config.use_knowledge_base:
            # Just chat then return
            chat_prompt = ChatPromptTemplate.from_messages([("user", "{input}")])
            chat_chain = chat_prompt | self.llm | StrOutputParser()
            for tok in chat_chain.stream({"input": self.config.question}):
                yield tok
            return

        # Determine user intent and answer accordingly
        intent = classify(
            self.config.question,
            self.get_chat_chain(INTENT_PROMPT),
            UserIntent
        )

        if intent is None or intent.intentType == 'Unknown':
            logger.warning('Unknown user intent, falling back to basic RAG')
        elif intent.intentType in ['RecentSummary', 'TimeWindow']:
            try:
                # Determine the time units user is asking about
                recency = classify(
                    self.config.question,
                    self.get_chat_chain(RECENCY_PROMPT),
                    TimeResponse
                )

                # Answer with a summary of the recent entries
                if intent.intentType == 'RecentSummary':
                    yield from self.answer_by_recent(recency)
                # Answer a question about entries near some point in the past
                elif intent.intentType == 'TimeWindow':
                    yield from self.answer_by_past(recency)
                return
            except Exception as e:
                # If there's an exception for some reason, just fall back to basic retrieval
                logger.warning(
                    f"Exception {e} occured trying to answer with {intent.intentType}, "
                    f"falling back to basic RAG"
                )
                intent.intentType = 'SpecificTopic'

        # Do basic RAG with semantic similarity retrieval
        yield from self.answer_by_relevence()
        return

    def answer_by_relevence(self):
        # Retrieve
        docs = self.retv_interface.search(
            self.config.question,
            max_entries=self.config.max_docs
        )

        # Output
        if not len(docs):
            yield "*Found no documents related to the query*"
        else:
            yield f"*Returned {len(docs)} related entries*\n\n"
            yield from self.generate(docs)

    def answer_by_recent(self, recency: TimeResponse):
        # Retrieve
        seconds = recency.to_seconds()
        tstamp = datetime.now() - timedelta(seconds=seconds)
        docs = self.timestamp_db.recent(tstamp)
        yield f"*Found {len(docs)} entries from the last {seconds:.0f}s*\n"

        # Handle case when we get too many docs
        if len(docs) > self.config.max_docs:
            if self.config.allow_summary:
                # Use recursive summarization
                yield f"*Using summarization to reduce context*\n"
                for attempt in range(MAX_SUMMARIZATION_ATTEMPTS):
                    docs = self.summarize(docs)
                    yield f"*Reduced to {len(docs)} entries on attempt {attempt+1}*\n"
                    if len(docs) <= self.config.max_docs:
                        break
                docs = docs[-self.config.max_docs:]
            else:
                # Just throw some away
                docs = docs[-self.config.max_docs:]
                oldest = docs[0].metadata['tstamp'].second
                yield f"*Reduced to last {len(docs)} entries, oldest is from {oldest}s ago*\n"

        # Output
        if len(docs):
            yield "\n"
            yield from self.generate(docs)

    def answer_by_past(self, recency: TimeResponse, window=90):
        # Retrieve
        seconds = recency.to_seconds()
        tstamp = datetime.now() - timedelta(seconds=seconds)
        docs = self.timestamp_db.past(tstamp, window=window)
        yield f"*Found {len(docs)} entries from {seconds:.0f}s ago (+/- {window}s)*\n"

        # Handle case when we get too many docs
        if len(docs) > self.config.max_docs:
            if self.config.allow_summary:
                # Use recursive summarization
                yield f"*Using summarization to reduce context*\n"
                for attempt in range(MAX_SUMMARIZATION_ATTEMPTS):
                    docs = self.summarize(docs)
                    yield f"*Reduced to {len(docs)} entries on attempt {attempt+1}*\n"
                    if len(docs) <= self.config.max_docs:
                        break
                docs = docs[-self.config.max_docs:]
            else:
                # Just throw some away
                sorted_docs = sorted(docs, key=lambda doc: abs(doc.metadata['tstamp'] - tstamp))
                docs = sorted_docs[:self.config.max_docs]
                dt = abs(docs[-1].metadata['tstamp'] - tstamp).seconds
                yield f"*Reduced to last {len(docs)} entries, furthest is {dt}s away*\n"

        # Output
        if len(docs):
            yield "\n"
            yield from self.generate(docs)

    def summarize(self, docs):
        """ Given a set of documents, leverage the LLM to reduce context via summarization
        """
        summary_chain = self.get_chat_chain(SUMMARIZATION_PROMPT)
        splitter = copy(self.text_accumulator.splitter)
        splitter._chunk_overlap = 0

        # Summarize each chunk of 'max_docs' entries
        summary = ""
        for i in range(0, len(docs), self.config.max_docs):
            k = min(i + self.config.max_docs, len(docs))
            text = " ".join(docs[j].page_content for j in range(i, k))
            summary = f"{summary} {summary_chain.invoke({'input': text})}"

        return [Document(page_content=chunk) for chunk in splitter.split_text(summary)]
