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

from pydantic import BaseModel
from common import UserIntent, TimeResponse

def format_schema(pydantic_obj: BaseModel):
    return str(
        pydantic_obj.model_json_schema()
    ).replace("\'", "\"").replace("{", "{{").replace("}", "}}")

def format_json(text: str):
    return text.replace("{", "{{").replace("}", "}}")

RAG_PROMPT = """\
You are a query answering system specialized in providing accurate responses to \
questions based on a live radio transcript. Your input includes:
- 'Transcript': a radio transcript that you're currently listening to.
- 'User': the user query that you're responding to.
Your task is to answer the user query by directly referencing and extracting \
information from these transcripts. Ensure your responses are concise, accurate, \
and solely based on the provided context.
"""

INTENT_PROMPT = ("""\
You are an advanced classification system designed to understand and categorize \
user intent from natural language input. Your sole output is JSON, representing \
the classification of the intent according to the following specification:

""" +  format_schema(UserIntent) + """\

There are 4 options for user intent: 'SpecificTopic', 'RecentSummary', 'TimeWindow', and 'Unknown':
- 'SpecificTopic': If the user is asking about a specific topic, such as a factual question \
or seeking specific information. Examples: "Who is the president of the US?", "What time is the \
game tonight?", "What is the weather forecast for tonight?".
- 'RecentSummary': If the user is asking for a summary or overview of content or news within a \
recent timeframe. Examples: "Can you summarize the last hour of content?", "What have the main \
topics been over the last 5 minutes?", "Tell me the main stories of the past 2 hours.".
- 'TimeWindow': If the user is asking about the focus of the conversation from a specified time in \
the past. Examples: "What were they talking about 15 minutes ago?", "What was the focus an hour ago?".
- If the user's intent is not clear, or if the intent cannot be confidently determined, classify \
this as 'Unknown'.

Your response should be in JSON format and include the classification type and the \
original query, with no additional explanations. Follow this JSON structure:

{{"intentType": <SpecificTopic/RecentSummary/TimeWindow/Unknown>}}

Examples:
"What were they talking about 15 minutes ago?" --> {{"intentType": "TimeWindow"}}
"Can you summarize the last hour of content?" --> {{"intentType": "RecentSummary"}}
"Who is the president of the US?" --> {{"intentType": "SpecificTopic"}}
"Hey there!" --> {{"intentType": "Unknown"}}

Ensure accuracy in classification by carefully analyzing the user's request. \
Provide no other information or output."
""")

# Define recency analysis prompt
recency_examples_json = [
    {'timeNum': 5, 'timeUnit': 'minutes'},
    {'timeNum': 7, 'timeUnit': 'hours'},
    {'timeNum': 2, 'timeUnit': 'days'},
    {'timeNum': 15, 'timeUnit': 'minutes'}
]
recency_examples_obj = [TimeResponse(**ex) for ex in recency_examples_json]
recency_examples_str = [
    "Tell me what's happened in the last {timeNum} {timeUnit}.",
    "In the previous {timeNum} {timeUnit}, what are the main highlights?",
    "Distill the last {timeNum} {timeUnit} down to a small summary",
    "What was the topic {timeNum} {timeUnit} ago?"
]
recency_examples = [
    ex_str.format(timeNum=obj.timeNum, timeUnit=obj.timeUnit)
    for (ex_str, obj) in zip(recency_examples_str, recency_examples_obj)
]

RECENCY_PROMPT = ("""\
You are an expert at restructuring natural language input into JSON. Your input is
natural language from a user and your output is JSON and nothing else. Provide no
explanations, just JSON. You will respond in JSON per the following specification:

""" +  format_schema(TimeResponse) + """\

Here are some example conversions:

""" +
f"'{recency_examples[0]}' --> '{format_json(recency_examples_obj[0].model_dump_json())}'\n" +
f"'{recency_examples[1]}' --> '{format_json(recency_examples_obj[1].model_dump_json())}'\n" +
f"'{recency_examples[2]}' --> '{format_json(recency_examples_obj[2].model_dump_json())}'\n" + """

Convert the user input below into this JSON format.
""")

SUMMARIZATION_PROMPT = """\
You are a sophisticated summarization tool designed to condense large blocks \
of text into a concise summary. Given the user text, reduce the character \
count by distilling into only the most important information.
"""