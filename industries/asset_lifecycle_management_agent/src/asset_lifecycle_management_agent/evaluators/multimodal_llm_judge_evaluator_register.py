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


class MultimodalLLMJudgeEvaluatorConfig(EvaluatorBaseConfig, name="multimodal_llm_judge_evaluator"):
    """Configuration for Multimodal LLM Judge evaluator with text and visual evaluation capabilities."""
    
    llm_name: str = Field(description="Name of the LLM to use as judge (should support vision for multimodal evaluation)")
    judge_prompt: str = Field(
        description="Prompt template for the judge LLM. Should include {question}, {reference_answer}, and {generated_answer} placeholders. This prompt works for both text-only and multimodal evaluation.",
        default="""You are an expert evaluator for Asset Lifecycle Management agentic workflows. Your task is to evaluate how well a generated response (which may include both text and visualizations) matches the reference answer for a given question.

Question: {question}

Reference Answer: {reference_answer}

Generated Response: {generated_answer}

Please evaluate the complete response considering:

TEXT EVALUATION:
1. Factual accuracy and correctness of technical information
2. Completeness of the response (does it answer all parts of the question?)
3. Technical accuracy for Asset Lifecycle Management context (RUL predictions, sensor data analysis, etc.)
4. Appropriate use of Asset Lifecycle Management and predictive maintenance terminology and concepts

VISUAL EVALUATION (if plots/charts are present):
1. Does the visualization show the correct data/variables as specified in the reference?
2. Are the axes labeled correctly and with appropriate ranges?
3. Does the plot type (line chart, bar chart, distribution, etc.) match what was requested?
4. Are the data values, trends, and patterns approximately correct?
5. Is the visualization clear and appropriate for Asset Lifecycle Management analysis?
6. Does the plot help answer the original question effectively?

COMBINED EVALUATION:
1. Do the text and visual elements complement each other appropriately?
2. Does the overall response provide a complete answer?
3. Is the combination more helpful than text or visuals alone would be?

For Asset Lifecycle Management context, pay special attention to:
- RUL (Remaining Useful Life) predictions and trends
- Sensor data patterns and operational settings
- Time-series data representation
- Unit/engine-specific data filtering
- Dataset context (FD001, FD002, etc.)

Provide your evaluation as a JSON object with the following format:
{{
    "score": <float: 0.0, 0.5, or 1.0>,
    "reasoning": "<detailed explanation of your evaluation, covering both text and visual elements if present>"
}}

The score should be:
- 1.0: Completely correct response - text and any visuals match reference accurately, comprehensive and helpful
- 0.5: Partially correct response - some elements correct but significant issues in text or visuals
- 0.0: Completely wrong response - major errors in text or visuals that make the response unhelpful"""
    )


@register_evaluator(config_type=MultimodalLLMJudgeEvaluatorConfig)
async def register_multimodal_llm_judge_evaluator(config: MultimodalLLMJudgeEvaluatorConfig, builder: EvalBuilder):
    """Register the Multimodal LLM Judge evaluator with NeMo Agent Toolkit."""
    from nat.builder.framework_enum import LLMFrameworkEnum
    
    from .multimodal_llm_judge_evaluator import MultimodalLLMJudgeEvaluator
    
    # Get the LLM instance
    llm = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    
    # Create the evaluator instance
    evaluator = MultimodalLLMJudgeEvaluator(
        llm=llm,
        judge_prompt=config.judge_prompt,
        max_concurrency=builder.get_max_concurrency()
    )
    
    yield EvaluatorInfo(
        config=config, 
        evaluate_fn=evaluator.evaluate, 
        description="Multimodal LLM Judge Evaluator with Text and Visual Evaluation Capabilities for Asset Lifecycle Management"
    )