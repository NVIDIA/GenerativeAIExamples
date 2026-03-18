# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""
Simulator Agent Query Decomposition Script

This script decomposes user queries into tool execution plans based on the
TOOL_DECISION_TREE.md logic. It integrates the system_prompt from config.yaml
and routes queries according to the hierarchical decision tree structure.
"""

from llm_provider import ChatOpenAI
import os
import json
import re
import yaml
from string import Template
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict, Any, Optional, Union
from simulator_agent.skill_loader import SkillLoader, load_skills

# Tool to Skill Mapping
# Based on SKILL.md files from each skill folder
TOOL_TO_SKILL_MAP = {
    # RAG Skill
    "simulator_manual": "rag_skill",
    "simulator_examples": "rag_skill",
    
    # Data File Skill
    "parse_simulation_input_file": "input_file_skill",
    "modify_simulation_input_file": "input_file_skill",
    "patch_simulation_input_keyword": "input_file_skill",
    
    # Simulation Skill
    "run_and_heal": "simulation_skill",
    "monitor_simulation": "simulation_skill",
    "stop_simulation": "simulation_skill",
    
    # Plot Skill
    "plot_summary_metric": "plot_skill",
    "plot_compare_summary_metric": "plot_skill",
    
    # Results Skill
    "read_simulation_summary": "results_skill",
    "read_grid_properties": "results_skill",
    "run_flow_diagnostics": "results_skill",
    
    # Special/HITL tools (no skill)
    "hitl_confirm_run": None,
    "hitl_apply_fix": None,
    "hitl_confirm_modify": None,
    "hitl_confirm_plot": None,
    "final_response": None,
    "none": None,
}


def get_skill_name(tool_name: str) -> Optional[str]:
    """Get the skill name for a given tool."""
    return TOOL_TO_SKILL_MAP.get(tool_name)


# Sliding window: keep this many complete turns (user + assistant pairs) from conversation history
_CONV_HISTORY_MAX_TURNS = 3


def _trim_conversation_history(history: List[Dict[str, Any]], max_turns: int = _CONV_HISTORY_MAX_TURNS) -> List[Dict[str, Any]]:
    """Keep the last `max_turns` complete turns from conversation_history.
    One turn consists of a user message + an assistant/tool response (2 entries).
    Older turns are dropped so the LLM context stays focused on recent interactions.
    """
    if not history:
        return []
    max_msgs = max_turns * 2
    if len(history) <= max_msgs:
        return list(history)
    return list(history[-max_msgs:])


def _format_skills_description(skill_loader: SkillLoader, user_groups: Optional[List[str]] = None) -> str:
    """
    Format skills from SkillLoader into a readable description for the prompt.
    
    Similar to the reference implementation, this lists only skill names and descriptions,
    not individual tools. The LLM will use skill names in the decomposition output.
    
    Args:
        skill_loader: SkillLoader instance
        user_groups: Optional user groups for access control
    
    Returns:
        Formatted string describing available skills (skill names and descriptions only)
    """
    skills = skill_loader.list_skills(user_groups)
    
    if not skills:
        return "No skills available."
    
    skill_descriptions = []

    for skill in sorted(skills, key=lambda s: s.name):
        skill_desc = skill.description or f"Skill: {skill.name}"
        skill_descriptions.append(f"- {skill.name}: {skill_desc}")
    
    # Add special skills that don't have directories
    skill_descriptions.append("- final_response: For directly responding to the user (used as the final step)")
    skill_descriptions.append("- none: Use when query cannot be fulfilled with available skills")
    
    return "\n".join(skill_descriptions)


def post_process_decomposition(result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Post-process decomposition result to ensure skill_name is set correctly
    for each step based on tool_name.
    
    Args:
        result: The decomposition result from LLM
        
    Returns:
        Post-processed result with skill_name set for each step
    """
    if not result or len(result) == 0:
        return result
    
    # Process each decomposition in the result list
    for decomp in result:
        if "output_steps" not in decomp:
            continue
        
        # Process each step
        for step in decomp.get("output_steps", []):
            tool_name = step.get("tool_name")
            
            # If skill_name is missing or None, set it based on tool_name
            if "skill_name" not in step or step.get("skill_name") is None:
                step["skill_name"] = get_skill_name(tool_name) if tool_name else None
            
            # If sub_query is missing, generate a basic one from tool_name and rationale
            if "sub_query" not in step or not step.get("sub_query"):
                rationale = step.get("rationale", "")
                step["sub_query"] = f"Execute {tool_name}: {rationale}" if tool_name else rationale
    
    return result

# Get API key from environment
api_key = os.environ.get("NVIDIA_API_KEY")
if not api_key:
    raise ValueError("NVIDIA_API_KEY environment variable not set")


def _load_query_decomposition_llm() -> ChatOpenAI:
    """Load LLM for query decomposition from config.yaml, with fallback to default model."""
    default_model = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    env_config = os.environ.get("CONFIG_PATH", "").strip()
    config_path = Path(env_config) if env_config else None
    if not config_path or not config_path.exists():
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        llm_cfg = config.get("llm", {})
        model = llm_cfg.get("model_name", default_model)
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=llm_cfg.get("temperature", 0.3),
            top_p=llm_cfg.get("top_p", 0.95),
            max_tokens=llm_cfg.get("max_tokens", 36000),
        )
    return ChatOpenAI(
        model=default_model,
        api_key=api_key,
        temperature=0.3,
        max_completion_tokens=36000,
    )


llm = _load_query_decomposition_llm()

