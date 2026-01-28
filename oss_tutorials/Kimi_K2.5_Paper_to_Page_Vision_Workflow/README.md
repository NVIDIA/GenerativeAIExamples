# ML Paper Webpage Generator

Transform ML research papers into HTML summaries with CSS animations using **Kimi K2.5** via NVIDIA AI endpoints.

**Input:** PDF file of an ML paper
**Output:** Single HTML file with animated diagram

## Model

This project uses [Kimi K2.5](https://build.nvidia.com/moonshotai/kimi-k2.5) - a vision-language model from Moonshot AI, available through NVIDIA AI endpoints.

## How It Works

```
extract_pdf → analyze_paper → generate_webpage
```

1. **Extract PDF** - Convert pages to images
2. **Analyze Paper** - Vision model extracts title, abstract, contributions, and describes the key diagram
3. **Generate Webpage** - Creates HTML with a CSS animation illustrating the paper's core concept

## Setup

### 1. Get an NVIDIA API Key

1. Go to [build.nvidia.com](https://build.nvidia.com/)
2. Sign in or create an account
3. Navigate to [Kimi K2.5](https://build.nvidia.com/moonshotai/kimi-k2.5)
4. Click "Get API Key" to generate your key

### 2. Install Dependencies

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 3. Configure API Key

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
NVIDIA_API_KEY=nvapi-your-key-here
```

## Usage

```bash
uv run jupyter notebook kimi_vision_paper_to_page_workflow.ipynb
```

Run all cells, then:

```python
workflow = PaperWebpageWorkflow()
result = workflow.process_and_save("your_paper.pdf")
```

Display the output:

```python
from IPython.display import IFrame
IFrame("your_paper.html", width="100%", height=600)
```

## Project Structure

```
├── pyproject.toml                          # Dependencies
├── .env.example                            # API key template
├── README.md                               # This file
└── kimi_vision_paper_to_page_workflow.ipynb  # Main notebook
```
