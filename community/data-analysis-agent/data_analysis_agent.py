# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os, io, re
import pandas as pd
import numpy as np
import streamlit as st
from openai import OpenAI
import matplotlib.pyplot as plt
from typing import List, Any, Optional

# === Configuration ===
# Global configuration
API_BASE_URL = "https://integrate.api.nvidia.com/v1"
API_KEY = os.environ.get("NVIDIA_API_KEY")

# Plot configuration
DEFAULT_FIGSIZE = (6, 4)
DEFAULT_DPI = 100

# Display configuration
MAX_RESULT_DISPLAY_LENGTH = 300

class ModelConfig:
    """Configuration class for different models."""
    
    def __init__(self, model_name: str, model_url: str, model_print_name: str, 
                 # QueryUnderstandingTool parameters
                 query_understanding_temperature: float = 0.1,
                 query_understanding_max_tokens: int = 5,
                 # CodeGenerationAgent parameters
                 code_generation_temperature: float = 0.2,
                 code_generation_max_tokens: int = 1024,
                 # ReasoningAgent parameters
                 reasoning_temperature: float = 0.2,
                 reasoning_max_tokens: int = 1024,
                 # DataInsightAgent parameters
                 insights_temperature: float = 0.2,
                 insights_max_tokens: int = 512,
                 reasoning_false: str = "detailed thinking off",
                 reasoning_true: str = "detailed thinking on"):
        self.MODEL_NAME = model_name
        self.MODEL_URL = model_url
        self.MODEL_PRINT_NAME = model_print_name
        
        # Function-specific LLM parameters
        self.QUERY_UNDERSTANDING_TEMPERATURE = query_understanding_temperature
        self.QUERY_UNDERSTANDING_MAX_TOKENS = query_understanding_max_tokens
        self.CODE_GENERATION_TEMPERATURE = code_generation_temperature
        self.CODE_GENERATION_MAX_TOKENS = code_generation_max_tokens
        self.REASONING_TEMPERATURE = reasoning_temperature
        self.REASONING_MAX_TOKENS = reasoning_max_tokens
        self.INSIGHTS_TEMPERATURE = insights_temperature
        self.INSIGHTS_MAX_TOKENS = insights_max_tokens
        self.REASONING_FALSE = reasoning_false
        self.REASONING_TRUE = reasoning_true

# Predefined model configurations
MODEL_CONFIGS = {
    "llama-3-1-nemotron-ultra-v1": ModelConfig(
        model_name="nvidia/llama-3.1-nemotron-ultra-253b-v1",
        model_url="https://build.nvidia.com/nvidia/llama-3_1-nemotron-ultra-253b-v1",
        model_print_name="NVIDIA Llama 3.1 Nemotron Ultra 253B v1",
        # QueryUnderstandingTool
        query_understanding_temperature=0.1,
        query_understanding_max_tokens=5,
        # CodeGenerationAgent
        code_generation_temperature=0.2,
        code_generation_max_tokens=1024,
        # ReasoningAgent
        reasoning_temperature=0.6,
        reasoning_max_tokens=1024,
        # DataInsightAgent
        insights_temperature=0.2,
        insights_max_tokens=512,
        reasoning_false="detailed thinking off",
        reasoning_true="detailed thinking on"
    ),
    "llama-3-3-nemotron-super-v1-5": ModelConfig(
        model_name="nvidia/llama-3.3-nemotron-super-49b-v1.5",
        model_url="https://build.nvidia.com/nvidia/llama-3_3-nemotron-super-49b-v1_5",
        model_print_name="NVIDIA Llama 3.3 Nemotron Super 49B v1.5",
        # QueryUnderstandingTool
        query_understanding_temperature=0.1,
        query_understanding_max_tokens=5,
        # CodeGenerationAgent
        code_generation_temperature=0.0,
        code_generation_max_tokens=1024,
        # ReasoningAgent
        reasoning_temperature=0.6,
        reasoning_max_tokens=2048,
        # DataInsightAgent
        insights_temperature=0.2,
        insights_max_tokens=512,
        reasoning_false="/no_think",
        reasoning_true=""
    )
}

# Default configuration (can be changed via environment variable or UI)
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "llama-3-1-nemotron-ultra-v1")
Config = MODEL_CONFIGS.get(DEFAULT_MODEL, MODEL_CONFIGS["llama-3-1-nemotron-ultra-v1"])

# Initialize OpenAI client with configuration
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY
)

