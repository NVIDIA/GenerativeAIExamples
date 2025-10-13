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
import logging
import os
from typing import List, Tuple, Dict, Any

from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableAssign

from .utils import get_llm, get_prompts, get_env_variable

logger = logging.getLogger(__name__)
prompts = get_prompts()

def _retry_score_generation(chain, inputs: Dict[str, Any], max_retries: int = 3, config: Dict[str, Any] = {}) -> int:
    """Helper method to retry score generation with error handling.
    
    Args:
        chain: The chain to execute
        inputs: Input dictionary for the chain
        max_retries: Maximum number of retry attempts
        
    Returns:
        int: Generated score (0, 1, or 2), or 0 if all retries fail
    """
    for retry in range(max_retries):
        try:
            response = chain.invoke(inputs, config=config)
            # Extract numeric score from response
            for score in [2, 1, 0]:
                if str(score) in response:
                    return score
        except Exception as e:
            logger.warning(f"Retry {retry + 1}/{max_retries} failed: {str(e)}")
            if retry == max_retries - 1:
                logger.error(f"All retries failed for score generation")
                return 0
            continue
    return 0

class ReflectionCounter:
    """Tracks the number of reflection iterations across query rewrites and response regeneration."""
    def __init__(self, max_loops: int):
        self.max_loops = max_loops
        self.current_count = 0
    
    def increment(self) -> bool:
        """Increment counter and return whether we can continue."""
        if self.current_count >= self.max_loops:
            return False
        self.current_count += 1
        return True
    
    @property
    def remaining(self) -> int:
        return max(0, self.max_loops - self.current_count)

def check_context_relevance(retriever_query: str,
                          retriever,
                          ranker,
                          reflection_counter: ReflectionCounter,
                          enable_reranker: bool = True) -> Tuple[List[str], bool]:
    """Check relevance of retrieved context and optionally rewrite query for better results.
    
    Args:
        retriever_query (str): Current query to use for retrieval
        retriever: Document retriever instance
        ranker: Optional document ranker instance
        reflection_counter: ReflectionCounter instance to track loop count
        enable_reranker: Whether to use the reranker if available
        
    Returns:
        Tuple[List[str], bool]: Retrieved documents and whether they meet relevance threshold
    """
    relevance_threshold = int(os.environ.get("CONTEXT_RELEVANCE_THRESHOLD", 1))
    reflection_llm_name = get_env_variable(variable_name="REFLECTION_LLM", default_value="mistralai/mixtral-8x22b-instruct-v0.1").strip('"').strip("'")
    reflection_llm_endpoint = os.environ.get("REFLECTION_LLM_SERVERURL", "").strip('"').strip("'")
    
    llm_params = {
        "model": reflection_llm_name,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 512
    }
    
    if reflection_llm_endpoint:
        llm_params["llm_endpoint"] = reflection_llm_endpoint
    
    reflection_llm = get_llm(**llm_params)
    
    relevance_template = ChatPromptTemplate.from_messages([
        ("system", prompts["reflection_relevance_check_prompt"]["system"]),
        ("human", "{query}\n\n{context}")
    ])

    query_rewrite_template = ChatPromptTemplate.from_messages([
        ("system", prompts["reflection_query_rewriter_prompt"]["system"]),
        ("human", "{query}")
    ])

    current_query = retriever_query
    
    while reflection_counter.remaining > 0:
        # Get documents using current query
        if ranker and enable_reranker:
            context_reranker = RunnableAssign({
                "context":
                    lambda input: ranker.compress_documents(query=input['question'], documents=input['context'])
            })

            retriever = {"context": retriever} | RunnableAssign({"context": lambda input: input["context"]})
            docs = retriever.invoke(current_query, config={'run_name':'retriever'})
            docs = context_reranker.invoke({"context": docs.get("context", []), "question": current_query}, config={'run_name':'context_reranker'})
            original_docs = docs.get("context", [])
        else:
            original_docs = retriever.invoke(current_query, config={'run_name':'retriever'})
        
        docs = [d.page_content for d in original_docs]

        context_text = "\n".join(docs)
        relevance_chain = relevance_template | reflection_llm | StrOutputParser()
        relevance_score = _retry_score_generation(
            relevance_chain,
            {"query": current_query, "context": context_text},
            config={'run_name':'relevance-checker'}
        )
        
        logger.info(f"Context relevance score: {relevance_score} (threshold: {relevance_threshold})")
        reflection_counter.increment()
        
        if relevance_score >= relevance_threshold:
            return original_docs, True
        
        if reflection_counter.remaining > 0:
            rewrite_chain = query_rewrite_template | reflection_llm | StrOutputParser()
            current_query = rewrite_chain.invoke({"query": current_query}, config={'run_name':'query-rewriter'})
            logger.info(f"Rewritten query (iteration {reflection_counter.current_count}): {current_query}")
    
    return original_docs, False

def check_response_groundedness(response: str,
                              context: List[str],
                              reflection_counter: ReflectionCounter,
                              ) -> Tuple[str, bool]:
    """Check groundedness of generated response against retrieved context.
    
    Args:
        response (str): Generated response to check
        context (List[str]): List of context documents
        reflection_counter: ReflectionCounter instance to track loop count
        
    Returns:
        Tuple[str, bool]: Final response and whether it meets groundedness threshold
    """
    groundedness_threshold = int(os.environ.get("RESPONSE_GROUNDEDNESS_THRESHOLD", 1))
    reflection_llm_name = get_env_variable(variable_name="REFLECTION_LLM", default_value="mistralai/mixtral-8x22b-instruct-v0.1").strip('"').strip("'")
    reflection_llm_endpoint = os.environ.get("REFLECTION_LLM_SERVERURL", "").strip('"').strip("'")
    
    llm_params = {
        "model": reflection_llm_name,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1024
    }
    
    if reflection_llm_endpoint:
        llm_params["llm_endpoint"] = reflection_llm_endpoint
    
    reflection_llm = get_llm(**llm_params)
    
    groundedness_template = ChatPromptTemplate.from_messages([
        ("system", prompts["reflection_groundedness_check_prompt"]["system"]),
        ("human", "{context}\n\n{response}")
    ])

    context_text = "\n".join(context)
    current_response = response
    
    while reflection_counter.remaining > 0:
        groundedness_chain = groundedness_template | reflection_llm | StrOutputParser()
        groundedness_score = _retry_score_generation(
            groundedness_chain,
            {"context": context_text, "response": current_response}
        )
        
        logger.info(f"Response groundedness score: {groundedness_score} (threshold: {groundedness_threshold})")
        reflection_counter.increment()
        
        if groundedness_score >= groundedness_threshold:
            return current_response, True
        
        if reflection_counter.remaining > 0:
            regen_prompt = ChatPromptTemplate.from_messages([
                ("system", prompts["reflection_response_regeneration_prompt"]["system"]),
                ("human", f"Context: {context_text}\n\nPrevious response: {current_response}\n\n"
                         "Generate a new, more grounded response:")
            ])
            
            regen_chain = regen_prompt | reflection_llm | StrOutputParser()
            current_response = regen_chain.invoke({}, config={'run_name':'response-regenerator'})
            logger.info(f"Regenerated response (iteration {reflection_counter.current_count})")
    
    return current_response, False 