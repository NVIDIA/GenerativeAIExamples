---
name: input_file_skill
description: Parse, modify, validate, and patch simulator input files. Use when working with reservoir simulation input files, testing scenarios, or validating simulation configurations. This implementation supports reference format (.DATA); other simulators use different extensions (e.g., .afi, .DAT). Supports natural language modifications, keyword patching, and syntax validation.
license: Apache-2.0
metadata:
  author: sim-agent
  version: "1.0"
  category: simulator
compatibility: Requires simulator tools and Python environment with langchain, pydantic, and nvidia-ai-endpoints packages
---

# DATA File Processing Skill

This skill provides tools for working with simulator input files. The reference format uses .DATA as the primary input extension; other simulators use different extensions.

## Overview

The DATA File Processing skill enables agents to:

- **Parse** simulator input files to understand their structure and sections
- **Modify** simulator input files using natural language instructions
- **Validate** simulator input files for syntax and consistency
- **Patch** specific keyword blocks without rewriting entire files

## Tools

### parse_simulation_input_file

Parses a simulator input file and returns its structure (sections found). Reference format uses .DATA extension.

**Usage:**
```python
parse_simulation_input_file(file_path: str) -> str
```

**Example:**
```
parse_simulation_input_file("data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA")
```

**Returns:** A string listing all sections found (e.g., "Sections found: HEADER, RUNSPEC, GRID, PROPS, SOLUTION, SUMMARY, SCHEDULE")

**When to use:** First step in scenario testing chain (TOOL_DECISION_TREE.md Section 2.4) or when user asks to parse/list sections of a simulator input file.

### modify_simulation_input_file

Modifies a simulator input file based on natural language instructions. Can modify entire file or target specific keyword blocks.

**Usage:**
```python
modify_simulation_input_file(
    file_path: str,
    modifications: str,
    output_path: Optional[str] = None,
    llm_model: Optional[str] = None,
    manual_context: Optional[str] = None,
    example_context: Optional[str] = None,
    target_keyword: Optional[str] = None
) -> str
```

**Parameters:**
- `file_path`: Path to the simulator input file to modify
- `modifications`: Natural language description of changes (e.g., "Increase water injection rate for well I1 to 55")
- `output_path`: Where to save modified file (default: overwrite original)
- `llm_model`: Optional model override for LLM-based modifications
- `manual_context`: Optional simulator manual excerpt for the relevant keyword
- `example_context`: Optional example DATA snippets for the relevant keyword
- `target_keyword`: If set, only this keyword block is edited; rest of file is copied unchanged

**Example:**
```
modify_simulation_input_file(
    file_path="SPE1CASE1.DATA",
    modifications="Increase water injection rate for well I1 in WCONINJE to 55",
    output_path="SPE1CASE1_AGENT_GENERATED.DATA",
    target_keyword="WCONINJE"
)
```

**When to use:** In scenario test chain (Section 2.4) after parse_simulation_input_file → simulator_manual → simulator_examples, or when user requests modifications to a simulator input file.

### patch_simulation_input_keyword

Patches a specific keyword block in a simulator input file without modifying other parts. Useful for auto-fixes.

**Usage:**
```python
patch_simulation_input_keyword(
    file_path: str,
    keyword: str,
    output_path: str,
    item_index: Optional[int] = None,
    new_value: Optional[str] = None,
    new_block_content: Optional[str] = None
) -> str
```

**Parameters:**
- `file_path`: Path to the simulator input file
- `keyword`: Keyword to patch (e.g., WELLDIMS, TABDIMS)
- `output_path`: Path for the new file (original is unchanged)
- `item_index`: 1-based index of the numeric item to replace
- `new_value`: New value for the item (used with item_index)
- `new_block_content`: Exact new block content (keyword line + data). If set, item_index/new_value are ignored.

**Example:**
```
patch_simulation_input_keyword(
    file_path="SPE1CASE1.DATA",
    keyword="WELLDIMS",
    output_path="SPE1CASE1_FIXED.DATA",
    item_index=1,
    new_value="10"
)
```

**When to use:** In HITL apply fix flow (Section 2.2) for auto-fixes, or when only a specific keyword needs to be changed.

## Workflow Integration

This skill integrates with the Simulator Agent's decision tree (TOOL_DECISION_TREE.md):

1. **Scenario Test Chain (Section 2.4):**
   ```
   parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal
   ```

2. **HITL Apply Fix (Section 2.2):**
   ```
   patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal
   ```

## Implementation Details

Tools are implemented as LangChain tools with Pydantic input schemas. The skill uses:

- **utils.py**: Shared utility functions for parsing, keyword finding, and LLM integration
- **Tool modules**: Individual tool implementations in separate modules
- **LLM integration**: Uses ChatOpenAI for natural language modifications

## Error Handling

All tools return descriptive error messages if:
- Files are not found
- Syntax errors occur during parsing
- LLM modifications fail
- Validation checks fail

## References

- [OPM Flow Manual](references/OPM_MANUAL.md) - Detailed keyword reference
- [Tool Decision Tree](references/TOOL_DECISION_TREE.md) - Routing logic
- [Examples](references/EXAMPLES.md) - Usage examples

## Testing

Run the test suite:

```bash
python -m simulator_agent.skills.input_file_skill.test --file path/to/test.DATA
```

Or test individual tools:

```bash
python -m simulator_agent.skills.input_file_skill.test --file path/to/test.DATA --tool parse_simulation_input_file
```

The test script is located in `test.py` at the root of the skill directory.