# Query decomposition prompt
QUERY_DECOMPOSITION_PROMPT = """<System>

CRITICAL: You are a JSON-ONLY Query Decomposition Agent for reservoir simulation. You MUST output ONLY valid JSON - no text, no explanations, no greetings.

Your role: Analyze user queries and output a JSON plan for which tools to use, following the TOOL_DECISION_TREE logic.

IMPORTANT RULES:
1. OUTPUT FORMAT: You MUST respond with ONLY a JSON array. No text before or after.
2. DO NOT answer the user's question. DO NOT generate a response. ONLY output a tool plan.
3. If you output anything other than JSON, the system will fail.
4. Follow the TOOL_DECISION_TREE routing logic strictly (Section 1 → 2/3/4/5 → 2.1, 2.2, etc.)

</System>

<Available Skills>

{available_skills_desc}

IMPORTANT: These are the ONLY skills available. You CANNOT use any other skills not listed here.
If a query requires capabilities beyond these skills, you MUST use the "none" skill.

</Available Skills>

<TOOL_DECISION_TREE_LOGIC>

## 1. High-level flow
- First message (no ToolMessage in history) → Section 2 routing
- Follow-up (has ToolMessage in history) → Section 3 routing

## 2. First message routing (Section 2)

### 2.0 Spatial visualization → suggest GUI (no tool in catalog)
**Condition:** User asks to visualize spatial results: grid structure (dimensions, geometry, cell count), static properties (permeability, porosity, pore volume), or dynamic fields (pressure, saturation). Simulations may be 1D, 2D, or 3D.
**Tool:** final_response only (with GUI suggestion message). No spatial visualization tools exist in the catalog.
**Examples:** "What is the grid structure?", "Show me the permeability map", "Visualize porosity distribution", "Plot pressure distribution", "Show me the saturation map"

### 2.1 HITL: confirm run
**Condition:** Previous AI message had pending_confirm_run AND user's message is a direct response (yes/no/run/cancel).
- If user **confirms** ("yes", "run", "go ahead", "sure", or equivalent): call run_and_heal.
- If user **declines** ("no", "not yet", "cancel", "skip", "don't run", or equivalent): call final_response only (acknowledge; do NOT call run_and_heal).
- If user asks a **different question** (e.g. "Help me understand why breakthrough at P3 in FILE.DATA"): do NOT use 2.1; route to the matching section (e.g. 2.5b for flow diagnostics).
**Tools:** run_and_heal (confirm) OR final_response only (decline)
**Examples:** "yes" / "run" → run_and_heal; "no" / "not yet" / "cancel" → final_response only

### 2.2 HITL: apply fix
**Condition:** Previous AI message had pending_auto_fix and user says "yes" or "apply fix".
**Tools:** patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal
**Examples:** "yes" (after fix suggestion), "apply fix"

### 2.3 Direct run (no modification)
**Condition:** User message contains DATA file path + run intent (e.g. "run", "execute", "simulate") and NO modification intent.
**Tool chain:** run_and_heal (no confirmation — user already asked to run). confirm_before_run does NOT apply to direct run; it applies only to scenario test (2.4).
**Examples:** 
- "Run data/knowledge_base/examples/spe1/SPE1CASE1.DATA" → run_and_heal
- "Execute the simulation for data/knowledge_base/examples/spe1/SPE1CASE1.DATA" → run_and_heal

### 2.4 Scenario test (modify then run)
**Condition:** User message contains DATA file path AND modification intent (e.g. "increase injection", "change rate", "test a scenario with...").
**Tool chain:** 
- Base chain: parse_simulation_input_file → simulator_manual (inferred keyword) → simulator_examples (same keyword) → modify_simulation_input_file → run_and_heal
- If confirm_before_modify is true: insert hitl_confirm_modify before modify_simulation_input_file (wait for user "yes"/"apply")
- If confirm_before_run is true: insert hitl_confirm_run before run_and_heal (wait for user "yes"/"run")
**Examples:** 
- "Test a scenario with increased gas injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA" (no HITL) → parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal
- "Test a scenario with increased gas injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA" (confirm_before_modify=true) → parse_simulation_input_file → simulator_manual → simulator_examples → hitl_confirm_modify → (wait) → modify_simulation_input_file → run_and_heal
- "Test a scenario with increased gas injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA" (confirm_before_run=true) → parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → hitl_confirm_run → (wait) → run_and_heal
- "Test a scenario with increased gas injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA" (both confirms=true) → parse_simulation_input_file → simulator_manual → simulator_examples → hitl_confirm_modify → modify_simulation_input_file → hitl_confirm_run → run_and_heal

### 2.5 Keyword/documentation question
**Condition:** LLM identifies primary keywords from query (e.g. COMPDAT, WELSPECS) and user is NOT in scenario-test mode.
**Tool chain:** simulator_manual → (simulator_examples if manual lacks format) → final_response
**Examples:** "What is the COMPDAT keyword format?", "How do I define well connections?", "Explain WELSPECS syntax"

### 2.5a Compare or plot with uploaded results
**Condition:** User asks to plot or compare summary metrics AND has uploaded files (e.g. .SMSPEC or .DATA files with results). Use when user wants to compare existing simulation results without running simulations first.
**Tool chain:** plot_compare_summary_metric (when comparing 2+ cases) or plot_summary_metric (single case) → final_response
**Examples:**
- "Compare field cumulative oil production" (with uploaded .SMSPEC or .DATA files) → plot_compare_summary_metric → final_response
- "Plot FOPT" (with uploaded .SMSPEC or single .DATA) → plot_summary_metric → final_response

### 2.5b Flow diagnostics / "why" questions
**Condition:** User asks "why" about flow behavior, e.g. early water breakthrough, injector-producer connectivity, flow paths, sweep efficiency. User provides a case path (e.g. FILE.DATA) or has uploaded results.
**Tool chain:** run_flow_diagnostics → final_response. The graph will ask for confirmation and time step(s) before running (default: last step only).
**CRITICAL:** Do NOT refuse with "no simulation has been run" or "simulation must first be executed" when the user provides a case path. The simulation may have been run before this session. Use run_flow_diagnostics — the tool will validate if output files exist and return a clear error if not.
**Examples:**
- "Why am I seeing early water breakthrough at well P3 in data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA?" → run_flow_diagnostics → final_response
- "Which injectors are connected to producer P1?" (with case in context) → run_flow_diagnostics → final_response
- "Explain the flow paths in this case" → run_flow_diagnostics → final_response

### 2.6 Fallback (LLM tool choice)
**Condition:** None of the above. Use appropriate tool from catalog.
**Examples:** "Parse data/knowledge_base/examples/spe1/SPE1CASE1.DATA and list sections" → parse_simulation_input_file

## 3. Follow-up routing (Section 3)

### 3.1 Plot or compare results
**Condition:** User asks to plot or compare AND prior run_and_heal exists.
**Tool chain:**
- plot_summary_metric or plot_compare_summary_metric → final_response (no confirmation; user already asked to plot)
**Examples:**
- "Plot the results" (no metric specified) → final_response only: ask user "Which metrics do you want to plot? (e.g., field cumulative oil production (FOPT), field oil production rate (FOPR))". Do not assume a default metric.
- "Plot field cumulative oil production" → plot_summary_metric (FOPT) → final_response
- "Compare those two cases" → plot_compare_summary_metric → final_response

### 3.2 Scenario test chain (continued)
**Condition:** Last tool in scenario chain, continue automatically.
- last_tool = parse_simulation_input_file → simulator_manual
- last_tool = simulator_manual → simulator_examples
- last_tool = simulator_examples → (hitl_confirm_modify if confirm_before_modify=true, wait for "yes"/"apply") → modify_simulation_input_file
- last_tool = modify_simulation_input_file → (hitl_confirm_run if confirm_before_run=true, wait for "yes"/"run") → run_and_heal
**HITL Notes:**
- If confirm_before_modify is true and last_tool = simulator_examples: call hitl_confirm_modify, wait for user confirmation before modify_simulation_input_file
- If confirm_before_run is true and last_tool = modify_simulation_input_file: call hitl_confirm_run, wait for user confirmation before run_and_heal

### 3.3 After run_and_heal
**Condition:** Last message is ToolMessage from run_and_heal.
**Behavior:** Auto-fix is built into run_and_heal (run + monitor + heal chain). On completion → final_response (summarize result).

### 3.3b After flow diagnostics failure — user confirms run
**Condition:** Last tool was run_flow_diagnostics, tool output indicates failure (Error, flux, RPTRST, re-run, "Surface fluxes"), and user confirms (yes, run, run the simulation, run it).
**Tool chain:** run_and_heal → final_response. Use the case_path from the prior run_flow_diagnostics tool call.
**Examples:** "yes" / "run it" / "yes run the simulation" (after assistant offered to run) → run_and_heal with that case_path → final_response

### 3.4 Keyword chain (after simulator_manual/simulator_examples)
**Condition:** Last tool is simulator_manual or simulator_examples and user asked keyword question.
**Behavior:** (if needed) simulator_examples → final_response (synthesize answer)

### 3.5 Fallback (LLM tool choice)
**Condition:** Has ToolMessage but no special case.
**Behavior:** Use appropriate tool from catalog → final_response

</TOOL_DECISION_TREE_LOGIC>

<Instructions>

0. FIRST - Determine Conversation State:
   - Check if conversation_history contains ToolMessage (has_tool_output = true/false)
   - If has_tool_output = false → Use Section 2 routing (First message)
   - If has_tool_output = true → Use Section 3 routing (Follow-up)

1. For First Message (Section 2):
   - Check conditions in order: 2.0 → 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.5a → 2.5b → 2.6
   - Apply the first matching condition
   - Build tool chain according to the matched section

2. For Follow-up (Section 3):
   - Check last_tool_name from conversation_history
   - Check conditions in order: 3.1 → 3.2 → 3.3 → 3.3b → 3.4 → 3.5
   - Apply the first matching condition
   - Build tool chain according to the matched section

3. Tool Chain Rules:
   - Each step must use EXACTLY ONE tool
   - Order steps logically based on dependencies
   - CRITICAL: "final_response" should ONLY appear as the VERY LAST STEP
   - NEVER use "final_response" in intermediate steps
   - For multi-step chains, always end with final_response (except when tool result can be directly returned)
   - For each step, classify by skill_name and provide sub_query with files and arguments

4. HITL Tools (Human-in-the-Loop):
   - hitl_confirm_run: Use when confirm_before_run is true, before run_and_heal in scenario test (Section 2.4 only; not for direct run 2.3). Waits for user "yes" or "run" confirmation.
   - hitl_confirm_modify: Use when confirm_before_modify is true, before modify_simulation_input_file in scenario test chains. Waits for user "yes" or "apply" confirmation.
   - hitl_apply_fix: Use when auto-fix is suggested and user confirms (Section 2.2)
   - These are treated as tool steps in the chain and should appear as separate steps before the action they confirm

5. Special Cases:
   - Spatial visualization requests (grid, permeability, porosity, pressure, saturation, etc.) → final_response only (no tools in catalog; GUI suggestion)
   - Direct run with no modification → run_and_heal (no confirm; confirm_before_run applies only to scenario test)
   - Scenario test → parse_simulation_input_file → simulator_manual → simulator_examples → (hitl_confirm_modify if confirm_before_modify=true) → modify_simulation_input_file → (hitl_confirm_run if confirm_before_run=true) → run_and_heal → final_response
   - Plot/compare results → plot_summary_metric or plot_compare_summary_metric → final_response (no confirmation before plot)
   - Keyword questions → simulator_manual → (simulator_examples) → final_response
   - "Why" questions (breakthrough, connectivity, flow paths) with case path → run_flow_diagnostics → final_response. Do NOT refuse with "no simulation run" — use the tool; it validates files.
   - When flow diagnostics fails due to missing results (flux, RPTRST, re-run), ask user if they want to run the simulation first. If user confirms (yes/run) in next turn → run_and_heal (Section 3.3b).
   - Section 2.1 applies ONLY when user responds yes/no to a pending run confirm. If user asks a new question (e.g. flow diagnostics with case path), use 2.5b, not 2.1.

</Instructions>

<Output Format>

You MUST respond with ONLY valid JSON as a LIST containing ONE object in the following format:

[
  {{
    "multi_steps": true/false,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "tool_name_here",
        "skill_name": "skill_name_here",
        "sub_query": "sub_query_with_files_and_arguments",
        "rationale": "clear explanation of why this tool is used for this step, referencing the decision tree section"
      }}
    ]
  }}
]

CRITICAL: For each step, you MUST include:
1. "skill_name": The name of the skill that contains this tool. Must be one of:
   - "rag_skill" (for simulator_manual, simulator_examples)
   - "input_file_skill" (for parse_simulation_input_file, modify_simulation_input_file, patch_simulation_input_keyword)
   - "simulation_skill" (for run_and_heal, monitor_simulation, stop_simulation)
   - "plot_skill" (for plot_summary_metric, plot_compare_summary_metric)
   - "results_skill" (for read_simulation_summary, read_grid_properties, run_flow_diagnostics)
   - null (for hitl_confirm_run, hitl_confirm_modify, hitl_confirm_plot, hitl_apply_fix, final_response, none)

2. "sub_query": A natural language sub-query that includes:
   - All necessary file paths (extracted from user query or conversation history)
   - All necessary arguments/parameters needed to activate the skill
   - Context about what needs to be done in this step
   
   Examples of good sub_queries:
   - For parse_simulation_input_file: "Parse the DATA file at data/knowledge_base/examples/spe1/SPE1CASE1.DATA and list all sections"
   - For simulator_manual: "Retrieve documentation for the WCONINJE keyword format and syntax"
   - For modify_simulation_input_file: "Modify data/knowledge_base/examples/spe1/SPE1CASE1.DATA: increase water injection rate for well I1 in WCONINJE to 55, output to data/knowledge_base/examples/spe1/SPE1CASE1_AGENT_GENERATED.DATA"
   - For run_and_heal: "Run simulation on the modified file (output from modify step) with background=False"
   - For plot_summary_metric: "Plot FOPT metric from output directory /path/to/output"
   - For read_simulation_summary: "Read FOPR and FOPT variables from case data/knowledge_base/examples/spe1/SPE1CASE1.DATA"
   - For run_flow_diagnostics: "Run flow diagnostics on data/knowledge_base/examples/spe1/SPE1CASE1.DATA for time steps 1 and 2"

</Output Format>

<Examples>

Example 1 - Section 2.0: Spatial visualization request
User: "What is the grid structure?"
Conversation: [] (no tool output)
Response:
[
  {{
    "multi_steps": false,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Respond to user that spatial visualization (grid, permeability, porosity, pore volume, pressure, saturation, etc.) requires GUI tools like ResInsight, as this capability is not available in the current toolset",
        "rationale": "User asks for spatial visualization. Section 2.0: no spatial visualization tools in catalog; return final_response with GUI suggestion."
      }}
    ]
  }}
]

Example 2 - Section 2.1: HITL confirm run (user confirms)
User: "yes"
Conversation: [{"role": "assistant", "content": "Run the simulation? Reply yes or run to start.", "pending_confirm_run": true, "pending_data_file": "data/knowledge_base/examples/spe1/SPE1CASE1.DATA"}]
Response:
[
  {{
    "multi_steps": false,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "run_and_heal",
        "skill_name": "simulation_skill",
        "sub_query": "Run simulation on data/knowledge_base/examples/spe1/SPE1CASE1.DATA with background=False (foreground mode to wait for completion)",
        "rationale": "User confirmed run after pending_confirm_run prompt. According to Section 2.1, call run_and_heal with data_file from pending context."
      }}
    ]
  }}
]

Example 2b - Section 2.1: HITL confirm run (user declines)
User: "not yet"
Conversation: [{"role": "assistant", "content": "Run the simulation? Reply yes or run to start.", "pending_confirm_run": true, "pending_data_file": "data/knowledge_base/examples/spe1/SPE1CASE1.DATA"}]
Response:
[
  {{
    "multi_steps": false,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Acknowledge that the user declined to run; do not start the simulation.",
        "rationale": "User declined run after pending_confirm_run prompt (e.g. no, not yet, cancel). According to Section 2.1, do NOT call run_and_heal; use final_response only."
      }}
    ]
  }}
]

Example 3 - Section 2.3: Direct run
User: "Run the simulation: data/knowledge_base/examples/spe1/SPE1CASE1.DATA"
Conversation: [] (no tool output)
Response:
[
  {{
    "multi_steps": false,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "run_and_heal",
        "skill_name": "simulation_skill",
        "sub_query": "Run simulation on data/knowledge_base/examples/spe1/SPE1CASE1.DATA with background=True (default background mode)",
        "rationale": "User message contains DATA file path and run intent with no modification intent. Section 2.3: direct run — call run_and_heal directly (no confirmation; confirm_before_run does not apply to direct run)."
      }}
    ]
  }}
]

Example 4 - Section 2.4: Scenario test (no HITL)
User: "Test a scenario with increased injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA"
Conversation: [] (no tool output)
confirm_before_modify: false, confirm_before_run: false
Response:
[
  {{
    "multi_steps": true,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "parse_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Parse data/knowledge_base/examples/spe1/SPE1CASE1.DATA to understand file structure and identify sections, especially WCONINJE keyword for injection rate modification",
        "rationale": "Scenario test requires file context first. According to Section 2.4, start with parse_simulation_input_file to understand file structure."
      }},
      {{
        "step_nr": 2,
        "tool_name": "simulator_manual",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve documentation for WCONINJE keyword format, syntax, and parameters to understand how to modify injection rates",
        "rationale": "Need to look up keyword documentation (e.g., WCONINJE) for injection rate modification. According to Section 2.4, call simulator_manual with inferred keyword."
      }},
      {{
        "step_nr": 3,
        "tool_name": "simulator_examples",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve example DATA files showing WCONINJE keyword usage with injection rate specifications",
        "rationale": "Need working examples of the keyword. According to Section 2.4, call simulator_examples with same keyword."
      }},
      {{
        "step_nr": 4,
        "tool_name": "modify_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Modify data/knowledge_base/examples/spe1/SPE1CASE1.DATA: increase water injection rate in WCONINJE keyword, output to new scenario file in same directory",
        "rationale": "Apply the modification with manual and example context. According to Section 2.4, call modify_simulation_input_file to create scenario file (_AGENT_GENERATED.DATA)."
      }},
      {{
        "step_nr": 5,
        "tool_name": "run_and_heal",
        "skill_name": "simulation_skill",
        "sub_query": "Run simulation on the modified scenario file (output from previous step) with background=False to wait for completion and check results",
        "rationale": "Run the modified scenario file. According to Section 2.4, call run_and_heal on the generated file."
      }},
      {{
        "step_nr": 6,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Summarize the scenario test: confirm modification applied, report simulation result (success/failure), and provide key metrics if available",
        "rationale": "Summarize the scenario test results. According to Section 2.4, end with final_response."
      }}
    ]
  }}
]

Example 4a - Section 2.4: Scenario test (with hitl_confirm_modify)
User: "Test a scenario with increased injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA"
Conversation: [] (no tool output)
confirm_before_modify: true, confirm_before_run: false
Response:
[
  {{
    "multi_steps": true,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "parse_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Parse data/knowledge_base/examples/spe1/SPE1CASE1.DATA to understand file structure and identify sections, especially WCONINJE keyword for injection rate modification",
        "rationale": "Scenario test requires file context first. According to Section 2.4, start with parse_simulation_input_file."
      }},
      {{
        "step_nr": 2,
        "tool_name": "simulator_manual",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve documentation for WCONINJE keyword format, syntax, and parameters to understand how to modify injection rates",
        "rationale": "Need to look up keyword documentation. According to Section 2.4, call simulator_manual with inferred keyword."
      }},
      {{
        "step_nr": 3,
        "tool_name": "simulator_examples",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve example DATA files showing WCONINJE keyword usage with injection rate specifications",
        "rationale": "Need working examples. According to Section 2.4, call simulator_examples with same keyword."
      }},
      {{
        "step_nr": 4,
        "tool_name": "hitl_confirm_modify",
        "skill_name": null,
        "sub_query": "Request user confirmation before modifying data/knowledge_base/examples/spe1/SPE1CASE1.DATA: increase water injection rate in WCONINJE keyword. Wait for user to reply 'yes' or 'apply'.",
        "rationale": "According to Section 2.4, since confirm_before_modify=true, call hitl_confirm_modify before modify_simulation_input_file to get user confirmation."
      }},
      {{
        "step_nr": 5,
        "tool_name": "modify_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Modify data/knowledge_base/examples/spe1/SPE1CASE1.DATA: increase water injection rate in WCONINJE keyword, output to new scenario file (after user confirms)",
        "rationale": "After user confirms via hitl_confirm_modify, apply the modification. According to Section 2.4, call modify_simulation_input_file to create scenario file."
      }},
      {{
        "step_nr": 6,
        "tool_name": "run_and_heal",
        "skill_name": "simulation_skill",
        "sub_query": "Run simulation on the modified scenario file with background=False",
        "rationale": "Run the modified scenario file. According to Section 2.4, call run_and_heal on the generated file."
      }},
      {{
        "step_nr": 7,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Summarize the scenario test: confirm modification applied, report simulation result (success/failure), and provide key metrics if available",
        "rationale": "Summarize the scenario test results. According to Section 2.4, end with final_response."
      }}
    ]
  }}
]

Example 4b - Section 2.4: Scenario test (with both HITL confirms)
User: "Test a scenario with increased gas injection rate in data/knowledge_base/examples/spe1/SPE1CASE1.DATA"
Conversation: [] (no tool output)
confirm_before_modify: true, confirm_before_run: true
Response:
[
  {{
    "multi_steps": true,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "parse_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Parse data/knowledge_base/examples/spe1/SPE1CASE1.DATA to understand file structure and identify sections, especially WCONINJE keyword for injection rate modification",
        "rationale": "Scenario test requires file context first. According to Section 2.4, start with parse_simulation_input_file."
      }},
      {{
        "step_nr": 2,
        "tool_name": "simulator_manual",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve documentation for WCONINJE keyword format, syntax, and parameters to understand how to modify injection rates",
        "rationale": "Need to look up keyword documentation. According to Section 2.4, call simulator_manual with inferred keyword."
      }},
      {{
        "step_nr": 3,
        "tool_name": "simulator_examples",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve example DATA files showing WCONINJE keyword usage with injection rate specifications",
        "rationale": "Need working examples. According to Section 2.4, call simulator_examples with same keyword."
      }},
      {{
        "step_nr": 4,
        "tool_name": "hitl_confirm_modify",
        "skill_name": null,
        "sub_query": "Request user confirmation before modifying data/knowledge_base/examples/spe1/SPE1CASE1.DATA: increase water injection rate in WCONINJE keyword. Wait for user to reply 'yes' or 'apply'.",
        "rationale": "According to Section 2.4, since confirm_before_modify=true, call hitl_confirm_modify before modify_simulation_input_file."
      }},
      {{
        "step_nr": 5,
        "tool_name": "modify_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Modify data/knowledge_base/examples/spe1/SPE1CASE1.DATA: increase water injection rate in WCONINJE keyword, output to new scenario file (after user confirms)",
        "rationale": "After user confirms via hitl_confirm_modify, apply the modification. According to Section 2.4, call modify_simulation_input_file."
      }},
      {{
        "step_nr": 6,
        "tool_name": "hitl_confirm_run",
        "skill_name": null,
        "sub_query": "Request user confirmation before running simulation on the modified scenario file. Wait for user to reply 'yes' or 'run'.",
        "rationale": "According to Section 2.4, since confirm_before_run=true, call hitl_confirm_run before run_and_heal."
      }},
      {{
        "step_nr": 7,
        "tool_name": "run_and_heal",
        "skill_name": "simulation_skill",
        "sub_query": "Run simulation on the modified scenario file with background=False (after user confirms)",
        "rationale": "After user confirms via hitl_confirm_run, run the modified scenario file. According to Section 2.4, call run_and_heal."
      }},
      {{
        "step_nr": 8,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Summarize the scenario test: confirm modification applied, report simulation result (success/failure), and provide key metrics if available",
        "rationale": "Summarize the scenario test results. According to Section 2.4, end with final_response."
      }}
    ]
  }}
]

Example 5 - Section 2.5: Keyword question
User: "What is the COMPDAT keyword format?"
Conversation: [] (no tool output)
Response:
[
  {{
    "multi_steps": true,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "simulator_manual",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve documentation for COMPDAT keyword format, syntax, field definitions, and parameter tables from simulator manual",
        "rationale": "User asks for keyword format. According to Section 2.5, start with simulator_manual for authoritative documentation."
      }},
      {{
        "step_nr": 2,
        "tool_name": "simulator_examples",
        "skill_name": "rag_skill",
        "sub_query": "Retrieve example DATA files showing COMPDAT keyword usage with concrete syntax examples",
        "rationale": "May need examples to illustrate format. According to Section 2.5, optionally call simulator_examples if manual lacks format details."
      }},
      {{
        "step_nr": 3,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Synthesize COMPDAT keyword format from manual and examples: provide title, purpose, general format with code block, field-by-field list, and source citation",
        "rationale": "Synthesize format, fields, and examples into final answer. According to Section 2.5, end with final_response."
      }}
    ]
  }}
]

Example 6 - Section 3.1: Plot results (user did not specify which metric)
User: "Plot the results"
Conversation: [{"role": "tool", "tool_name": "run_and_heal", "output": "Simulation completed successfully", "output_dir": "/path/to/output"}]
Response:
[
  {{
    "multi_steps": false,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Ask the user: Which metrics do you want to plot? (e.g., field cumulative oil production (FOPT), field oil production rate (FOPR), well cumulative oil (WOPT)). Do not assume a default; wait for the user to specify.",
        "rationale": "User asked to plot results but did not specify a metric. According to Section 3.1, do not default to FOPT; ask the user which metric(s) to plot."
      }}
    ]
  }}
]

Example 7 - Section 2.6: Fallback (parse file)
User: "Parse data/knowledge_base/examples/spe1/SPE1CASE1.DATA and list sections"
Conversation: [] (no tool output)
Response:
[
  {{
    "multi_steps": true,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "parse_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Parse data/knowledge_base/examples/spe1/SPE1CASE1.DATA file and extract all sections (RUNSPEC, GRID, PROPS, SOLUTION, SUMMARY, SCHEDULE, etc.)",
        "rationale": "User explicitly asks to parse file. According to Section 2.6 fallback, use appropriate tool from catalog."
      }},
      {{
        "step_nr": 2,
        "tool_name": "final_response",
        "skill_name": null,
        "sub_query": "Present the list of sections found in data/knowledge_base/examples/spe1/SPE1CASE1.DATA to the user",
        "rationale": "Present parsed file structure to user. According to Section 2.6, end with final_response."
      }}
    ]
  }}
]

Example 8 - Section 3.2: Scenario test chain continued (with HITL)
User: (no new query, automatic follow-up)
Conversation: [{"role": "tool", "tool_name": "simulator_examples", "output": "Examples retrieved", "keyword": "WCONINJE"}]
last_tool_name: "simulator_examples"
confirm_before_modify: true, confirm_before_run: true
Response:
[
  {{
    "multi_steps": true,
    "output_steps": [
      {{
        "step_nr": 1,
        "tool_name": "hitl_confirm_modify",
        "skill_name": null,
        "sub_query": "Request user confirmation before modifying DATA file based on WCONINJE keyword examples. Wait for user to reply 'yes' or 'apply'.",
        "rationale": "Last tool was simulator_examples in scenario test chain. According to Section 3.2, since confirm_before_modify=true, call hitl_confirm_modify before modify_simulation_input_file."
      }},
      {{
        "step_nr": 2,
        "tool_name": "modify_simulation_input_file",
        "skill_name": "input_file_skill",
        "sub_query": "Modify DATA file using WCONINJE keyword context from simulator_manual and simulator_examples, output to new scenario file (after user confirms)",
        "rationale": "After user confirms via hitl_confirm_modify, continue scenario test chain. According to Section 3.2, call modify_simulation_input_file with manual and example context."
      }},
      {{
        "step_nr": 3,
        "tool_name": "hitl_confirm_run",
        "skill_name": null,
        "sub_query": "Request user confirmation before running simulation on the modified scenario file. Wait for user to reply 'yes' or 'run'.",
        "rationale": "After modify_simulation_input_file completes, according to Section 3.2, since confirm_before_run=true, call hitl_confirm_run before run_and_heal."
      }},
      {{
        "step_nr": 4,
        "tool_name": "run_and_heal",
        "skill_name": "simulation_skill",
        "sub_query": "Run simulation on the modified scenario file with background=False (after user confirms)",
        "rationale": "After user confirms via hitl_confirm_run, complete scenario test chain. According to Section 3.2, call run_and_heal on the generated file."
      }}
    ]
  }}
]

</Examples>

<Constraints>

ABSOLUTELY CRITICAL - JSON OUTPUT ONLY:
- Your response MUST start with [ and end with ]
- Your response MUST be valid JSON - nothing else
- DO NOT write any text, greetings, or explanations
- DO NOT answer the user's question - only output the plan
- If you output ANYTHING other than JSON, the system will BREAK

JSON FORMAT RULES:
- Response must be a JSON array wrapped in [ ]
- Each step must have exactly ONE tool
- Always include "step_nr" starting from 1
- Always include "skill_name" - the name of the skill containing this tool (or null for special tools)
- Always include "sub_query" - a natural language query with file paths and arguments needed to activate the skill
- Always include "rationale" explaining why this tool is chosen, referencing the decision tree section
- Make each step atomic

CRITICAL RULES FOR "none" TOOL:
- NEVER invent, hallucinate, or use tools that are not explicitly listed
- If the query requires ANY capability not available, use "none" as tool_name
- When using "none", set "multi_steps" to false
- Provide detailed rationale explaining what capabilities are missing

CRITICAL RULES FOR "final_response":
- For multi_steps=true: "final_response" MUST ONLY be the LAST step
- NEVER use "final_response" in intermediate steps
- "final_response" is ONLY for delivering the final answer after ALL processing
- Exception: Section 2.0 (spatial visualization) uses final_response as single step for GUI suggestion (no spatial visualization tools in catalog)

</Constraints>

<Current_Context_Info>

- Conversation history: {conversation_history}
- Last tool name (if any): {last_tool_name}
- Has tool output: {has_tool_output}
- Pending confirm run: {pending_confirm_run}
- Pending auto fix: {pending_auto_fix}
- Confirm before run setting: {confirm_before_run}
- Confirm before modify setting: {confirm_before_modify}
- Uploaded files (absolute paths from UI): {uploaded_files}

When the user has uploaded one or more files, treat them as available. For Section 2.3 (direct run): if the user says "run the simulation" (or similar run intent) and has uploaded a file with extension .DATA, route to run_and_heal — the DATA file path is the uploaded file. Do NOT use final_response with "cannot run without DATA file" when a .DATA file is in the uploaded list. For Section 2.5a (compare with uploaded results): if the user asks to "compare" or "plot" summary metrics and has uploaded .SMSPEC or .DATA files, route to plot_compare_summary_metric or plot_summary_metric — do NOT use final_response with "no simulation results" when uploaded files include results. For Section 2.5b (flow diagnostics): if the user asks about breakthrough, connectivity, flow paths, etc. and provides a case path (e.g. in the query or uploaded), route to run_flow_diagnostics — do NOT use final_response with "no simulation has been run" or "simulation must first be executed"; the simulation may have been run before this session.

### User Query
{user_input}
</Current_Context_Info>"""


