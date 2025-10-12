# NeMo Data Designer Tutorial Style Guide

This guide defines standards and best practices for creating high-quality tutorial notebooks for NeMo Data Designer.

## 📋 Table of Contents

1. [Notebook Structure](#notebook-structure)
2. [Notebook Cell Content](#notebook-cell-content)
3. [Writing Style](#writing-style)
4. [Code Standards](#code-standards)
5. [Documentation Patterns](#documentation-patterns)
6. [Visual Elements](#visual-elements)
7. [Example Patterns](#example-patterns)
8. [Quality Checklist](#quality-checklist)

---

## Notebook Structure

### Title Cell (Cell 0)

Every notebook must start with a markdown cell containing:

1. A descriptive title with an emoji prefix
2. An Early Release warning
3. A description of what the user will learn
4. An important notice about the environment setup
5. Optional suggestion to see the getting started tutorials if this is a new user

**Example:**

```markdown
# 🎨 NeMo Data Designer 101: [Descriptive Title]

> ⚠️ **Warning**: NeMo Data Designer is currently in Early Release and is not recommended for production use.

#### 📚 What you'll learn

[2-3 sentences describing what this notebook demonstrates]

<br>

> 👋 **IMPORTANT** – Environment Setup
>
> - If you haven't already, follow the instructions in the [README](../../README.md) to install the necessary dependencies.
>
> - You may need to restart your notebook's kernel after setting up the environment.
>
> - In this notebook, we assume you have a self-hosted instance of Data Designer up and running.
>
> - For deployment instructions, see the [Installation Options](https://docs.nvidia.com/nemo/microservices/latest/design-synthetic-data-from-scratch-or-seeds/index.html#installation-options) section of the [NeMo Data Designer documentation](https://docs.nvidia.com/nemo/microservices/latest/design-synthetic-data-from-scratch-or-seeds/index.html).
```

### Standard Section Order

1. **Imports** (`### 📦 Import the essentials`)
2. **Client Initialization** (`### ⚙️ Initialize the NeMo Data Designer Client`)
3. **Model Configuration** (`### 🎛️ Define model configurations`)
4. **Config Builder Initialization** (`### 🏗️ Initialize the Data Designer Config Builder`)
5. **Dataset Design** (Custom section titles with appropriate emojis)
6. **Preview** (`### 🔁 Iteration is key – preview the dataset!`)
7. **Analysis** (`### 📊 Analyze the generated data`)
8. **Scale Up** (`### 🆙 Scale up!`)
9. **Next Steps** (`### ⏭️ Next Steps`)

### Final Cell

Tutorial notebooks should end with a "Next Steps" section that:
- Points to the next tutorial in the series, OR
- Encourages users to apply what they learned to their own use cases

**Example:**

```markdown
### ⏭️ Next Steps

Now that you've seen the basics of Data Designer, check out the following notebooks to learn more about:

- [Topic 1](./2-topic-name.ipynb)

- [Topic 2](./3-topic-name.ipynb)
```

---

## Notebook Cell Content

### Markdown Before Coding Sections

**ALWAYS** place a markdown cell before new coding sections to explain what the code does, why it's important, and key concepts being introduced.

**ALWAYS** consolidate markdown content into a single cell when possible—use `<br>` tags to create space rather than using multiple markdown cells.

### Code Cell Grouping

- **One concept per code cell** – Don't mix unrelated operations
- **Separate configuration from execution** – Model config in one cell, usage in another
- **Group related column definitions** but maintain readability

### Comments in Code

- **Use inline comments sparingly** – Let markdown cells do the explaining
- **Single-line comments are strongly preferred** – Keep comments concise and on one line whenever possible
- When needed, use clear, concise comments that add value
- Avoid stating the obvious

**NEVER** do this:
```python
# set value of x
x = 1
```
👆 That's not helpful. Don't do it – ever.

---

## Writing Style

### Tone

- **Friendly and approachable** – Use conversational language
- **Educational** – Explain the "why" not just the "what"
- **Encouraging** – Build confidence in the user
- **Concise** – Respect the user's time

### Markdown Cell Headers

Use progressive header levels:
- `#` for the main tutorial title
- `###` for section headers
- Avoid going deeper than `###`

### Emoji Usage

Use emojis strategically to make section headers more scannable, draw attention to important information, and create visual hierarchy.

**Standard emoji mappings:**
- 🎨 Dataset Designer
- 📦 Imports/Packages
- ⚙️ Configuration/Setup
- 🎛️ Configuration Settings
- 🏗️ Builder/Construction
- 🎲 Samplers/Random generation
- 🦜 LLM-related content
- 🔁 Iteration/Preview
- 📊 Analysis
- 🆙 Scaling up
- ⏭️ Next steps
- 💡 Tips
- ⚡ Advanced features
- 🌱 Seeds and Seed Datasets
- 👋 Important notices
- ⚠️ Warnings

### Blockquote Usage

Use blockquotes for three purposes:

**1. Important Setup Information**
```markdown
> 👋 **IMPORTANT** – Environment Setup
>
> [Setup instructions]
```

**2. Tips and Best Practices**
```markdown
> 💡 **Why Pydantic?**
>
> - Reason 1
>
> - Reason 2
```

**3. Highlighted Content**
```markdown
> ⚡ **Advanced Feature**:
>
> - Explanation
>
> - Example usage
```

**Blockquote formatting rules:**
- Always include emoji and bold header
- Use `>` for every line within the blockquote
- Include blank lines between list items for readability
- Keep content focused and concise

---

## Code Standards

### Imports

```python
from nemo_microservices.data_designer.essentials import (
    CategorySamplerParams,
    DataDesignerConfigBuilder,
    # ... alphabetically ordered
)
```

**Requirements:**
- Import from `essentials` module when available
- Alphabetically order imports
- Use explicit imports (no `import *`)
- One import per line in the tuple

### Variable Naming

**Constants (UPPER_SNAKE_CASE):**
```python
NEMO_MICROSERVICES_BASE_URL = "http://localhost:8080"
MODEL_PROVIDER = "nvidiabuild"
MODEL_ID = "nvidia/nvidia-nemotron-nano-9b-v2"
MODEL_ALIAS = "nemotron-nano-v2"
SYSTEM_PROMPT = "/no_think"
TUTORIAL_OUTPUT_PATH = "data-designer-tutorial-output"
```

**Variables (snake_case):**
```python
data_designer_client = NeMoDataDesignerClient(base_url=NEMO_MICROSERVICES_BASE_URL)
config_builder = DataDesignerConfigBuilder(model_configs=model_configs)
preview = data_designer_client.preview(config_builder)
job_results = data_designer_client.create(config_builder, num_records=20)
```

### Configuration Objects

**Prefer explicit configuration:**
```python
# STRONGLY PREFERRED: Explicit and clear
config_builder.add_column(
    SamplerColumnConfig(
        name="product_category",
        sampler_type=SamplerType.CATEGORY,
        params=CategorySamplerParams(
            values=[
                "Electronics",
                "Clothing",
                "Home & Kitchen",
            ],
        ),
    )
)

# ACCEPTABLE for shorter examples: Keyword arguments
config_builder.add_column(
    name="patient_id",
    column_type="sampler",
    sampler_type="uuid",
    params={
        "prefix": "PT-",
        "short_form": True,
    },
)
```

### Multi-line Strings

**ALWAYS** use parentheses for multi-line strings:

```python
# Be careful with spaces after periods in multi-line strings.
prompt=(
    "You are a customer named {{ customer.first_name }} from {{ customer.city }}. "
    "Write a review of this product."
)
```

### Code Formatting

**Line length:**
- Aim for 88 characters (Black default)
- Break long parameter lists across multiple lines

**Indentation:**
- 4 spaces for Python code
- Align parameters vertically when breaking lines

**Trailing commas:**
- Use trailing commas in multi-line lists/dicts

---

## Documentation Patterns

### Explaining New Concepts

**Pattern 1: Bullet List Introduction**
```markdown
### 🎲 Getting started with sampler columns

- Sampler columns offer non-LLM based generation of synthetic data.
- They are particularly useful for **steering the diversity** of the generated data.

<br>

You can view available samplers using the config builder's `info` property:
```

**Pattern 2: Blockquote with Reasoning**
```markdown
> 💡 **Why use a seed dataset?**
>
> - Seed datasets let you steer the generation process by providing context.
>
> - They inject real-world diversity into your synthetic data.
>
> - Prompt templates can reference any seed dataset fields.
```

### Code Explanations

**Before code cells:**
```markdown
Let's start designing our product review dataset by adding category columns.
```

**After code cells (for transitions):**
```markdown
Next, let's add samplers to generate customer review data.
```

### Inline Comments

**Use inline comments sparingly and keep them single-line whenever possible.**

```python
# Conditional parameters are only supported for Sampler column types.
config_builder.add_column(
    SamplerColumnConfig(
        name="review_style",
        sampler_type=SamplerType.CATEGORY,
        params=CategorySamplerParams(values=["rambling", "brief"]),
        conditional_params={
            "target_age_range == '18-25'": CategorySamplerParams(values=["rambling"]),
        },
    )
)
```

---

## Visual Elements

### Section Breaks

Use `<br>` tags to create visual breathing room:
- After the title cell introduction
- Between major concept explanations
- Before code examples

### Bolding for Emphasis

- **Bold** key terms on first introduction
- **Bold** important concepts
- Don't overuse—reserve for truly important information

### Code Formatting in Markdown

- Use backticks for `variable_names` and `function_names()`
- Use code blocks for multi-line examples
- Use inline code for file paths and configuration values

### Lists

**When to use each list type:**

**Bulleted lists (-):**
- Unordered information
- Feature lists
- Conceptual explanations

**Numbered lists (1., 2., 3.):**
- Sequential steps
- Ordered processes
- Tutorial workflows

**Formatting:**
- **Single-line items are strongly preferred** – Keep list items concise and on one line when possible
- Add a blank line between list items for better readability
- This applies to both bulleted and numbered lists
- Exception: Very short, tightly related items can be kept together

**Example of numbered workflow:**
```markdown
1. Use the `preview` method to generate a sample of records quickly.

2. Inspect the results for quality and format issues.

3. Adjust column configurations, prompts, or parameters as needed.

4. Re-run the preview until satisfied.
```

---

## Example Patterns

### Dataset Design Examples

**Progressive complexity:**
- Start with simple examples (category samplers)
- Build to intermediate (LLM text generation)
- Advance to complex (structured outputs, conditionals)

### Interactive Elements

**1. Preview exploration:**
```python
# Run this cell multiple times to cycle through the 10 preview records.
preview.display_sample_record()
```

**2. DataFrame display:**
```python
# The preview dataset is available as a pandas DataFrame.
preview.dataset
```

**3. Analysis display:**
```python
# Print the analysis as a table.
preview.analysis.to_report()
```

### Validation Calls

Include validation strategically:
```python
# Optionally validate that the columns are configured correctly.
config_builder.validate()
```

Use it:
- After adding multiple columns
- To show it's available (first tutorial)
- Less frequently in later tutorials (users know it exists)

### Cross-referencing

**Within notebook:**
- Reference previous sections: "as we will see below", "as we saw above"
- Point to related concepts: "similar to X we used earlier"

**Between notebooks:**
- When relevant, link to previous tutorials for new users
- Link to official documentation for detailed information
- Provide **relative paths**: `./2-next-tutorial.ipynb`

### Artifacts and Output

**Standardize output handling:**

The `.gitignore` file contains the `data-designer-tutorial-output` directory, so it will be ignored by git.

```python
TUTORIAL_OUTPUT_PATH = "data-designer-tutorial-output"

# Download the job artifacts and save them to disk.
job_results.download_artifacts(
    output_path=TUTORIAL_OUTPUT_PATH,
    artifacts_folder_name="relevant-folder-name",
);
```

---

## Quality Checklist

Before finalizing a tutorial, verify:

- [ ] Title cell follows standard format
- [ ] Early Release warning included
- [ ] Learning objectives clearly stated
- [ ] Environment setup instructions provided
- [ ] All imports from essentials when available
- [ ] Constants use UPPER_SNAKE_CASE
- [ ] Variables use snake_case
- [ ] Markdown cell before each new coding section
- [ ] Appropriate emoji use in headers
- [ ] Blockquotes for tips and important info
- [ ] Comments and list items are single-line whenever possible
- [ ] Validation calls included strategically
- [ ] Next Steps section included (if applicable)
- [ ] Code runs without errors
- [ ] Consistent formatting throughout

---
