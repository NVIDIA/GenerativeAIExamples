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

import asyncio
import logging
from typing import Any, Dict, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from nat.eval.evaluator.base_evaluator import BaseEvaluator
from nat.eval.evaluator.evaluator_model import EvalInputItem, EvalOutputItem

logger = logging.getLogger(__name__)


class LLMJudgeEvaluator(BaseEvaluator):
    """
    LLM-as-a-Judge evaluator that uses a large language model to evaluate 
    how well the generated response matches the reference answer.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        judge_prompt: str,
        max_concurrency: int = 4,
    ):
        super().__init__(max_concurrency=max_concurrency, tqdm_desc="LLM Judge Evaluating")
        self.llm = llm
        self.judge_prompt = judge_prompt
        
        # Create the prompt template
        self.prompt_template = ChatPromptTemplate.from_template(self.judge_prompt)
        logger.debug("LLM Judge evaluator initialized with custom prompt.")

    async def evaluate_item(self, item: EvalInputItem) -> EvalOutputItem:
        """
        Evaluate a single EvalInputItem using LLM-as-a-judge.
        
        The judge_prompt should contain placeholders for:
        - {question}: The original question/input
        - {reference_answer}: The expected/reference answer  
        - {generated_answer}: The model's generated answer
        
        The LLM should return a JSON object with 'score' and 'reasoning' fields.
        """
        question = str(item.input_obj) if item.input_obj else ""
        reference_answer = str(item.expected_output_obj) if item.expected_output_obj else ""
        generated_answer = str(item.output_obj) if item.output_obj else ""

        try:
            # Format the prompt with the actual values
            messages = self.prompt_template.format_messages(
                question=question,
                reference_answer=reference_answer,
                generated_answer=generated_answer
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            response_text = response.content
            
            # Try to parse the response as JSON
            try:
                import json
                import re
                
                # First try to parse as direct JSON
                eval_result = json.loads(response_text)
                
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from markdown code blocks
                try:
                    # Look for JSON within markdown code blocks (```json or just ```)
                    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
                    json_match = re.search(json_pattern, response_text, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(1)
                        eval_result = json.loads(json_str)
                    else:
                        # If no code blocks found, fall back to text extraction
                        raise json.JSONDecodeError("No JSON code blocks found", "", 0)
                        
                except json.JSONDecodeError:
                    # Final fallback to text-based score extraction
                    score = self._extract_score_from_text(response_text)
                    reasoning = response_text
                    eval_result = None
            
            # Process the parsed JSON result
            if eval_result is not None:
                if isinstance(eval_result, dict) and 'score' in eval_result:
                    score = eval_result.get('score', 0.0)
                    reasoning = eval_result.get('reasoning', response_text)
                else:
                    # If not proper JSON format, try to extract score from text
                    score = self._extract_score_from_text(response_text)
                    reasoning = response_text
                    
            # Ensure score is numeric and between 0 and 1
            if isinstance(score, (int, float)):
                score = max(0.0, min(1.0, float(score)))
            else:
                score = 0.0
                reasoning = f"Could not parse score from LLM response: {response_text}"
            
            return EvalOutputItem(
                id=item.id,
                score=score,
                reasoning={
                    "question": question,
                    "reference_answer": reference_answer,
                    "generated_answer": generated_answer,
                    "llm_judgment": reasoning,
                    "raw_response": response_text
                }
            )
            
        except Exception as e:
            logger.exception("Error evaluating item %s: %s", item.id, e)
            return EvalOutputItem(
                id=item.id, 
                score=0.0, 
                reasoning={
                    "error": f"LLM evaluation failed: {str(e)}",
                    "question": question,
                    "reference_answer": reference_answer,
                    "generated_answer": generated_answer
                }
            )

    def _extract_score_from_text(self, text: str) -> float:
        """
        Extract a numeric score from text response if JSON parsing fails.
        Looks for patterns like "Score: 0.8" or "8/10" or "80%"
        """
        import re
        
        # Try to find score patterns in the text
        patterns = [
            r'"?score"?[:\s]*([0-9]*\.?[0-9]+)',  # "score": 0.8, score: 0.8, or score 0.8
            r'([0-9]*\.?[0-9]+)[/\s]*10',     # "8/10" or "8 out of 10"
            r'([0-9]*\.?[0-9]+)%',            # "80%"
            r'([0-9]*\.?[0-9]+)[/\s]*100',    # "80/100" or "80 out of 100"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    value = float(match.group(1))
                    
                    # Normalize different scales to 0-1 range
                    if '/10' in pattern:
                        return value / 10.0
                    elif '%' in pattern or '/100' in pattern:
                        return value / 100.0
                    else:
                        # Assume it's already in 0-1 range, but clamp it
                        return max(0.0, min(1.0, value))
                except ValueError:
                    continue
        
        # Default to 0.0 if no score found
        logger.warning("Could not extract score from text: %s", text)
        return 0.0