# DATA File Processing Examples

## Example 1: Parse a DATA File

**User query:**
```
Parse data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA
```

**Tool call:**
```python
parse_simulation_input_file(file_path="data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA")
```

**Result:**
```
Sections found: HEADER, RUNSPEC, GRID, PROPS, SOLUTION, SUMMARY, SCHEDULE
```

## Example 2: Scenario Test with Modification

**User query:**
```
Test a scenario with increased injection rate in SPE1CASE1.DATA
```

**Tool chain:**
1. `parse_simulation_input_file("SPE1CASE1.DATA")` → Get file structure
2. `simulator_manual("WCONINJE")` → Get keyword documentation
3. `simulator_examples("WCONINJE")` → Get examples
4. `modify_simulation_input_file(
       file_path="SPE1CASE1.DATA",
       modifications="Increase water injection rate for well I1 to 55",
       output_path="SPE1CASE1_AGENT_GENERATED.DATA",
       target_keyword="WCONINJE",
       manual_context="...",
       example_context="..."
   )` → Apply modification
5. `run_and_heal("SPE1CASE1_AGENT_GENERATED.DATA")` → Run simulation

## Example 3: Patch a Keyword (Auto-fix)

**User query:**
```
Apply fix for WELLDIMS
```

**Tool call:**
```python
patch_simulation_input_keyword(
    file_path="SPE1CASE1.DATA",
    keyword="WELLDIMS",
    output_path="SPE1CASE1_FIXED.DATA",
    item_index=1,
    new_value="10"
)
```

**Result:**
```
Patched keyword 'WELLDIMS' only; rest of file unchanged.
- Input: SPE1CASE1.DATA
- Output: SPE1CASE1_FIXED.DATA
```

## Example 4: Modify with Natural Language

**User query:**
```
Change the oil production rate for well PROD1 to 5000 STB/day
```

**Tool call:**
```python
modify_simulation_input_file(
    file_path="SPE1CASE1.DATA",
    modifications="Change the oil production rate for well PROD1 to 5000 STB/day in WCONPROD",
    output_path="SPE1CASE1_MODIFIED.DATA",
    target_keyword="WCONPROD"
)
```

**Result:**
```
LLM modification complete.
- File: SPE1CASE1.DATA
- Output: SPE1CASE1_MODIFIED.DATA
- Changes applied: Yes
```

