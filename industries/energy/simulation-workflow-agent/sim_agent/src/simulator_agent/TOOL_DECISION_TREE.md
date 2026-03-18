# Simulator Agent Tool Decision Tree

This document describes how the agent routes user queries to tools. Routing depends on **conversation state** (first message vs after tool output) and **intent detection** (regex + LLM). When `tool_calls_supported` is true, the LLM chooses tools from the catalog directly; the tree below applies to **manual routing** (no native tool calls).

---

## 1. High-level flow

```
User message
    │
    ├─ [Has ToolMessage in history?] ─No──► First-message routing (Section 2)
    │
    └─ Yes ──► Follow-up routing (Section 3)
```

---

## 2. First message (no tool output yet)

**Routing tree:**

```
First message
    │
    ├─ [Spatial visualization request?] ─Yes──► Final message: suggest GUI (no tool in catalog)
    │
    ├─ [HITL: pending_confirm_run + "yes"/"run"?] ─Yes──► run_and_heal
    │
    ├─ [HITL: pending_auto_fix + "yes"/"apply fix"?] ─Yes──► patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal
    │
    ├─ [Path + run intent, no modification?] ─Yes──► run_and_heal
    │
    ├─ [Path + modification intent?] ─Yes──► parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal
    │
    ├─ [Primary keywords identified, not scenario?] ─Yes──► simulator_manual → (simulator_examples) → answer
    │
    └─ Other ──► LLM tool choice or final_response
```

### 2.0 Spatial visualization → suggest GUI (no tool)

**Condition:** User asks to **visualize spatial results** such as grid structure (dimensions, geometry, cell count), static properties (permeability, porosity, pore volume), or dynamic fields (pressure, saturation). Simulations may be 1D, 2D, or 3D; no tools exist in the catalog for spatial visualization. The agent returns a **final message** directing the user to use a **GUI** (e.g. ResInsight). Time-series and summary plotting stay in chat.

**Tool called:** None.

**Examples (tree):**

```
"What is the grid structure?" / "Grid dimensions?" / "How many cells?"
    └─► Final message: suggest GUI

"Show me the permeability map" / "Visualize porosity distribution"
    └─► Final message: suggest GUI

"Plot pressure" / "Show me the saturation map" / "Pressure distribution"
    └─► Final message: suggest GUI
```

### 2.1 Human-in-the-loop: confirm run

**Condition:** Previous AI message had `pending_confirm_run`.

- **User confirms** ("yes", "run", "go ahead", "sure", etc.) → call `run_and_heal` (with `data_file` from pending).
- **User declines** ("no", "not yet", "cancel", "skip", "don't run", etc.) → `final_response` only (acknowledge; do **not** call `run_and_heal`).

**Examples (tree):**

```
"yes" / "run" (after: "Run the simulation? Reply **yes** or **run** to start.")
    └─► run_and_heal

"not yet" / "no" / "cancel"
    └─► final_response only (do not run)
```

### 2.2 Human-in-the-loop: apply fix

**Condition:** Previous AI message had `pending_auto_fix` and user says "yes" or "apply fix".

**Tools called:** `patch_simulation_input_keyword` or `modify_simulation_input_file`, then `run_and_heal`.

**Examples (tree):**

```
"yes" (after a suggested WELLDIMS / keyword fix)
    └─► patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal

"apply fix"
    └─► patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal
```

### 2.3 Direct run (no modification)

**Condition:** User message contains a DATA file path + run intent (e.g. "run", "execute", "simulate") and **no** modification intent. No scenario-test chain.

**Tool called:** `run_and_heal` (no confirmation prompt — the user has already asked to run).

**Note:** `confirm_before_run` does **not** apply to direct run; it applies only to scenario test (Section 2.4), where the agent has generated a new file and then runs it. For direct run, the user has already said "run", so we do not ask again.

**Examples (tree):**

```
"Run sim_agent/data/knowledge_base/examples/spe1/SPE1CASE1.DATA"
    └─► run_and_heal

"Execute the simulation for SPE1CASE1.DATA"
    └─► run_and_heal

"Start simulation on @.../SPE1CASE1.DATA"
    └─► run_and_heal
```

### 2.4 Scenario test (modify then run)

**Condition:** User message contains a DATA file path **and** modification intent (e.g. "increase injection", "change rate", "test a scenario with...").