def _strip_think_tags(text: str) -> str:
    """Remove thinking-model tags (think/open/close) so only the actual response remains."""
    if not text or not isinstance(text, str):
        return text
    open_tag = "<" + "think" + ">"
    close_tag = "<" + "/think" + ">"
    if open_tag in text and close_tag in text:
        start = text.find(close_tag) + len(close_tag)
        text = text[start:].lstrip()
    elif open_tag in text:
        start = text.find(open_tag)
        text = text[:start].strip()
    return text


def query_decomposition_call(
    user_input: str,
    conversation_history: List[Dict[str, Any]] = None,
    last_tool_name: Optional[str] = None,
    pending_confirm_run: bool = False,
    pending_auto_fix: bool = False,
    confirm_before_run: bool = False,
    confirm_before_modify: bool = False,
    confirm_before_plot: bool = False,
    skill_loader: Optional[SkillLoader] = None,
    skills_base_path: Optional[Union[str, Path]] = None,
    exclude_skills: Optional[List[str]] = None,
    available_skills_desc: Optional[str] = None,
    user_groups: Optional[List[str]] = None,
    uploaded_files: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Call the LLM with the query and system prompt to decompose the query into steps.
    
    Args:
        user_input: User query string
        conversation_history: List of conversation messages (dicts with role, content, tool_name, etc.)
        last_tool_name: Name of the last tool that was called (if any)
        pending_confirm_run: Whether there's a pending confirmation for running simulation
        pending_auto_fix: Whether there's a pending auto-fix confirmation
        confirm_before_run: Whether to confirm before running (from config)
        confirm_before_modify: Whether to confirm before modifying DATA files (from config)
        confirm_before_plot: Whether to confirm before plotting results (from config)
        skill_loader: Optional SkillLoader instance (if provided, used to generate skills description)
        skills_base_path: Optional path to skills directory (used if skill_loader not provided)
        exclude_skills: Optional list of skill names to exclude from discovery
        available_skills_desc: Optional manual skills description string (for backward compatibility)
        user_groups: Optional user groups for access control
        uploaded_files: Optional list of absolute file paths the user uploaded via the UI (e.g. .DATA files)
    
    Returns:
        Parsed JSON response as a list containing the decomposition dictionary
    """
    # Apply sliding window: keep only the last 3 turns so the LLM context stays focused
    conversation_history = _trim_conversation_history(conversation_history or [])

    # Determine if we have tool output in history
    has_tool_output = False
    if conversation_history:
        has_tool_output = any(
            msg.get("role") == "tool" or msg.get("tool_name") is not None
            for msg in conversation_history
        )
    
    # Generate available skills description
    if available_skills_desc:
        # Use provided manual description (backward compatibility)
        skills_description = available_skills_desc
    elif skill_loader:
        # Use provided SkillLoader
        skills_description = _format_skills_description(skill_loader, user_groups)
    elif skills_base_path:
        # Load skills from path
        skill_loader = load_skills(skills_base_path, exclude_skills=exclude_skills)
        skills_description = _format_skills_description(skill_loader, user_groups)
    else:
        # Fallback: Use default hardcoded description (backward compatibility)
        # List only skill names and descriptions, not individual tools
        skills_description = """- rag_skill: Retrieve information from simulator manual and example DATA files. Use for keyword definitions, syntax, and official references.
- input_file_skill: Parse, modify, validate, and patch simulator input files. Use when working with reservoir simulation input files, testing scenarios, or validating simulation configurations.
- simulation_skill: Run, monitor, and control simulations. Use when executing simulations, checking progress, or stopping running simulations.
- plot_skill: Plot and compare summary metrics from simulation results. Use for visualization and comparison of simulation outputs.
- results_skill: Read simulation summary results, grid properties, and analyze production performance. Use for analyzing simulation outputs and performance metrics.
- final_response: For directly responding to the user (used as the final step to wrap and deliver results, or for GUI suggestions)
- none: Use this when the query cannot be fulfilled because required tools/capabilities are not available"""
    
    # Format conversation history as string
    history_str = json.dumps(conversation_history, ensure_ascii=False) if conversation_history else "[]"
    
    # Use Template to safely replace placeholders (avoids issues with JSON braces)
    # First, convert the format() style placeholders to Template style ($variable)
    prompt_template = QUERY_DECOMPOSITION_PROMPT.replace("{conversation_history}", "$conversation_history")
    prompt_template = prompt_template.replace("{last_tool_name}", "$last_tool_name")
    prompt_template = prompt_template.replace("{has_tool_output}", "$has_tool_output")
    prompt_template = prompt_template.replace("{pending_confirm_run}", "$pending_confirm_run")
    prompt_template = prompt_template.replace("{pending_auto_fix}", "$pending_auto_fix")
    prompt_template = prompt_template.replace("{confirm_before_run}", "$confirm_before_run")
    prompt_template = prompt_template.replace("{confirm_before_modify}", "$confirm_before_modify")
    prompt_template = prompt_template.replace("{confirm_before_plot}", "$confirm_before_plot")
    prompt_template = prompt_template.replace("{user_input}", "$user_input")
    prompt_template = prompt_template.replace("{available_skills_desc}", "$available_skills_desc")
    prompt_template = prompt_template.replace("{uploaded_files}", "$uploaded_files")
    
    # Format uploaded_files for prompt (list of paths or "None")
    uploaded_files_str = json.dumps(uploaded_files or [], ensure_ascii=False) if uploaded_files else "[]"
    
    # Now use Template.safe_substitute to replace values
    template = Template(prompt_template)
    formatted_prompt = template.safe_substitute(
        conversation_history=history_str,
        last_tool_name=last_tool_name if last_tool_name else "None",
        has_tool_output=str(has_tool_output).lower(),
        pending_confirm_run=str(pending_confirm_run).lower(),
        pending_auto_fix=str(pending_auto_fix).lower(),
        confirm_before_run=str(confirm_before_run).lower(),
        confirm_before_modify=str(confirm_before_modify).lower(),
        confirm_before_plot=str(confirm_before_plot).lower(),
        user_input=user_input,
        available_skills_desc=skills_description,
        uploaded_files=uploaded_files_str
    )
    
    # Use LangChain Message objects (SystemMessage/HumanMessage)
    # ChatOpenAI from llm_provider expects Message objects
    messages = [
        SystemMessage(content=formatted_prompt),
        HumanMessage(content=user_input)
    ]
    
    try:
        response = llm.invoke(messages)
        # Extract content from response (LangChain AIMessage has .content attribute)
        raw_content = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        # Normalize double curly braces (LLM sometimes copies {{ }} from prompt examples)
        raw_content = raw_content.replace("{{", "{").replace("}}", "}")
        # Strip thinking-model tags (e.g. <think>...</think>
        raw_content = _strip_think_tags(raw_content)
        
        # Try to parse the response as JSON (should be a list)
        try:
            parsed_response = json.loads(raw_content)
            
            # Ensure it's a list
            if not isinstance(parsed_response, list):
                # If it's a dict, wrap it in a list
                parsed_response = [parsed_response]
            
            # Post-process to ensure skill_name and sub_query are set
            parsed_response = post_process_decomposition(parsed_response)
            
            return parsed_response
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response if LLM added surrounding text
            json_match = re.search(r'\[[\s\S]*\]', raw_content)
            if json_match:
                try:
                    extracted_json = json_match.group(0).replace("{{", "{").replace("}}", "}")
                    parsed_response = json.loads(extracted_json)
                    if not isinstance(parsed_response, list):
                        parsed_response = [parsed_response]
                    # Post-process to ensure skill_name and sub_query are set
                    parsed_response = post_process_decomposition(parsed_response)
                    print("[DEBUG] Extracted JSON from mixed response successfully")
                    return parsed_response
                except json.JSONDecodeError:
                    pass  # Fall through to error handling
            
            print(f"[WARNING] Error parsing query decomposition JSON response: {e}")
            print(f"Raw response: {raw_content[:500]}...")  # Truncate for logging
            
            # Fallback: Simple heuristics for fallback routing
            return _fallback_routing(user_input, has_tool_output, last_tool_name)
    
    except Exception as e:
        print(f"[ERROR] Exception in query_decomposition_call: {e}")
        return _fallback_routing(user_input, has_tool_output, last_tool_name)


def _fallback_routing(
    user_input: str,
    has_tool_output: bool,
    last_tool_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fallback routing when JSON parsing fails.
    Uses simple heuristics based on keywords.
    """
    user_lower = user_input.lower()
    
    # Spatial visualization: no tools in catalog; respond with GUI suggestion only (Section 2.0)
    spatial_viz_keywords = [
        "grid", "egrid", "pressure map", "saturation map", "permeability map", "porosity map", "pore volume",
        "cell count", "dimensions", "grid structure",
        "spatial visualization", "grid visualization"
    ]
    if any(kw in user_lower for kw in spatial_viz_keywords):
        return [{
            "multi_steps": False,
            "output_steps": [{
                "step_nr": 1,
                "tool_name": "final_response",
                "skill_name": None,
                "sub_query": "Respond to user that spatial visualization (grid, permeability, porosity, pore volume, pressure, saturation, etc.) requires GUI tools like ResInsight, as this capability is not available in the current toolset",
                "rationale": "Fallback: Detected spatial visualization request; no tools in catalog, suggest GUI (Section 2.0)"
            }]
        }]
    
    # Check for run/modification intent
    run_keywords = ["run", "execute", "simulate", "start"]
    data_file_pattern = r'\.data\b|\.DATA\b'
    has_data_file = bool(re.search(data_file_pattern, user_input, re.IGNORECASE))
    
    # Check for modification intent (scenario test)
    mod_keywords = ["modify", "change", "increase", "decrease", "test scenario", "scenario with"]
    has_modification = any(kw in user_lower for kw in mod_keywords)
    
    if has_data_file:
        # Extract data file path
        data_file_match = re.search(r'[\w/\.-]+\.DATA', user_input, re.IGNORECASE)
        data_file_path = data_file_match.group(0) if data_file_match else "DATA_FILE_PATH"
        
        if has_modification:
            # Section 2.4: Scenario test
            return [{
                "multi_steps": True,
                "output_steps": [
                    {"step_nr": 1, "tool_name": "parse_simulation_input_file", "skill_name": "input_file_skill", "sub_query": f"Parse {data_file_path} to understand file structure", "rationale": "Fallback: Scenario test - parse file first"},
                    {"step_nr": 2, "tool_name": "simulator_manual", "skill_name": "rag_skill", "sub_query": "Retrieve keyword documentation for the modification requested", "rationale": "Fallback: Look up keyword documentation"},
                    {"step_nr": 3, "tool_name": "simulator_examples", "skill_name": "rag_skill", "sub_query": "Retrieve example DATA files showing the keyword usage", "rationale": "Fallback: Get examples"},
                    {"step_nr": 4, "tool_name": "modify_simulation_input_file", "skill_name": "input_file_skill", "sub_query": f"Modify {data_file_path} according to user request, output to new scenario file", "rationale": "Fallback: Apply modification"},
                    {"step_nr": 5, "tool_name": "run_and_heal", "skill_name": "simulation_skill", "sub_query": f"Run simulation on modified file with background=False", "rationale": "Fallback: Run modified file"},
                    {"step_nr": 6, "tool_name": "final_response", "skill_name": None, "sub_query": "Summarize scenario test results", "rationale": "Fallback: Summarize results"}
                ]
            }]
        elif any(kw in user_lower for kw in run_keywords):
            # Section 2.3: Direct run
            return [{
                "multi_steps": False,
                "output_steps": [{
                    "step_nr": 1,
                    "tool_name": "run_and_heal",
                    "skill_name": "simulation_skill",
                    "sub_query": f"Run simulation on {data_file_path} with background=True",
                    "rationale": "Fallback: Direct run request (Section 2.3)"
                }]
            }]
    
    # Check for parse file intent (Section 2.6)
    parse_keywords = ["parse", "list sections", "extract sections"]
    if any(kw in user_lower for kw in parse_keywords) and has_data_file:
        data_file_match = re.search(r'[\w/\.-]+\.DATA', user_input, re.IGNORECASE)
        data_file_path = data_file_match.group(0) if data_file_match else "DATA_FILE_PATH"
        return [{
            "multi_steps": True,
            "output_steps": [
                {"step_nr": 1, "tool_name": "parse_simulation_input_file", "skill_name": "input_file_skill", "sub_query": f"Parse {data_file_path} file and extract all sections (RUNSPEC, GRID, PROPS, etc.)", "rationale": "Fallback: Parse file request (Section 2.6)"},
                {"step_nr": 2, "tool_name": "final_response", "skill_name": None, "sub_query": "Present the list of sections found to the user", "rationale": "Fallback: Present parsed file structure"}
            ]
        }]
    
    # Check for keyword questions
    keyword_patterns = ["format", "syntax", "what is", "how do", "explain", "keyword"]
    if any(kw in user_lower for kw in keyword_patterns):
        return [{
            "multi_steps": True,
            "output_steps": [
                {"step_nr": 1, "tool_name": "simulator_manual", "skill_name": "rag_skill", "sub_query": f"Retrieve documentation for keyword from user query: {user_input}", "rationale": "Fallback: Keyword question - look up manual"},
                {"step_nr": 2, "tool_name": "simulator_examples", "skill_name": "rag_skill", "sub_query": f"Retrieve example DATA files showing keyword usage from user query", "rationale": "Fallback: Get examples"},
                {"step_nr": 3, "tool_name": "final_response", "skill_name": None, "sub_query": "Synthesize keyword format, fields, and examples into final answer with source citations", "rationale": "Fallback: Synthesize answer"}
            ]
        }]
    
    # Check for plot/compare requests (Section 3.1)
    plot_keywords = ["plot", "graph", "chart", "visualize"]
    compare_keywords = ["compare", "comparison"]
    if any(kw in user_lower for kw in plot_keywords + compare_keywords) and has_tool_output:
        tool_name = "plot_compare_summary_metric" if any(kw in user_lower for kw in compare_keywords) else "plot_summary_metric"
        return [{
            "multi_steps": True,
            "output_steps": [
                {"step_nr": 1, "tool_name": tool_name, "skill_name": "plot_skill", "sub_query": f"Plot summary metrics from user request: {user_input}, using output directory from previous simulation", "rationale": "Fallback: Plot/compare request after run"},
                {"step_nr": 2, "tool_name": "final_response", "skill_name": None, "sub_query": "Present the generated plot to the user", "rationale": "Fallback: Deliver plot"}
            ]
        }]
    
    # Default fallback
    return [{
        "multi_steps": False,
        "output_steps": [{
            "step_nr": 1,
            "tool_name": "final_response",
            "skill_name": None,
            "sub_query": f"Respond to user query: {user_input}",
            "rationale": "Fallback: Unable to determine routing, use final_response"
        }]
    }]

