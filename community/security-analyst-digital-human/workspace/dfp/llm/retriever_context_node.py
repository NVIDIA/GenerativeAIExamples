# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from morpheus.llm import LLMContext
from morpheus.llm import LLMNodeBase
from dfp.llm.nemo_retriever_client import RetrieverClient

logger = logging.getLogger(__name__)


class RetrieverContextNode(LLMNodeBase):
    """
    Collects context text chunks from NeMo Retriever for use downstream in RAG based generation.

    Parameters
    ----------
    retriever_client : RetrieverClient
        The client instance to use to generate responses.
        
    input_name : str
        Name of column containing the search query. Defaults to `rag_query`.
    """

    def __init__(self, retriever_client: RetrieverClient, input_name:str = "rag_query") -> None:
        super().__init__()

        self._retriever_client = retriever_client
        self._input_names = [input_name]
        
    def get_input_names(self) -> list[str]:
        return self._input_names
        
    async def execute(self, context: LLMContext) -> LLMContext:  # pylint: disable=invalid-overridden-method

        # Get the inputs
        inputs = context.get_inputs()
        print("Optimized RAG Query:")
        print(inputs['rag_query'][0])

        results = self._retriever_client.search(inputs['rag_query'][0])
        
        results = '\nCONTEXT\n '.join([r[0] for r in results])
        
        context.set_output(results)

        return context