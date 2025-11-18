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

import logging
from typing import Any, Dict

from pydantic import Field, BaseModel

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from nat.data_models.component_ref import LLMRef, FunctionRef
from nat.builder.framework_enum import LLMFrameworkEnum

logger = logging.getLogger(__name__)

class CodeGenerationAssistantConfig(FunctionBaseConfig, name="code_generation_assistant"):
    """
    NeMo Agent Toolkit function to generate and execute Python code based on input instructions and context.
    This tool combines code generation with direct execution, returning results and any generated files.
    """
    llm_name: LLMRef = Field(description="The LLM to use for code generation")
    code_execution_tool: FunctionRef = Field(description="The code execution tool to run generated code")
    output_folder: str = Field(description="The path to the output folder for generated files", default="/output_data")
    verbose: bool = Field(description="Enable verbose logging", default=True)
    max_retries: int = Field(description="Maximum number of retries if code execution fails", default=0)


@register_function(config_type=CodeGenerationAssistantConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def code_generation_assistant(
    config: CodeGenerationAssistantConfig, builder: Builder
):
    class CodeGenerationInputSchema(BaseModel):
        instructions: str = Field(description="Complete instructions including context, data information, and requirements for the code to be generated")

    # Get the LLM and code execution tool from builder
    llm = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    code_execution_fn = builder.get_function(config.code_execution_tool)
    max_retries = config.max_retries
    
    async def _generate_and_execute_code(
        instructions: str,
    ) -> str:
        """
        Generate and execute code based on complete instructions.
        
        Args:
            instructions: Complete instructions including context, data information, and requirements for what the code should do
            
        Returns:
            String containing execution results and summary
        """
        
        system_prompt = """You are an expert Python developer. Generate MINIMAL, EFFICIENT code.

**CRITICAL OUTPUT REQUIREMENT:**
OUTPUT ONLY THE CODE. NO COMMENTS. NO DOCSTRINGS. NO EXPLANATIONS.
Generate only the code needed. Your response must contain ONLY executable Python code which will be DIRECTLY EXECUTED IN A SANDBOX.

**DATABASE PATH:**
For SQLite operations, the database file is located at: '/workspace/database/nasa_turbo.db'
ALWAYS use this exact path when connecting to the database.

**UTILITIES (OPTIONAL - ONLY FOR RUL TRANSFORMATIONS):**
ONLY IF the task involves piecewise RUL transformation, you may use:
- utils.apply_piecewise_rul_transformation(df, maxlife=100, time_col='time_in_cycles', rul_col='RUL')
  Takes a pandas DataFrame and returns it with an added 'transformed_RUL' column using piecewise transformation.

To use utilities (ONLY if needed for RUL transformation):
```python
import sys
sys.path.append("/workspace")
import utils

# Your code using the utility
df_transformed = utils.apply_piecewise_rul_transformation(df, maxlife=100)
```

DO NOT import utils unless specifically needed for RUL transformation tasks.

**CODE REQUIREMENTS:**
1. Generate COMPLETE, SYNTACTICALLY CORRECT Python code
2. ALWAYS finish the complete code - never stop mid-statement
3. EVERY if/elif statement MUST have a complete return statement or action
4. NO comments, NO docstrings, NO explanations
5. Use minimal variable names (df, fig, data, etc.)
6. **CRITICAL FILE PATH RULE**: Use ONLY the filename directly (e.g., "filename.json"), NOT "output_data/filename.json"
7. **DATABASE PATH RULE**: Use '/workspace/database/nasa_turbo.db' for SQLite connections
8. **IF YOU STILL NEED TO SAVE FILES, THEN PRINT FILE NAMES TO STDOUT. (eg: print("Saved file to: filename.json"))**

GENERATE CODE ONLY. NO COMMENTS. NO EXPLANATIONS."""

        user_prompt = """**INSTRUCTIONS:**
{instructions}. Generate a Python code that fulfills these instructions."""

        if config.verbose:
            logger.info(f"Generating code with instructions: {instructions}")

        try:
            from langchain_core.prompts.chat import ChatPromptTemplate
            
            # Create prompt template following the existing pattern
            prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", user_prompt)])
            coding_chain = prompt | llm
            
            # Generate code using the LLM with proper parameter passing
            response = await coding_chain.ainvoke({
                "instructions": instructions
            })
            
            # Clean up the response to extract just the code
            raw_code = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            code = _clean_generated_code(raw_code)
            
            if config.verbose:
                logger.info(f"Generated code length: {len(code)} characters")
                logger.info(f"Generated code:\n{code}")
            
            # Execute the generated code with retry logic
            for attempt in range(max_retries + 1):
                if config.verbose:
                    logger.info(f"Attempt {attempt + 1}/{max_retries + 1}: Executing generated code...")
                
                # Check if code appears incomplete
                def is_code_incomplete(code):
                    is_truncated = (not code.endswith(')') and not code.endswith('"') and 
                                  not code.endswith("'") and not code.endswith(';'))
                    has_incomplete_fig_write = 'fig.write' in code and not 'fig.write_html(' in code
                    return is_truncated or has_incomplete_fig_write
                
                # Skip execution if code is incomplete on retry attempts
                execution_failed = False
                error_info = ""
                
                if is_code_incomplete(code):
                    execution_failed = True
                    error_info = "Code generation was incomplete - code appears to be truncated or has incomplete statements"
                    logger.warning(f"Code appears incomplete: {code[-100:]}")
                else:
                    # Execute the code
                    execution_result = await code_execution_fn.acall_invoke(generated_code=code)
                    
                    if config.verbose:
                        logger.info(f"Execution result: {execution_result}")
                    
                    # Parse result
                    process_status = execution_result.get('process_status', 'unknown')
                    raw_stdout = execution_result.get('stdout', '')
                    stderr = execution_result.get('stderr', '')
                    
                    # Handle nested JSON result
                    actual_stdout, actual_stderr = raw_stdout, stderr
                    try:
                        if raw_stdout.startswith('{"') and raw_stdout.endswith('}\n'):
                            import json
                            nested = json.loads(raw_stdout.strip())
                            if nested.get('process_status') == 'error' or nested.get('stderr'):
                                process_status = 'error'
                                actual_stdout = nested.get('stdout', '')
                                actual_stderr = nested.get('stderr', '')
                    except:
                        pass
                    
                    # Check if execution succeeded
                    if process_status in ['completed', 'success'] and not actual_stderr:
                        # Success! Return result
                        generated_files = _extract_file_paths(actual_stdout, config.output_folder)
                        file_count = len(generated_files)
                        
                        if file_count > 0:
                            file_list = ', '.join([f.split('/')[-1] for f in generated_files])
                            response = f"Code executed successfully. Generated {file_count} file(s): {file_list}"
                        else:
                            response = "Code executed successfully."
                        
                        if actual_stdout:
                            clean_output = actual_stdout.strip().replace('\n', ' ')
                            response += f"\n\nOutput: {clean_output}"
                        
                        logger.info(f"Code generation successful: {response}")
                        return response
                    else:
                        # Execution failed
                        execution_failed = True
                        error_info = ""
                        if actual_stderr:
                            error_info += f"Error: {actual_stderr.strip()}"
                        if actual_stdout:
                            error_info += f"\nOutput: {actual_stdout.strip()}"
                
                # If we have retries left, ask LLM to fix the code
                if execution_failed and attempt < max_retries:
                    logger.warning(f"Execution failed, asking LLM to fix (attempt {attempt + 1})...")
                    
                    fix_prompt_text = f"""The previous code needs to be fixed. Please analyze the issue and generate corrected Python code.

ORIGINAL INSTRUCTIONS: {instructions}

PREVIOUS CODE:
{code}

ISSUE TO FIX:
{error_info}

Please generate corrected Python code that fixes the problem. Follow all requirements:
- Use '/workspace/database/nasa_turbo.db' for database connections
- Only import utils if doing RUL transformations (use sys.path.append("/workspace"))
- Generate only executable Python code
- No comments or explanations
- Handle file paths correctly (use only filename, not paths)
- Complete all code blocks properly
- Ensure the code is complete and not truncated

CORRECTED CODE:"""

                    try:
                        fix_prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", fix_prompt_text)])
                        fix_chain = fix_prompt | llm
                        fix_response = await fix_chain.ainvoke({})
                        raw_fixed_code = fix_response.content.strip() if hasattr(fix_response, 'content') else str(fix_response).strip()
                        code = _clean_generated_code(raw_fixed_code)
                        
                        if config.verbose:
                            logger.info(f"Generated corrected code:\n{code}")
                        
                    except Exception as e:
                        logger.error(f"Failed to generate corrected code: {e}")
                        break
                elif execution_failed:
                    # Max retries reached
                    break
            
            # All retries failed
            response = f"Code generation failed after {max_retries + 1} attempts."
            if error_info:
                error_text = error_info.strip().replace('\n', ' ')
                response += f" Last error: {error_text}"
            response += " Consider using alternative approaches."
            
            logger.error(response)
            return response
            
        except Exception as e:
            logger.error(f"Error in code generation and execution: {e}")
            return f"Error in code generation and execution: {str(e)}"
    
    yield FunctionInfo.from_fn(
        fn=_generate_and_execute_code,
        input_schema=CodeGenerationInputSchema,
        description="""Generate and execute Python code based on complete instructions. 
        Accepts comprehensive instructions including context, data information, and requirements in a single parameter.
        Includes retry logic with max_retries parameter for handling execution failures.
        Returns a summary with execution status, generated files, and output details.
        Specializes in data analysis, visualization, and file processing tasks.
        Include all necessary context, data file information, and requirements in the instructions parameter.""")
    
    if config.verbose:
        logger.info("Code generation assistant initialized successfully")


def _clean_generated_code(raw_code: str) -> str:
    """
    Clean generated code by removing markdown formatting and explanatory text.
    
    Args:
        raw_code: Raw code string from LLM response
        
    Returns:
        Cleaned code string with only executable code
    """
    code = raw_code.strip()
    
    # Remove markdown code blocks if present
    if code.startswith("```python"):
        code = code[9:]  # Remove ```python
    elif code.startswith("```"):
        code = code[3:]  # Remove ```
        
    if code.endswith("```"):
        code = code[:-3]  # Remove closing ```
        
    code = code.strip()
    
    # Remove any explanatory text that might appear after the code
    # Look for common patterns that indicate explanatory text
    explanatory_patterns = [
        "\nThis script performs",
        "\nThis code performs",
        "\nThe script does",
        "\nThe code does",
        "\nExplanation:",
        "\nSummary:",
        "\nThe above code",
        "\nThis will",
        "\nThe generated code"
    ]
    
    for pattern in explanatory_patterns:
        if pattern in code:
            code = code.split(pattern)[0].strip()
            break
    
    # Also remove any line that starts with explaining the script
    lines = code.split('\n')
    clean_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        # Skip lines that look like explanations
        if (stripped_line.startswith('This script') or 
            stripped_line.startswith('This code') or
            stripped_line.startswith('The script') or
            stripped_line.startswith('The code') or
            stripped_line.startswith('Explanation:') or
            (stripped_line and not any(char in stripped_line for char in ['=', '(', ')', '[', ']', '{', '}', 'import', 'from', 'def', 'class', 'if', 'for', 'while', 'try', 'except', 'with', '#']))):
            continue
        clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()

def _extract_file_paths(stdout: str, output_folder: str) -> list:
    """Extract generated file paths from execution output."""
    import re
    import os
    
    files = []
    # Look for common patterns indicating file generation
    patterns = [
        r'saved to[:\s]+([^\s\n]+\.(?:html|png|jpg|jpeg|pdf|csv|json))',
        r'([^\s\n]+\.(?:html|png|jpg|jpeg|pdf|csv|json))',
        r'Plot saved to[:\s]+([^\s\n]+)',
        r'File saved[:\s]+([^\s\n]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, stdout, re.IGNORECASE)
        for match in matches:
            file_path = match.strip().strip('"\'')
            if file_path and not file_path.startswith('#'):
                # Convert relative paths to absolute if needed
                if not os.path.isabs(file_path):
                    full_path = os.path.join(output_folder, file_path.lstrip('./'))
                else:
                    full_path = file_path
                files.append(full_path)
    
    return list(set(files))  # Remove duplicates 