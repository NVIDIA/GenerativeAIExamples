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

from pydantic import Field

from nat.builder.builder import EvalBuilder
from nat.builder.evaluator import EvaluatorInfo
from nat.cli.register_workflow import register_evaluator
from nat.data_models.evaluator import EvaluatorBaseConfig


class LLMJudgeEvaluatorConfig(EvaluatorBaseConfig, name="llm_judge"):
    """Configuration for LLM-as-a-Judge evaluator."""
    
    llm_name: str = Field(description="Name of the LLM to use as judge")
    judge_prompt: str = Field(
        description="Prompt template for the judge LLM. Should include {question}, {reference_answer}, and {generated_answer} placeholders",
        default="""You are an expert evaluator for Asset Lifecycle Management systems. Your task is to evaluate how well a generated answer matches the reference answer for a given question.

Question: {question}

Reference Answer: {reference_answer}

Generated Answer: {generated_answer}

Please evaluate the generated answer against the reference answer considering:
1. Factual accuracy and correctness
2. Completeness of the response
3. Technical accuracy for Asset Lifecycle Management context
4. Relevance to the question asked

Provide your evaluation as a JSON object with the following format:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<detailed explanation of your scoring>"
}}

The score should be:
- 1.0: Perfect match, completely accurate and complete
- 0.8-0.9: Very good, minor differences but essentially correct
- 0.6-0.7: Good, mostly correct with some inaccuracies or missing details
- 0.4-0.5: Fair, partially correct but with significant issues
- 0.2-0.3: Poor, mostly incorrect but some relevant information
- 0.0-0.1: Very poor, completely incorrect or irrelevant"""
    )


@register_evaluator(config_type=LLMJudgeEvaluatorConfig)
async def register_llm_judge_evaluator(config: LLMJudgeEvaluatorConfig, builder: EvalBuilder):
    """Register the LLM Judge evaluator with NeMo Agent Toolkit."""
    from nat.builder.framework_enum import LLMFrameworkEnum
    
    from .llm_judge_evaluator import LLMJudgeEvaluator
    
    # Get the LLM instance
    llm = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    
    # Create the evaluator instance
    evaluator = LLMJudgeEvaluator(
        llm=llm,
        judge_prompt=config.judge_prompt,
        max_concurrency=builder.get_max_concurrency()
    )
    
    yield EvaluatorInfo(
        config=config, 
        evaluate_fn=evaluator.evaluate, 
        description="LLM-as-a-Judge Evaluator for Asset Lifecycle Management"
    ) 