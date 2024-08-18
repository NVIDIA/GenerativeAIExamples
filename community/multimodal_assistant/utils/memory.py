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

from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain_core.prompts.prompt import PromptTemplate

def init_memory(llm, prompt_str):
    SUMMARY_PROMPT = PromptTemplate(
            input_variables=["summary", "new_lines"], template=prompt_str
    )
    memory = ConversationSummaryMemory(llm=llm, prompt=SUMMARY_PROMPT)

    return memory

def get_summary(memory):
    return memory.buffer

def add_history_to_memory(memory, input_str, output_str):

    # add message to memory
    chat_memory = memory.chat_memory
    chat_memory.add_user_message(input_str)
    chat_memory.add_ai_message(output_str)

    # generate new summary
    buffer = memory.buffer
    new_buffer = memory.predict_new_summary(
            chat_memory.messages[-2:], buffer
            )
    # update buffer
    memory.buffer = new_buffer
    print("\n\nUpdated summary: ", new_buffer)

    return memory

