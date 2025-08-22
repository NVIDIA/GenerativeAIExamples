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
    output_folder: str = Field(description="The path to the output folder for generated files", default="/workspace")
    verbose: bool = Field(description="Enable verbose logging", default=True)


@register_function(config_type=CodeGenerationAssistantConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def code_generation_assistant(
    config: CodeGenerationAssistantConfig, builder: Builder
):
    class CodeGenerationInputSchema(BaseModel):
        instructions: str = Field(description="Complete instructions including context, data information, and requirements for the code to be generated")

    # Get the LLM and code execution tool from builder
    llm = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    code_execution_fn = builder.get_function(config.code_execution_tool)
    
    async def _generate_and_execute_code(
        instructions: str
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

**WORKSPACE UTILITIES AVAILABLE:**
A '/workspace/utils' folder contains a pre-built function for predictive maintenance tasks:
- utils.apply_piecewise_rul_transformation(file_path, maxlife=125): 
  * Transform RUL data with realistic knee pattern
  * Automatically saves the transformed data back to the original JSON file

**CRITICAL REQUIREMENT: ALWAYS USE UTILITIES when available instead of writing custom implementations.**
This ensures reliable, tested functionality and consistent results.

To use utilities, start your code with:
```python
import sys
sys.path.append('/workspace')
import utils
```

**UTILITY USAGE GUIDELINES:**
- Check if your task can be accomplished using the utility function
- For RUL transformations: ALWAYS use utils.apply_piecewise_rul_transformation() instead of custom logic
- The utility automatically saves the file, so NO NEED to write additional saving code
- The utility handles all error checking and provides detailed success messages
- Use maxlife parameter to control the knee threshold (default: 125)
- Simply call the utility and print its return message to show results

**CODE REQUIREMENTS:**
1. Generate COMPLETE, SYNTACTICALLY CORRECT Python code
2. ALWAYS finish the complete code - never stop mid-statement
3. EVERY if/elif statement MUST have a complete return statement or action
4. NO comments, NO docstrings, NO explanations
5. Use minimal variable names (df, fig, data, etc.)
6. The working directory is already set to: {output_folder}
7. **FILE PATH REQUIREMENT**: While generating Python code, use "./filename" to access files in the workspace directory
8. Use relative paths like "./filename" for all file operations
9. For data analysis: use pandas and plotly
10. For visualizations: save as HTML with fig.write_html()
11. For data: save as JSON with to_json()

**FILE MODIFICATION PREFERENCE:**
- PREFER modifying existing files IN-PLACE when possible
- Use utilities that modify files in-place (like RUL transformation)
- Only create new files when explicitly required

**MANDATORY COMPLETION:**
Every script MUST end with file saving and print statement:
```python
fig.write_html('./filename.html')
print(f"Successfully saved file to: filename.html")
```

GENERATE CODE ONLY. NO COMMENTS. NO EXPLANATIONS."""

        user_prompt = """**INSTRUCTIONS:**
{instructions}

**IMPORTANT FILE PATH HANDLING:**
- Input files mentioned in instructions should be accessed using ONLY the filename (e.g., "data.json")
- All files are available in the current working directory
- Use "./filename" pattern for all file operations

**UTILITIES REMINDER:**
- Check if task can be accomplished using workspace utilities
- Add path setup: sys.path.append('/workspace'); import utils
- For RUL transformations: use utils.apply_piecewise_rul_transformation(file_path)
- Utilities handle error checking and provide detailed success messages

Generate the Python code that fulfills these instructions."""

        if config.verbose:
            logger.info(f"Generating code with instructions: {instructions}")

        try:
            from langchain_core.prompts.chat import ChatPromptTemplate
            
            # Create prompt template following the existing pattern
            prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", user_prompt)])
            coding_chain = prompt | llm
            
            # Generate code using the LLM with proper parameter passing
            response = await coding_chain.ainvoke({
                "output_folder": config.output_folder,
                "instructions": instructions
            })
            
            # Clean up the response to extract just the code
            raw_code = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            code = _clean_generated_code(raw_code)
            
            if config.verbose:
                logger.info(f"Generated code length: {len(code)} characters")
                logger.info(f"Generated code:\n{code}")
            
            # Check if code appears to be truncated and request completion
            is_truncated = (not code.endswith(')') and not code.endswith('"') and 
                          not code.endswith("'") and not code.endswith(';'))
            has_incomplete_fig_write = 'fig.write' in code and not 'fig.write_html(' in code
            
            if is_truncated or has_incomplete_fig_write:
                logger.warning("Generated code appears to be incomplete. Requesting completion from LLM...")
                logger.warning(f"Code ends with: '{code[-100:]}'")
                
                # Create a completion prompt
                completion_prompt = f"""The following Python code was generated but appears to be incomplete:

```python
{code}
```

Please complete ONLY the remaining code that's missing. Do not repeat the existing code, just provide the completion starting from where it left off. Ensure you complete any unfinished statements and add proper file saving and print statements.

Requirements:
- Complete any unfinished lines or statements
- If there's a visualization (fig), ensure it's saved with fig.write_html('./filename.html')
- If there's data output, save with appropriate method (e.g., to_json())
- Add a print statement showing the saved file
- Do not include any explanations, just the completion code

Completion:"""

                try:
                    # Request completion from LLM
                    completion_response = await llm.ainvoke(completion_prompt)
                    raw_completion = completion_response.content.strip() if hasattr(completion_response, 'content') else str(completion_response).strip()
                    completion_code = _clean_generated_code(raw_completion)
                    
                    # Append completion to original code
                    if completion_code:
                        code = code + "\n" + completion_code
                        logger.info(f"Code completion added. New total length: {len(code)} characters")
                        if config.verbose:
                            logger.info(f"Added completion:\n{completion_code}")
                    
                except Exception as e:
                    logger.error(f"Failed to get code completion: {e}")
                    # Fallback to simple auto-fix for fig.write
                    if code.endswith('fig.write'):
                        code += f"_html('./plot.html')\nprint(f'Plot saved to: plot.html')"
                        logger.info("Applied fallback auto-fix for fig.write statement")
            
            # Execute the generated code
            if config.verbose:
                logger.info("Executing generated code...")
            
            execution_result = await code_execution_fn.acall_invoke(generated_code=code)
            
            if config.verbose:
                logger.info(f"Code execution completed with status: {execution_result.get('process_status', 'unknown')}")
                logger.info(f"Execution output: {execution_result}")
            
            # Parse execution result and create clean response
            process_status = execution_result.get('process_status', 'unknown')
            raw_stdout = execution_result.get('stdout', '')
            stderr = execution_result.get('stderr', '')
            
            # Handle nested JSON in stdout and check for actual execution errors
            actual_execution_failed = False
            try:
                if raw_stdout.startswith('{"') and raw_stdout.endswith('}\n'):
                    import json
                    nested_result = json.loads(raw_stdout.strip())
                    nested_status = nested_result.get('process_status', '')
                    actual_stdout = nested_result.get('stdout', '')
                    actual_stderr = nested_result.get('stderr', '')
                    
                    # Check if the nested execution actually failed
                    if nested_status == 'error' or actual_stderr:
                        actual_execution_failed = True
                        process_status = 'error'  # Override the outer status
                        if config.verbose:
                            logger.warning(f"Detected nested execution error: {actual_stderr}")
                else:
                    actual_stdout = raw_stdout
                    actual_stderr = stderr
            except:
                actual_stdout = raw_stdout
                actual_stderr = stderr
            
            # Extract generated files from output
            generated_files = _extract_file_paths(actual_stdout, config.output_folder)
            
            # Create clean string response following the codebase pattern
            if process_status in ['completed', 'success'] and not actual_execution_failed:
                file_count = len(generated_files)
                if file_count > 0:
                    file_list = ', '.join([f.split('/')[-1] for f in generated_files])
                    response = f"Code executed successfully. Generated {file_count} file(s): {file_list}"
                else:
                    response = "Code executed successfully."
                
                if actual_stdout:
                    # Clean and add output info
                    clean_output = actual_stdout.strip().replace('\n', ' ')
                    response += f"\n\nOutput: {clean_output}"
            else:
                response = f"Code execution failed with status: {process_status}"
                if actual_stderr:
                    clean_error = actual_stderr.strip().replace('\n', ' ')
                    response += f"\nError: {clean_error}"
                if actual_stdout:
                    clean_output = actual_stdout.strip().replace('\n', ' ')
                    response += f"\nOutput: {clean_output}"

            logger.info(f"Code generation assistant response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error in code generation and execution: {e}")
            return f"Error in code generation and execution: {str(e)}"
    
    yield FunctionInfo.from_fn(
        fn=_generate_and_execute_code,
        input_schema=CodeGenerationInputSchema,
        description="""Generate and execute Python code based on complete instructions. 
        Accepts comprehensive instructions including context, data information, and requirements in a single parameter.
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