"""
Multimodal LLM Judge Evaluator

An enhanced evaluator that uses llama-3.2-90b-instruct to evaluate both text and visual outputs
from agentic workflows. This evaluator is specifically designed for predictive maintenance 
responses that may include plots and visualizations.
"""

import asyncio
import logging
import os
import re
from typing import Any, Dict, Union, Optional
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from aiq.eval.evaluator.base_evaluator import BaseEvaluator
from aiq.eval.evaluator.evaluator_model import EvalInputItem, EvalOutputItem

try:
    from PIL import Image
    import base64
    from io import BytesIO
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL not available. Image evaluation will be disabled.")

logger = logging.getLogger(__name__)


class MultimodalLLMJudgeEvaluator(BaseEvaluator):
    """
    Enhanced multimodal LLM Judge evaluator using llama-3.2-90b-instruct that can evaluate
    responses containing both text and visual elements (plots).
    
    This evaluator automatically detects plot paths in responses and includes
    visual analysis in the evaluation process using a unified prompt.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        judge_prompt: str,
        max_concurrency: int = 4,
    ):
        super().__init__(max_concurrency=max_concurrency, tqdm_desc="Multimodal LLM Judge Evaluating")
        self.llm = llm
        self.judge_prompt = judge_prompt
        
        # Create the prompt template
        self.prompt_template = ChatPromptTemplate.from_template(self.judge_prompt)
        
        logger.debug("Multimodal LLM Judge evaluator initialized.")
        logger.debug(f"Model: llama-3.2-90b-instruct")

    @classmethod
    def from_config(
        cls,
        llm: BaseChatModel,
        judge_prompt: str,
        max_concurrency: int = 4,
        **kwargs
    ):
        """Create MultimodalLLMJudgeEvaluator from configuration parameters."""
        return cls(
            llm=llm,
            judge_prompt=judge_prompt,
            max_concurrency=max_concurrency
        )

    async def evaluate_item(self, item: EvalInputItem) -> EvalOutputItem:
        """
        Evaluate a single EvalInputItem that may contain text and/or visual elements.
        
        This method uses a unified evaluation approach that handles both text-only
        and text+visual responses with a single comprehensive prompt.
        """
        question = str(item.input_obj) if item.input_obj else ""
        reference_answer = str(item.expected_output_obj) if item.expected_output_obj else ""
        generated_answer = str(item.output_obj) if item.output_obj else ""

        try:
            # Check if the response contains plots
            plot_paths = self._extract_plot_paths(generated_answer)
            
            # Use unified evaluation for both text-only and text+visual responses
            return await self._evaluate_unified(
                item, question, reference_answer, generated_answer, plot_paths
            )
                
        except Exception as e:
            logger.exception("Error evaluating item %s: %s", item.id, e)
            return EvalOutputItem(
                id=item.id,
                score=0.0,
                reasoning={
                    "error": f"Evaluation failed: {str(e)}",
                    "question": question,
                    "reference_answer": reference_answer,
                    "generated_answer": generated_answer,
                    "plot_paths": [],
                    "num_images_analyzed": 0,
                    "evaluation_type": "ERROR"
                }
            )

    def _extract_plot_paths(self, response: str) -> list[str]:
        """Extract all PNG file paths from the generated response."""
        plot_paths = []
        
        # Look for PNG file paths in the response with improved patterns
        png_patterns = [
            r'([^\s\[\]]+\.png)',  # Original pattern but excluding brackets
            r'([/][^\s\[\]]+\.png)',  # Paths starting with /
            r'([A-Za-z]:[^\s\[\]]+\.png)',  # Windows paths starting with drive letter
            r'file://([^\s\[\]]+\.png)',  # file:// URLs
            r'\[([^\[\]]+\.png)\]',  # Paths inside square brackets
            r'located at ([^\s]+\.png)',  # "located at path.png" pattern
            r'saved.*?([/][^\s]+\.png)',  # "saved at /path.png" pattern
        ]
        
        for pattern in png_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                # Clean up the match - remove any trailing punctuation
                clean_match = match.rstrip('.,;:!?)]')
                # Check if the file actually exists
                if os.path.exists(clean_match):
                    plot_paths.append(clean_match)
        
        # Also look for responses that mention plot/chart generation even if file doesn't exist
        # This helps with cases where files are generated after response but before evaluation
        plot_indicators = [
            r'plot.*generated', r'chart.*generated', r'histogram.*generated',
            r'visualization.*generated', r'\.png.*generated', r'plot.*saved',
            r'chart.*saved', r'saved.*\.png'
        ]
        
        has_plot_indicator = any(re.search(indicator, response, re.IGNORECASE) 
                                for indicator in plot_indicators)
        
        # If we detect plot generation language but no existing files, 
        # try to find PNG files in the output_data directory that might be related
        if has_plot_indicator and not plot_paths:
            output_dir = "/Users/vikalluru/Documents/GenerativeAIExamples/industries/manufacturing/predictive_maintenance_agent/output_data"
            if os.path.exists(output_dir):
                png_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
                # Add the most recently modified PNG files
                for png_file in png_files[-3:]:  # Last 3 PNG files as a heuristic
                    full_path = os.path.join(output_dir, png_file)
                    plot_paths.append(full_path)
                
        return list(set(plot_paths))  # Remove duplicates

    async def _evaluate_unified(
        self, 
        item: EvalInputItem, 
        question: str, 
        reference_answer: str, 
        generated_answer: str,
        plot_paths: list[str]
    ) -> EvalOutputItem:
        """
        Unified evaluation method that handles both text-only and text+visual responses.
        Uses a single comprehensive prompt that works for both scenarios.
        """
        try:
            # Load and encode images if plot paths are provided
            image_data_list = []
            valid_plot_paths = []
            
            if plot_paths and HAS_PIL:
                for plot_path in plot_paths:
                    image_data = self._load_and_encode_image(plot_path)
                    if image_data:
                        image_data_list.append(image_data)
                        valid_plot_paths.append(plot_path)
            
            # Determine evaluation type based on whether we have valid images
            has_visuals = len(image_data_list) > 0
            evaluation_type = "multimodal" if has_visuals else "text_only"
            
            logger.info(f"Evaluation for item {item.id}: has_visuals={has_visuals}, plot_paths={plot_paths}, valid_plot_paths={valid_plot_paths}, image_data_count={len(image_data_list)}")
            
            # Use the configured judge_prompt and add explicit evaluation mode instruction
            prompt_text = self.judge_prompt.format(
                question=question,
                reference_answer=reference_answer,
                generated_answer=generated_answer
            )
            
            # Add explicit instruction based on whether we have visuals
            if has_visuals:
                prompt_text += f"\n\n🚨 CRITICAL OVERRIDE 🚨\nYou can see {len(image_data_list)} plot image(s) attached to this message.\nYou MUST respond with 'EVALUATION TYPE: PLOT' and evaluate the attached images against the reference description.\nIGNORE any text analysis - focus ONLY on the visual plot content."
                logger.info(f"Using PLOT evaluation mode for item {item.id} with {len(image_data_list)} images")
            else:
                prompt_text += "\n\n🚨 CRITICAL OVERRIDE 🚨\nNo images are attached to this message.\nYou MUST respond with 'EVALUATION TYPE: TEXT' and evaluate only the text content.\nDo NOT attempt plot evaluation."
                logger.info(f"Using TEXT evaluation mode for item {item.id}")
            
            # Call LLM using LangChain
            if has_visuals:
                # Call with images using LangChain multimodal capability
                response_text = await self._call_visual_api_langchain(
                    prompt_text, image_data_list
                )
            else:
                # Call without images (text-only)
                response_text = await self._call_api_langchain(
                    question, reference_answer, generated_answer
                )
            
            # Parse the response
            logger.info(f"LLM response for item {item.id}: {response_text[:200]}...")
            score, reasoning = self._parse_evaluation_response(response_text)
            
            # Build reasoning object 
            reasoning_obj = {
                "question": question,
                "reference_answer": reference_answer,
                "generated_answer": generated_answer,
                "llm_judgment": reasoning,
                "plot_paths": valid_plot_paths,
                "num_images_analyzed": len(image_data_list),
                "evaluation_type": "PLOT" if has_visuals else "TEXT"
            }
            
            return EvalOutputItem(
                id=item.id,
                score=score,
                reasoning=reasoning_obj
            )
            
        except Exception as e:
            logger.exception("Error in unified evaluation for item %s: %s", item.id, e)
            return EvalOutputItem(
                id=item.id,
                score=0.0,
                reasoning={
                    "error": f"Unified evaluation failed: {str(e)}",
                    "question": question,
                    "reference_answer": reference_answer,
                    "generated_answer": generated_answer,
                    "plot_paths": [],
                    "num_images_analyzed": 0,
                    "evaluation_type": "ERROR"
                }
            )

    async def _call_api_langchain(
        self, 
        question: str, 
        reference_answer: str, 
        generated_answer: str
    ) -> str:
        """Call the API using LangChain for text-only evaluation."""
        messages = self.prompt_template.format_messages(
            question=question,
            reference_answer=reference_answer,
            generated_answer=generated_answer
        )
        
        response = await self.llm.ainvoke(messages)
        return response.content

    async def _call_visual_api_langchain(
        self, 
        prompt_text: str, 
        image_data_list: list[str]
    ) -> str:
        """Call the API using LangChain for visual evaluation with multiple images."""
        # Create content with text and all images
        content = [
            {
                "type": "text",
                "text": prompt_text
            }
        ]
        
        # Add all images to the content
        for image_data in image_data_list:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_data}"
                }
            })
        
        messages = [
            HumanMessage(content=content)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content

    def _load_and_encode_image(self, image_path: str) -> Optional[str]:
        """Load an image file and encode it as base64."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to bytes buffer
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                # Encode as base64
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return image_data
                
        except Exception as e:
            logger.exception("Error loading image from %s: %s", image_path, e)
            return None

    def _parse_evaluation_response(self, response_text: str) -> tuple[float, str]:
        """Parse the evaluation response and extract score and reasoning."""
        try:
            import json
            
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
                return score, reasoning
        
        # Process the parsed JSON result
        if isinstance(eval_result, dict) and 'score' in eval_result:
            score = eval_result.get('score', 0.0)
            reasoning = eval_result.get('reasoning', response_text)
        else:
            # If not proper JSON format, try to extract score from text
            score = self._extract_score_from_text(response_text)
            reasoning = response_text
            
        # Ensure score is valid (0.0, 0.5, or 1.0)
        if isinstance(score, (int, float)):
            # Round to nearest valid score
            if score <= 0.25:
                score = 0.0
            elif score <= 0.75:
                score = 0.5
            else:
                score = 1.0
        else:
            score = 0.0
            reasoning = f"Could not parse score from LLM response: {response_text}"
        
        return score, reasoning

    def _extract_score_from_text(self, text: str) -> float:
        """
        Extract a numeric score from text response if JSON parsing fails.
        Looks for patterns like "Score: 0.8" or "8/10" or "80%" and maps to 0.0, 0.5, 1.0
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
                    
                    # Normalize different scales to 0-1 range first
                    if '/10' in pattern:
                        value = value / 10.0
                    elif '%' in pattern or '/100' in pattern:
                        value = value / 100.0
                    
                    # Now map to 0.0, 0.5, 1.0
                    if value <= 0.25:
                        return 0.0
                    elif value <= 0.75:
                        return 0.5
                    else:
                        return 1.0
                        
                except ValueError:
                    continue
        
        # Default to 0.0 if no score found
        logger.warning("Could not extract score from text: %s", text)
        return 0.0