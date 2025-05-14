## Enabling Reasoning in Nemotron Model

To enable reasoning in the Nemotron model, you need to set the `ENABLE_NEMOTRON_THINKING` environment variable to `true`.

```bash
export ENABLE_NEMOTRON_THINKING=true
```

This will enable the Nemotron model to use its reasoning capabilities. Which includes using the prompt `nemotron_thinking_prompt` in the prompt.yaml file instead of the default `rag_template`. It will also update llm_parameters temperature to 0.6 and top_p to 0.95.

## Displaying the reasoning tokens in the response

To display the reasoning tokens in the response, you need to set the `FILTER_THINK_TOKENS` environment variable to `false`.

```bash
export FILTER_THINK_TOKENS=false
```

This will display the reasoning tokens in the response.