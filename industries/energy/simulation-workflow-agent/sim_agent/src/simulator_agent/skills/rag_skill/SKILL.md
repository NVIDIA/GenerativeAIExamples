---
name: rag_skill
description: Retrieve information from simulator manual and example DATA files. Use when answering keyword format questions, syntax queries, or when looking up official documentation and working examples. Essential for understanding keyword definitions, parameter tables, and concrete usage patterns.
license: Apache-2.0
metadata:
  author: sim-agent
  version: "1.0"
  category: simulator
compatibility: Requires vector database with simulator manual and examples, embeddings model, and Python environment with langchain packages
---

# RAG (Retrieval-Augmented Generation) Skill

This skill provides retrieval tools for accessing simulator documentation and example files through vector search.

## Overview

The RAG skill enables agents to:

- **Retrieve** official simulator manual documentation for keyword definitions and syntax
- **Retrieve** example DATA files and case studies for concrete usage patterns
- **Answer** keyword format questions with authoritative sources
- **Provide** working examples to illustrate keyword usage

## Tools

### simulator_manual

Retrieves information from the simulator manual and official documentation using semantic search.

**Usage:**
```python
simulator_manual(query: str) -> str
```

**Parameters:**
- `query`: Natural language query about keywords, syntax, or documentation (e.g., "COMPDAT keyword format", "WELSPECS syntax and fields")

**Example:**
```
simulator_manual("What is the COMPDAT keyword format?")
```

**Returns:** Retrieved documentation snippets from the simulator manual with source citations.

**When to use:** 
- First step in keyword Q&A flow (TOOL_DECISION_TREE.md Section 2.5)
- In scenario test chain after `parse_simulation_input_file` (Section 2.4) to get keyword context
- When user asks about keyword definitions, syntax, or parameter tables

### simulator_examples

Retrieves example DATA files and case studies using semantic search.

**Usage:**
```python
simulator_examples(query: str) -> str
```

**Parameters:**
- `query`: Natural language query about keyword examples or usage patterns (e.g., "COMPDAT keyword format", "WCONINJE injection rate examples")

**Example:**
```
simulator_examples("COMPDAT keyword format")
```

**Returns:** Retrieved example DATA file snippets showing concrete keyword usage.

**When to use:**
- After `simulator_manual` when manual lacks format details or examples (Section 2.5)
- In scenario test chain after `simulator_manual` to get example context for modifications (Section 2.4)
- When user needs working examples to understand keyword syntax

## Workflow Integration

This skill integrates with the Simulator Agent's decision tree (TOOL_DECISION_TREE.md):

1. **Keyword Q&A Flow (Section 2.5):**
   ```
   simulator_manual → (simulator_examples) → answer
   ```

2. **Scenario Test Chain (Section 2.4):**
   ```
   parse_simulation_input_file → simulator_manual (inferred keyword) → simulator_examples (same keyword) → modify_simulation_input_file → run_and_heal
   ```

3. **Keyword Chain (Section 3.4):**
   ```
   simulator_manual → simulator_examples → synthesize format + example → final answer
   ```

## Implementation Details

Tools are implemented as LangChain retriever tools with:
- **Vector store**: Milvus containing embedded simulator manual and examples
- **Embeddings**: NVIDIA embedding API for semantic search
- **Top-k retrieval**: Configurable number of relevant chunks returned (default: 10, reranked to 5)
- **Source citation**: Metadata includes source file paths and section references

### extract_keyword (internal helper)

`scripts/extract_keyword.py` provides RAG + LLM keyword extraction (e.g. "plot field oil" → FOPT). Used by plot_skill validators and other skills that need to infer keywords from natural language.

```python
from simulator_agent.skills.rag_skill.scripts.extract_keyword import extract_keyword

kw = extract_keyword("plot field cumulative oil production", intent="summary_metric")  # -> "FOPT"
```

## Best Practices

1. **Always cite sources**: Include manual section names and example file paths in responses
2. **Use simulator_manual first**: It's the authoritative source for syntax and fields
3. **Use simulator_examples for illustration**: Examples show concrete usage but should not override manual definitions
4. **Handle conflicts**: If examples conflict with manual, prefer manual and explain the conflict

## References

- [Tool Decision Tree](references/TOOL_DECISION_TREE.md) - Routing logic
- [OPM Flow Manual](references/OPM_MANUAL.md) - Manual structure and indexing

## Configuration

RAG tools use Milvus collections created by `./scripts/setup.sh --full`:

| Tool name           | Milvus collection         | Ingested by                    |
|---------------------|---------------------------|--------------------------------|
| `simulator_manual`  | `docs`                    | `ingest_papers.sh`             |
| `simulator_examples`| `simulator_input_examples`| `ingest_opm_examples.py`       |

Environment variables:
- `MILVUS_URI`: Milvus endpoint (default: `http://localhost:19530`; Docker: `http://standalone:19530`)
- `NVIDIA_API_KEY`: Required for embeddings, reranker, and LLM