**Tool chain:**  
`parse_simulation_input_file` → `simulator_manual` (inferred keyword) → `simulator_examples` (same keyword) → `hitl_confirm_modify` (optional, if `confirm_before_modify` is true) → `modify_simulation_input_file` (with manual + example context, `target_keyword`) → `hitl_confirm_run` (optional, if `confirm_before_run` is true) → `run_and_heal` (on `*_AGENT_GENERATED.DATA`).

**First tool in chain:** `parse_simulation_input_file` (so the agent has file context before manual/examples).

**HITL:** 
- If `confirm_before_modify` is true, agent calls `hitl_confirm_modify` before `modify_simulation_input_file`, waits for user confirmation ("yes" or "apply").
- If `confirm_before_run` is true, agent calls `hitl_confirm_run` before `run_and_heal`, waits for user confirmation ("yes" or "run").

**Examples (tree):**

```
"Test a scenario with increased gas injection rate at 'INJ' in .../SPE1CASE1.DATA" (no HITL)
    └─► parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal

"Test a scenario with increased gas injection rate at 'INJ' in .../SPE1CASE1.DATA" (confirm_before_modify = true)
    └─► parse_simulation_input_file → simulator_manual → simulator_examples → hitl_confirm_modify → (wait for "yes"/"apply") → modify_simulation_input_file → run_and_heal

"Test a scenario with increased gas injection rate at 'INJ' in .../SPE1CASE1.DATA" (confirm_before_run = true)
    └─► parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → hitl_confirm_run → (wait for "yes"/"run") → run_and_heal

"Run SPE1CASE1.DATA with higher gas injection rate at 'INJ'" (both confirms = true)
    └─► parse_simulation_input_file → simulator_manual → simulator_examples → hitl_confirm_modify → (wait for "yes"/"apply") → modify_simulation_input_file → hitl_confirm_run → (wait for "yes"/"run") → run_and_heal

"Modify the well BHP limit in .../SPE1CASE1.DATA and run it"
    └─► parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal (or with HITL confirms if enabled)
```

### 2.5 Keyword / documentation question

**Condition:** LLM identifies **primary keywords** from the query (e.g. COMPDAT, WELSPECS) and user is **not** in scenario-test mode.

**Tool chain:**  
`simulator_manual` (keyword parameter table query) → optionally `simulator_examples` (if manual lacks format or `keywords_manual_first` logic) → final answer (format + fields + example).

**Examples (tree):**

```
"What is the COMPDAT keyword format?"
    └─► simulator_manual → (simulator_examples) → answer

"How do I define well connections? Which keyword?"
    └─► simulator_manual → (simulator_examples) → answer

"Explain WELSPECS syntax and fields"
    └─► simulator_manual → (simulator_examples) → answer

"What are the items in WCONPROD?"
    └─► simulator_manual → (simulator_examples) → answer

"Explain the RUNSPEC keyword"
    └─► simulator_manual → (simulator_examples) → answer
```

### 2.6 Fallback (LLM tool choice)

**Condition:** None of the above. Agent invokes the LLM with `manual_tool_instructions` and a **tool catalog** (name + description). LLM returns `action`, `tool_name`, `tool_input` (or `final_response`).

**Spatial visualization requests:** No tools exist for spatial visualization in the catalog. If the user asks to visualize grid structure, permeability, porosity, pore volume, pressure, saturation, or other spatial fields, the agent does **not** call a tool; it returns a message suggesting use of a **GUI** (e.g. ResInsight) instead. Time-series and summary plotting remain supported in chat.

**Examples (tree):**

```
"Parse .../SPE1CASE1.DATA and list sections"
    └─► parse_simulation_input_file (LLM choice)

"What was the field cumulative oil production (FOPT) for my last run?" (after a run)
    └─► plot_summary_metric (FOPT); see Section 3.1 when prior run_and_heal in history

Plots/comparison with no run_and_heal in history
    └─► "Run the simulation first, then ask again to plot or compare."
```

---

## 3. Follow-up (after at least one ToolMessage)

**Routing tree:**

