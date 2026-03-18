# Tool Decision Tree Reference

This file references the main TOOL_DECISION_TREE.md document.

For the complete decision tree logic, see:
`../../../TOOL_DECISION_TREE.md` (simulator_agent root)

## DATA File Tools in Decision Tree

### Section 2.4: Scenario Test (modify then run)

**Condition:** User message contains a DATA file path **and** modification intent.

**Tool chain:**  
`parse_simulation_input_file` → `simulator_manual` (inferred keyword) → `simulator_examples` (same keyword) → `modify_simulation_input_file` (with manual + example context, `target_keyword`) → `run_and_heal` (on `*_AGENT_GENERATED.DATA`).

**First tool in chain:** `parse_simulation_input_file` (so the agent has file context before manual/examples).

### Section 2.2: HITL: Apply Fix

**Condition:** Previous AI message had `pending_auto_fix` and user says "yes" or "apply fix".

**Tools called:** `patch_simulation_input_keyword` or `modify_simulation_input_file`, then `run_and_heal`.

### Section 2.6: Fallback (LLM tool choice)

**Condition:** None of the above. Agent invokes the LLM with tool catalog.

**Examples:**
- "Parse .../SPE1CASE1.DATA and list sections" → `parse_simulation_input_file` (LLM choice)