def get_current_config():
    """Get the current model configuration based on session state."""
    # Always return the current model from session state
    if "current_model" in st.session_state:
        return MODEL_CONFIGS[st.session_state.current_model]
    
    return MODEL_CONFIGS[DEFAULT_MODEL]

# ------------------  QueryUnderstandingTool ---------------------------
def QueryUnderstandingTool(query: str) -> bool:
    """Return True if the query seems to request a visualisation based on keywords."""
    # Use LLM to understand intent instead of keyword matching
    current_config = get_current_config()
    
    # Prepend the instruction to the query
    full_prompt = f"""You are a query classifier. Your task is to determine if a user query is requesting a data visualization.

IMPORTANT: Respond with ONLY 'true' or 'false' (lowercase, no quotes, no punctuation).

Classify as 'true' ONLY if the query explicitly asks for:
- A plot, chart, graph, visualization, or figure
- To "show" or "display" data visually
- To "create" or "generate" a visual representation
- Words like: plot, chart, graph, visualize, show, display, create, generate, draw

Classify as 'false' for:
- Data analysis without visualization requests
- Statistical calculations, aggregations, filtering, sorting
- Questions about data content, counts, summaries
- Requests for tables, dataframes, or text results

User query: {query}"""
    
    messages = [
        {"role": "system", "content": current_config.REASONING_FALSE},
        {"role": "user", "content": full_prompt}
    ]
    
    response = client.chat.completions.create(
        model=current_config.MODEL_NAME,
        messages=messages,
        temperature=current_config.QUERY_UNDERSTANDING_TEMPERATURE,
        max_tokens=current_config.QUERY_UNDERSTANDING_MAX_TOKENS  # We only need a short response
    )
    
    # Extract the response and convert to boolean

    intent_response = response.choices[0].message.content.strip().lower()

    return intent_response == "true"

# === CodeGeneration TOOLS ============================================


# ------------------  CodeWritingTool ---------------------------------
def CodeWritingTool(cols: List[str], query: str) -> str:
    """Generate a prompt for the LLM to write pandas-only code for a data query (no plotting)."""

    return f"""

    Given DataFrame `df` with columns: 

    {', '.join(cols)}

    Write Python code (pandas **only**, no plotting) to answer: 
    "{query}"

    Rules
    -----
    1. Use pandas operations on `df` only.
    2. Rely only on the columns in the DataFrame.
    3. Assign the final result to `result`.
    4. Return your answer inside a single markdown fence that starts with ```python and ends with ```.
    5. Do not include any explanations, comments, or prose outside the code block.
    6. Use **df** as the sole data source. **Do not** read files, fetch data, or use Streamlit.
    7. Do **not** import any libraries (pandas is already imported as pd).
    8. Handle missing values (`dropna`) before aggregations.

    Example
    -----
    ```python
    result = df.groupby("some_column")["a_numeric_col"].mean().sort_values(ascending=False)
    ```

    """


# ------------------  PlotCodeGeneratorTool ---------------------------
def PlotCodeGeneratorTool(cols: List[str], query: str) -> str:

    """Generate a prompt for the LLM to write pandas + matplotlib code for a plot based on the query and columns."""

    return f"""

    Given DataFrame `df` with columns:

    {', '.join(cols)}

    Write Python code using pandas **and matplotlib** (as plt) to answer:
    "{query}"

    Rules
    -----
    1. Use pandas for data manipulation and matplotlib.pyplot (as plt) for plotting.
    2. Rely only on the columns in the DataFrame.
    3. Assign the final result (DataFrame, Series, scalar *or* matplotlib Figure) to a variable named `result`.
    4. Create only ONE relevant plot. Set `figsize={DEFAULT_FIGSIZE}`, add title/labels.
    5. Return your answer inside a single markdown fence that starts with ```python and ends with ```.
    6. Do not include any explanations, comments, or prose outside the code block.
    7. Handle missing values (`dropna`) before plotting/aggregations.

    """
  

# === CodeGenerationAgent ==============================================