```
Follow-up (has ToolMessage)
    │
    ├─ [User asks to plot or compare?] ─Yes──► plot_summary_metric or plot_compare_summary_metric
    │       (if last message already plot result → final summary, no new tool)
    │
    ├─ [Scenario chain: last_tool = parse_simulation_input_file?] ─Yes──► simulator_manual (inferred keyword)
    ├─ [Scenario chain: last_tool = simulator_manual?] ─Yes──► simulator_examples (same keyword)
    ├─ [Scenario chain: last_tool = simulator_examples?] ─Yes──► modify_simulation_input_file → run_and_heal
    ├─ [Scenario chain: last_tool = modify_simulation_input_file?] ─Yes──► run_and_heal (or HITL confirm)
    │
    ├─ [Last tool = run_and_heal?] ─Yes──► summarize (optionally auto-fix + re-run)
    │
    ├─ [Last tool = simulator_manual or simulator_examples, keyword Q?] ─Yes──► re-call manual/examples or synthesize answer
    │
    └─ Other ──► LLM tool choice or final_response
```

### 3.1 Plot or compare results

**Condition:** User asks to plot or compare **and** (last message is HumanMessage or ToolMessage). If last message is already a plot tool result → return final summary (no new tool). **Includes:** user replying **yes** or *"Plot FOPT"* (etc.) after the agent asked *"Do you want me to plot the simulation results?"* (Section 3.3).

**Requirement:** A prior `run_and_heal` ToolMessage must exist (or output_dir inferred from conversation). Otherwise agent replies: "Run the simulation first, then ask again to plot or compare."

