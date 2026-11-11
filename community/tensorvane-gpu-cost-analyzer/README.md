# Tensorvane: AI GPU Cost Analyzer

The app is called Pears Analyzer in its UI.

Pears Analyzer is a local workspace for exploring operational CSVs. Pandas cleans the data and computes results. The model proposes validated JSON plans and selects the computed facts for the executive narrative. Python inserts all reported numbers from the results.

## Use with NVIDIA NIM

Open **Model settings**, choose **OpenAI-compatible**, and enter:

- Base URL: `https://integrate.api.nvidia.com/v1` (hosted NIM on build.nvidia.com), or your self-hosted NIM, for example `http://localhost:8000/v1`
- API key: your `nvapi-...` key

Pick a model that returns valid JSON, for example a Llama 3.1 Nemotron model.

## Run on Windows

From PowerShell in this folder:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open [the workspace](http://127.0.0.1:5000). Start with **Choose CSV** or **Try demo**. After an upload, select **Run analysis**. The backend detects and validates columns on upload. Daily gap checks are selected automatically for consistently daily data that includes weekends. You can change that setting when another calendar is expected. CSV files should be UTF-8 and fit the 8 MB, 100-column, and 100,000-row upload limits.

The parser handles comma, semicolon, tab, and pipe separators; currency symbols and grouping separators; European decimal commas; ISO dates; and slash dates with evidence for day/month order. Ambiguous slash dates remain invalid. Usage is nonnegative, and utilization uses a 0–100 scale.

## Connect an AI model

Open **Model settings** in the top-right corner. Choose OpenAI, Anthropic, Google Gemini, or an OpenAI-compatible endpoint. Enter your API key, save the provider, select a model, and click **Use model**. Pears Analyzer keeps the API key in Windows Credential Manager and saves the model list and active selection across restarts. You can refresh a provider's catalog by saving again with the key field blank, or remove the provider and its stored key.

For an OpenAI-compatible provider, enter its API base URL including any version path (for example, `https://openrouter.ai/api/v1` or a local Ollama server at `http://localhost:11434/v1`). Add a model ID manually if discovery omits it. The selected model needs to accept text and return valid JSON. Providers may list models that lack the required text or JSON capability.

Choose **Local analysis** for key-free reports and limited chat. Try “Which region spent the most in October?” in the demo. Existing `OPENAI_API_KEY` and `OPENAI_MODEL` environment settings remain available as a separate selection.

Column detection runs automatically. Rules match normalized headers and validate numeric and date fields against the values. The selected model handles unresolved columns using headers and derived profiles containing types, ranges, null rates, and masked shapes. A mapping needs a score of at least 95%, at least 80% compatible nonblank values for numeric or date fields, and a unique field assignment. These scores are heuristic and model-reported estimates.

The **Detected columns** section shows semantic mappings, value types, and retained source columns. Additional numeric metrics, identifiers, and categorical dimensions remain available to the executor and chat. A column with uncertain semantics keeps its original name. Reports include coverage notes, and chat requests with an unavailable breakdown receive a clarification.

Anonymous names such as `Col_9` do not establish whether a metric represents usage or money. The application can analyze that column by its original name. Semantic mapping can use the selected model, with a separate per-column consent action for raw samples when profile mapping remains below the confidence threshold. The planner receives the field registry, profiles, and data quality counts. The reporting call receives computed facts and the quality counts. Uploads live in server memory until replaced, evicted, or the server stops.

To run the same rules directly against a CSV:

```powershell
python column_mapping.py "path\to\data.csv"
```

The inspection script prints the accepted mapping and the reason recorded for every column. API clients can omit `mapping` from `POST /api/analyze` to use automatic detection. Existing clients can continue sending an explicit mapping override.

The overview includes **Usage by account** whenever usage and an account field are available. It uses account IDs as the grouping key, with account names as display labels when available. A renamed account keeps its ID-based total. Client, customer, or partner names serve as a fallback when the file has no explicit account fields. The table includes every account, sorted by total usage, with search and pagination. Unknown account IDs appear under **Unassigned**.

## Calculation audit

Every report and chat response includes aggregate tables and its validated plan. Plans can use numeric reductions, row counts, distinct counts, grouped rankings, calendar filters, and weekly comparisons. Week-over-week changes require adjacent Monday-start weeks and a nonzero baseline. Missing days are never filled with zero.

Missing and invalid measurements are counted by column and by data row. The engine checks utilization bounds, nonnegative physical measurements, and failed jobs exceeding submitted jobs. Unusual upper-tail values are flagged using six interquartile ranges within available entity/product/workload groups and remain in totals. Period tables show completeness, and daily datasets compare only complete adjacent weeks.

Repeated input and machine-duration columns that are constant within entity/date groups are recorded at that aggregation grain. Their totals count each measurement once. Splitting those batch measurements across incompatible product rows is rejected.

Run the regression suite and archive evaluation with:

```powershell
python -m unittest test_column_mapping test_data_pipeline
python evaluate_test_data.py
```

The browser workflow checks require Microsoft Edge and the optional Playwright test package:

```powershell
python -m pip install playwright
# Leave python app.py running in another terminal.
python tests/browser_workflow.py
```

Run the browser checks with **Local analysis** selected. They cover demo analysis, CSV upload, invalid-file and network-error recovery, chat, chart metrics, account search, all navigation views, model settings, keyboard dialog dismissal, and responsive layouts at five viewport widths. Screenshots and the browser check report are saved in `test-results/`. Run all Python regression tests with `python -m unittest discover -v`.

The evaluation writes detailed results to `test-results/`. Live inference accuracy requires configured provider credentials. Regression tests exercise provider mapping and consent with mocked model responses.

The archive evaluation (`evaluate_test_data.py`) and archive-based tests need a test-data archive (`nv-a-test-data.zip`) that is not published. Without it, those tests are skipped.