def CodeGenerationAgent(query: str, df: pd.DataFrame, chat_context: Optional[str] = None):
    """Selects the appropriate code generation tool and gets code from the LLM for the user's query."""

    should_plot = QueryUnderstandingTool(query)

    prompt = PlotCodeGeneratorTool(df.columns.tolist(), query) if should_plot else CodeWritingTool(df.columns.tolist(), query)

    # Prepend the instruction to the query
    context_section = f"\nConversation context (recent user turns):\n{chat_context}\n" if chat_context else ""

    full_prompt = f"""You are a senior Python data analyst who writes clean, efficient code. 
    Solve the given problem with optimal pandas operations. Be concise and focused. 
    Your response must contain ONLY a properly-closed ```python code block with no explanations before or after (starts with ```python and ends with ```). 
    Ensure your solution is correct, handles edge cases, and follows best practices for data analysis. 
    If the latest user request references prior results ambiguously (e.g., "it", "that", "same groups"), infer intent from the conversation context and choose the most reasonable interpretation. {context_section}{prompt}"""

    current_config = get_current_config()

    messages = [
        {"role": "system", "content": current_config.REASONING_FALSE},
        {"role": "user", "content": full_prompt}
    ]

    response = client.chat.completions.create(
        model=current_config.MODEL_NAME,
        messages=messages,
        temperature=current_config.CODE_GENERATION_TEMPERATURE,
        max_tokens=current_config.CODE_GENERATION_MAX_TOKENS
    )

    full_response = response.choices[0].message.content

    code = extract_first_code_block(full_response)
    return code, should_plot, ""

# === ExecutionAgent ====================================================

def ExecutionAgent(code: str, df: pd.DataFrame, should_plot: bool):
    """Executes the generated code in a controlled environment and returns the result or error message."""
    
    # Set up execution environment with all necessary modules
    env = {
        "pd": pd,
        "df": df
    }
    
    if should_plot:
        plt.rcParams["figure.dpi"] = DEFAULT_DPI  # Set default DPI for all figures
        env["plt"] = plt
        env["io"] = io
    
    try:
        # Execute the code in the environment
        exec(code, {}, env)
        result = env.get("result", None)
        
        # If no result was assigned, return the last expression
        if result is None:
            # Try to get the last executed expression
            if "result" not in env:
                return "No result was assigned to 'result' variable"
        
        return result
    except Exception as exc:
        return f"Error executing code: {exc}"

# === ReasoningCurator TOOL =========================================
def ReasoningCurator(query: str, result: Any) -> str:
    """Builds and returns the LLM prompt for reasoning about the result."""
    is_error = isinstance(result, str) and result.startswith("Error executing code")
    is_plot = isinstance(result, (plt.Figure, plt.Axes))

    if is_error:
        desc = result
    elif is_plot:
        title = ""
        if isinstance(result, plt.Figure):
            title = result._suptitle.get_text() if result._suptitle else ""
        elif isinstance(result, plt.Axes):
            title = result.get_title()
        desc = f"[Plot Object: {title or 'Chart'}]"
    else:
        desc = str(result)[:MAX_RESULT_DISPLAY_LENGTH]

    if is_plot:
        prompt = f'''
        The user asked: "{query}".
        Below is a description of the plot result:
        {desc}
        Explain in 2–3 concise sentences what the chart shows (no code talk).'''
    else:
        prompt = f'''
        The user asked: "{query}".
        The result value is: {desc}
        Explain in 2–3 concise sentences what this tells about the data (no mention of charts).'''
    return prompt

# === ReasoningAgent (streaming) =========================================
def ReasoningAgent(query: str, result: Any):
    """Streams the LLM's reasoning about the result (plot or value) and extracts model 'thinking' and final explanation."""
    current_config = get_current_config()
    prompt = ReasoningCurator(query, result)

    # Streaming LLM call
    response = client.chat.completions.create(
        model=current_config.MODEL_NAME,
        messages=[
            {"role": "system", "content": current_config.REASONING_TRUE},
            {"role": "user", "content": "You are an insightful data analyst. " + prompt}
        ],
        temperature=current_config.REASONING_TEMPERATURE,
        max_tokens=current_config.REASONING_MAX_TOKENS,
        stream=True
    )

    # Stream and display thinking
    thinking_placeholder = st.empty()
    full_response = ""
    thinking_content = ""
    in_think = False

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            token = chunk.choices[0].delta.content
            full_response += token

            # Simple state machine to extract <think>...</think> as it streams
            if "<think>" in token:
                in_think = True
                token = token.split("<think>", 1)[1]
            if "</think>" in token:
                token = token.split("</think>", 1)[0]
                in_think = False
            if in_think or ("<think>" in full_response and not "</think>" in full_response):
                thinking_content += token
                thinking_placeholder.markdown(
                    f'<details class="thinking" open><summary>🤔 Model Thinking</summary><pre>{thinking_content}</pre></details>',
                    unsafe_allow_html=True
                )

    # After streaming, extract final reasoning (outside <think>...</think>)
    cleaned = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()
    return thinking_content, cleaned