No confirmation prompt before plotting — the user has already asked to plot (or said "yes" to the agent's offer).

**Examples (tree):**

```
"yes" / "Plot FOPT" (after agent asked "Do you want me to plot the simulation results?" — Section 3.3)
    └─► plot_summary_metric (FOPT or requested metric)

"Plot the results" (after a run, no metric specified)
    └─► final_response: ask user "Which metrics do you want to plot? (e.g., field cumulative oil production (FOPT), FOPR, WOPT)". Do not assume a default.

"Plot field cumulative oil production"
    └─► plot_summary_metric (FOPT)

"Compare those two cases" (after run with baseline + modified or compare arbitrary cases)
    └─► plot_compare_summary_metric

"Plot FOPT and FWPT in the same plot"
    └─► plot_summary_metric (multiple metrics)
```

### 3.2 Scenario test chain (continued)

**Condition:** Same as Section 2.4 but **after** a tool has run. Agent checks `last_tool.name` and advances the chain (no new user query; automatic follow-ups).

**HITL:** 
- If `confirm_before_modify` is true and `last_tool = simulator_examples`, agent calls `hitl_confirm_modify` before `modify_simulation_input_file`, waits for user confirmation.
- If `confirm_before_run` is true and `last_tool = modify_simulation_input_file`, agent calls `hitl_confirm_run` before `run_and_heal`, waits for user confirmation.

**Examples (tree):**

```
last_tool = parse_simulation_input_file
    └─► simulator_manual (inferred keyword)

last_tool = simulator_manual
    └─► simulator_examples (same keyword)

last_tool = simulator_examples (confirm_before_modify = false)
    └─► modify_simulation_input_file (manual_context + example_context, target_keyword)

last_tool = simulator_examples (confirm_before_modify = true)
    └─► hitl_confirm_modify → (wait for "yes"/"apply") → modify_simulation_input_file

last_tool = modify_simulation_input_file (confirm_before_run = false)
    └─► run_and_heal on *_AGENT_GENERATED.DATA

last_tool = modify_simulation_input_file (confirm_before_run = true)
    └─► hitl_confirm_run → (wait for "yes"/"run") → run_and_heal on *_AGENT_GENERATED.DATA
```

### 3.3 After `run_and_heal`

**Condition:** Last message is a ToolMessage from `run_and_heal`.

**Behavior (no extra user message):** Failure + auto-fix → `patch_simulation_input_keyword` or `modify_simulation_input_file` → `run_and_heal` again; then summarize. Success or no auto-fix → LLM summarizes (`simulation_result_summary`). **On success, the agent proactively asks:** *"Do you want me to plot the simulation results?"* Optionally if failure + `auto_fix_ask_user`: "Apply this fix? Reply yes or apply fix."

**Then (user replies):** If the user says **yes** or asks for a plot (e.g. *"Plot FOPT"*, *"Plot field cumulative oil production"*), the next message is routed to **Section 3.1** and the agent calls `plot_summary_metric` (or `plot_compare_summary_metric` for comparison).

**Examples (tree):**

```
Last tool = run_and_heal, simulation failed, auto_fix enabled
    └─► patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal → summarize

Last tool = run_and_heal, simulation succeeded
    └─► summarize (agent asks: "Do you want me to plot the simulation results?")

User then says "yes" / "Plot FOPT" / "Plot field cumulative oil production"
    └─► Section 3.1 → plot_summary_metric (FOPT or requested metric)
```

### 3.4 Keyword chain (after simulator_manual / simulator_examples)

**Condition:** Last tool is `simulator_manual` or `simulator_examples` and user asked a keyword-format/meaning question.

**Behavior:** Re-call `simulator_manual` if only TOC; call `simulator_examples` if manual lacks format; else extract format/fields and LLM summarize → final answer.

**Examples (tree):**

```
User: "What is COMPDAT format?" → last_tool = simulator_manual
    └─► (if needed) simulator_examples → formatted answer (format + fields + source)

User: "What is COMPDAT format?" → last_tool = simulator_examples
    └─► synthesize format + example → final answer
```

### 3.5 Fallback (LLM tool choice)

**Condition:** Has ToolMessage but no special case (plot, compare, scenario, run_and_heal, keyword chain). Agent uses `manual_tool_instructions` + tool catalog.

**Examples (tree):**

```
```

---

## 4. Tool summary by category

| Category        | Tools |
|----------------|--------|
| **RAG**        | `simulator_manual`, `simulator_examples` |
| **DATA file**  | `parse_simulation_input_file`, `modify_simulation_input_file`, `patch_simulation_input_keyword` |
| **Simulation** | `run_and_heal`, `monitor_simulation`, `stop_simulation` |
| **Plot/compare** | `plot_summary_metric`, `plot_compare_summary_metric` |
| **Results**    | `read_simulation_summary`, `read_grid_properties` |

---

## 5. Quick reference: query → first tool (or outcome)

```
"Run FILE.DATA" (no change)
    └─► run_and_heal

"Test scenario with change in FILE.DATA"
    └─► parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal

"What is COMPDAT format?"
    └─► simulator_manual → (simulator_examples) → answer

"Parse FILE.DATA" / "List sections in FILE.DATA"
    └─► parse_simulation_input_file (via LLM)

"Plot results" / "Plot FOPT" (after run)
    └─► plot_summary_metric

"Compare those two cases" (after run)
    └─► plot_compare_summary_metric

"Yes" after confirm-run prompt
    └─► run_and_heal

"Yes" / "apply fix" after auto-fix suggestion
    └─► patch_simulation_input_keyword or modify_simulation_input_file → run_and_heal

Spatial visualization (grid, permeability, porosity, pressure, saturation, etc.)
    └─► Final message: suggest GUI (no tool)

Other (read summary, properties, etc.)
    └─► LLM chooses from catalog (e.g. read_simulation_summary, read_grid_properties)
```

---

## 6. Removed redundant tools

The following tools were removed as stubs/placeholders overlapping real functionality:

- **plot_results** — Replaced by `plot_summary_metric` (which actually generates plots).
- **compare_runs** — Replaced by `plot_compare_summary_metric` (which actually compares cases).
- **explain_keyword** — Replaced by the keyword Q&A flow using `simulator_manual` → `simulator_examples` directly.

### Never hard-wired in agent (LLM-only)

These are only used when the LLM picks them from the tool catalog. They are not referenced in `graph/nodes.py` routing logic:

- **monitor_simulation** – "Check simulation progress"; useful for background runs.
- **stop_simulation** – "Stop a running simulation".
- **read_simulation_summary**, **read_grid_properties** – Results/analysis; only via LLM choice (and tests/MCP).

**Spatial visualization not in catalog:** Grid structure, permeability, porosity, pore volume, pressure, saturation, and other spatial fields are not offered as visualization tools. The agent detects spatial visualization requests and suggests using a GUI (e.g. ResInsight) instead.

### Summary

- **Keep but optional (LLM-only):** `monitor_simulation`, `stop_simulation`, and the `read_simulation_summary` / `read_grid_properties` tools—they add value when the LLM (or MCP client) selects them.

---

*Source: `graph/nodes.py` — `agent_node`, manual routing branch and ToolNode.*
