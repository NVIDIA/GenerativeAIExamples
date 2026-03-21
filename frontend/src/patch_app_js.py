#!/usr/bin/env python3
from pathlib import Path

app_js = Path("/data/projects/chat-llama-nemotron/frontend/src/App.js")
text = app_js.read_text(encoding="utf-8")

text = text.replace(
    "max_tokens: appConfig?.llm?.model?.max_tokens || 128",
    "max_tokens: 128"
)

text = text.replace(
    "const refs = await searchChunks(cleanQuery, { k: 8 });",
    "const refs = await searchChunks(cleanQuery, { k: 50 });"
)

app_js.write_text(text, encoding="utf-8")
print(f"Updated {app_js}")