# === DataFrameSummary TOOL (pandas only) =========================================
def DataFrameSummaryTool(df: pd.DataFrame) -> str:
    """Generate a summary prompt string for the LLM based on the DataFrame."""
    prompt = f"""
        Given a dataset with {len(df)} rows and {len(df.columns)} columns:
        Columns: {', '.join(df.columns)}
        Data types: {df.dtypes.to_dict()}
        Missing values: {df.isnull().sum().to_dict()}

        Provide:
        1. A brief description of what this dataset contains
        2. 3-4 possible data analysis questions that could be explored
        Keep it concise and focused."""
    return prompt

# === DataInsightAgent (upload-time only) ===============================

def DataInsightAgent(df: pd.DataFrame) -> str:
    """Uses the LLM to generate a brief summary and possible questions for the uploaded dataset."""
    current_config = get_current_config()
    prompt = DataFrameSummaryTool(df)
    try:
        response = client.chat.completions.create(
            model=current_config.MODEL_NAME,
            messages=[
                {"role": "system", "content": current_config.REASONING_FALSE},
                {"role": "user", "content": "You are a data analyst providing brief, focused insights. " + prompt}
            ],
            temperature=current_config.INSIGHTS_TEMPERATURE,
            max_tokens=current_config.INSIGHTS_MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as exc:
        raise Exception(f"Error generating dataset insights: {exc}")

# === Helpers ===========================================================

def extract_first_code_block(text: str) -> str:
    """Extracts the first Python code block from a markdown-formatted string."""
    start = text.find("```python")
    if start == -1:
        return ""
    start += len("```python")
    end = text.find("```", start)
    if end == -1:
        return ""
    return text[start:end].strip()

# === Main Streamlit App ===============================================

def main():
    st.set_page_config(layout="wide")
    if "plots" not in st.session_state:
        st.session_state.plots = []
    if "current_model" not in st.session_state:
        st.session_state.current_model = DEFAULT_MODEL

    left, right = st.columns([3,7])

    with left:
        st.header("Data Analysis Agent")
        
        # Model selector
        available_models = list(MODEL_CONFIGS.keys())
        model_display_names = {key: MODEL_CONFIGS[key].MODEL_PRINT_NAME for key in available_models}
        
        selected_model = st.selectbox(
            "Select Model",
            options=available_models,
            format_func=lambda x: model_display_names[x],
            index=available_models.index(st.session_state.current_model)
        )
        
        # Get current config for the "Powered by" text - use selected_model for immediate updates
        display_config = MODEL_CONFIGS[selected_model]

        st.markdown(f"<medium>Powered by <a href='{display_config.MODEL_URL}'>{display_config.MODEL_PRINT_NAME}</a></medium>", unsafe_allow_html=True)
        
        file = st.file_uploader("Choose CSV", type=["csv"], key="csv_uploader")
        
        # Update configuration if model changed
        if selected_model != st.session_state.current_model:
            st.session_state.current_model = selected_model
            # Get the updated config for the new model
            new_config = MODEL_CONFIGS[selected_model]

            # Clear chat history when model changes
            if "messages" in st.session_state:
                st.session_state.messages = []
            if "plots" in st.session_state:
                st.session_state.plots = []

            # Regenerate insights immediately if we have data and file is present
            if "df" in st.session_state and file is not None:  # Check if file is still there
                with st.spinner("Generating dataset insights with new model …"):
                    try:
                        st.session_state.insights = DataInsightAgent(st.session_state.df)
                        st.success(f"Insights updated with {new_config.MODEL_PRINT_NAME}")
                    except Exception as e:
                        st.error(f"Error updating insights: {str(e)}")
                        # Clear old insights if regeneration fails
                        if "insights" in st.session_state:
                            del st.session_state.insights
                st.rerun()  # Force UI update to show new insights
        
        
        # Clear data if file is removed (but not during model change). Keep chat history.
        if not file and "df" in st.session_state and "current_file" in st.session_state:
            del st.session_state.df
            del st.session_state.current_file
            if "insights" in st.session_state:
                del st.session_state.insights
            st.rerun()
        
        if file:
            if ("df" not in st.session_state) or (st.session_state.get("current_file") != file.name):
                st.session_state.df = pd.read_csv(file)
                st.session_state.current_file = file.name
                st.session_state.messages = []
                # Generate insights with the current model
                with st.spinner("Generating dataset insights …"):
                    try:
                        st.session_state.insights = DataInsightAgent(st.session_state.df)
                    except Exception as e:
                        st.error(f"Error generating insights: {str(e)}")
            # Ensure insights exist even if they weren't generated properly
            elif "insights" not in st.session_state:
                with st.spinner("Generating dataset insights …"):
                    try:
                        st.session_state.insights = DataInsightAgent(st.session_state.df)
                    except Exception as e:
                        st.error(f"Error generating insights: {str(e)}")
        
        # Display data and insights (always execute if we have data)
        if "df" in st.session_state:
            st.markdown("### Dataset Insights")
            
            # Display insights with model attribution
            if "insights" in st.session_state and st.session_state.insights:
                st.dataframe(st.session_state.df.head())
                st.markdown(st.session_state.insights)
                # Get current config dynamically for model attribution
                current_config_left = get_current_config()
                st.markdown(f"*<span style='color: grey; font-style: italic;'>Generated with {current_config_left.MODEL_PRINT_NAME}</span>*", unsafe_allow_html=True)
            else:
                st.warning("No insights available.")
        else:
            st.info("Upload a CSV to begin chatting with your data.")

    with right:
        st.header("Chat with your data") 
        if "df" in st.session_state:
            # Get current config dynamically for the right column
            current_config_right = get_current_config()
            st.markdown(f"*<span style='color: grey; font-style: italic;'>Using {current_config_right.MODEL_PRINT_NAME}</span>*", unsafe_allow_html=True)
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Manual clear chat control
        clear_col1, clear_col2 = st.columns([9,1])
        with clear_col2:
            if st.button("Clear chat"):
                st.session_state.messages = []
                st.session_state.plots = []
                st.rerun()

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"], unsafe_allow_html=True)
                    if msg.get("plot_index") is not None:
                        idx = msg["plot_index"]
                        if 0 <= idx < len(st.session_state.plots):
                            # Display plot at fixed size
                            st.pyplot(st.session_state.plots[idx], use_container_width=False)

        if "df" in st.session_state:  # allow chat when we have data loaded
            if user_q := st.chat_input("Ask about your data…"):
                st.session_state.messages.append({"role": "user", "content": user_q})
                with st.spinner("Working …"):
                    # Build brief chat context from the last few user messages
                    recent_user_turns = [m["content"] for m in st.session_state.messages if m["role"] == "user"][-3:]
                    context_text = "\n".join(recent_user_turns[:-1]) if len(recent_user_turns) > 1 else None
                    code, should_plot_flag, code_thinking = CodeGenerationAgent(user_q, st.session_state.df, context_text)
                    result_obj = ExecutionAgent(code, st.session_state.df, should_plot_flag)
                    raw_thinking, reasoning_txt = ReasoningAgent(user_q, result_obj)
                    reasoning_txt = reasoning_txt.replace("`", "")

                # Build assistant response
                is_plot = isinstance(result_obj, (plt.Figure, plt.Axes))
                plot_idx = None
                if is_plot:
                    fig = result_obj.figure if isinstance(result_obj, plt.Axes) else result_obj
                    st.session_state.plots.append(fig)
                    plot_idx = len(st.session_state.plots) - 1
                    header = "Here is the visualization you requested:"
                elif isinstance(result_obj, (pd.DataFrame, pd.Series)):
                    header = f"Result: {len(result_obj)} rows" if isinstance(result_obj, pd.DataFrame) else "Result series"
                else:
                    header = f"Result: {result_obj}"

                # Show only reasoning thinking in Model Thinking (collapsed by default)
                thinking_html = ""
                if raw_thinking:
                    thinking_html = (
                        '<details class="thinking">'
                        '<summary>🧠 Reasoning</summary>'
                        f'<pre>{raw_thinking}</pre>'
                        '</details>'
                    )

                # Show model explanation directly 
                explanation_html = reasoning_txt

                # Code accordion with proper HTML <pre><code> syntax highlighting
                code_html = (
                    '<details class="code">'
                    '<summary>View code</summary>'
                    '<pre><code class="language-python">'
                    f'{code}'
                    '</code></pre>'
                    '</details>'
                )
                # Combine thinking, explanation, and code accordion
                assistant_msg = f"{thinking_html}{explanation_html}\n\n{code_html}"

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_msg,
                    "plot_index": plot_idx
                })
                st.rerun()

if __name__ == "__main__":
    main() 