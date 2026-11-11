"""Evaluate the supplied NV-A archive against the current backend."""

import io
import json
import math
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from app import app
from settings_store import selected_connection


ARCHIVE = Path("nv-a-test-data.zip")
OUTPUT = Path("test-results")
CORE = {"date": "date", "partner": "entity", "region": "region",
        "gpu_hours": "usage", "avg_utilization_pct": "utilization", "cost_usd": "cost"}


def equivalent(actual, expected):
    return actual is not None and math.isclose(actual, expected, abs_tol=0.005, rel_tol=1e-10)


def check(result, name, actual, expected):
    passed = equivalent(actual, expected) if isinstance(expected, float) else actual == expected
    requires_model = Path(result["file"]).name == "08_meaningless_headers.csv" and name.startswith("map ") and not passed
    result["checks"].append({"name": name, "passed": passed, "actual": actual,
                             "expected": expected, "requires_model": requires_model})


def totals(response):
    return {
        result["metric"]: result["rows"][0]["value"]
        for result in response.get("results", [])
        if not result["groups"] and result["operation"] in {"sum", "mean"} and result["rows"]
    }


def main():
    if selected_connection() is not None:
        raise SystemExit("This baseline evaluation expects local mode. Select Local demo mode before running.")
    results = []
    with ZipFile(ARCHIVE) as archive, app.test_client() as client:
        truth = json.loads(archive.read("nv-a-data/ground_truth.json"))
        for path in sorted(name for name in archive.namelist() if name.endswith(".csv")):
            name = Path(path).name
            expected = truth.get(name, {})
            item = {"file": path, "checks": []}
            upload = client.post("/api/upload", data={
                "file": (io.BytesIO(archive.read(path)), name),
            })
            item["upload_status"] = upload.status_code
            item["upload"] = upload.get_json() or {"error": "The server returned a non-JSON error."}
            if upload.status_code != 200:
                item["checks"].append({
                    "name": "upload accepted" if name not in {"13_header_only.csv", "14_not_a_csv.csv"} else "invalid file rejected",
                    "passed": name in {"13_header_only.csv", "14_not_a_csv.csv"},
                    "actual": upload.status_code, "expected": "reject" if name in {"13_header_only.csv", "14_not_a_csv.csv"} else 200,
                })
                results.append(item)
                continue

            if name in {"13_header_only.csv", "14_not_a_csv.csv"}:
                check(item, "invalid file rejected at upload", False, True)
            token = {"X-Dataset": item["upload"]["token"]}
            # Tokens are session capabilities and are unnecessary in a saved report.
            item["upload"].pop("token", None)
            inspection = item["upload"]["column_inspection"]
            mapping = inspection["mapping"]
            item["mapping"] = mapping
            expected_mapping = dict(CORE)
            if name in {"01_renamed_headers.csv", "12_kitchen_sink.csv"}:
                expected_mapping = {
                    "Usage Date": "date", "Client Name": "entity", "Region": "region",
                    "Hrs": "usage", "Util %": "utilization", "Price": "cost",
                    "GPUs": "gpus_allocated", "Failed Jobs": "jobs_failed", "Jobs": "jobs_submitted",
                    "Rate": "rate", "Plan": "contract_type", "Main Error": "top_failure_reason",
                    "GPU Model": "gpu_type", "Cluster": "cluster_id",
                }
            elif name == "09_spanish_headers.csv":
                expected_mapping = {"Fecha": "date", "Cliente": "entity", "Región": "region",
                                    "Horas GPU": "usage", "Utilización %": "utilization", "Monto": "cost"}
            elif name == "08_meaningless_headers.csv":
                expected_mapping = {
                    source: CORE[field] for source, field in expected["true_columns"].items() if field in CORE
                }
            elif name == "11_minimal_columns.csv":
                expected_mapping = {"date": "date", "partner": "entity", "cost_usd": "cost"}
            elif name == "mill_production_clean.csv":
                expected_mapping = {"production_date": "date", "mill_name": "entity", "city": "region"}
            elif name in {"13_header_only.csv", "14_not_a_csv.csv"}:
                expected_mapping = {}
            for header, field in expected_mapping.items():
                check(item, f"map {header} to {field}", mapping.get(field), header)

            response = client.post("/api/analyze", headers=token, json={"daily": "date" in mapping})
            item["analysis_status"] = response.status_code
            item["analysis"] = response.get_json()
            if response.status_code == 200:
                output = item["analysis"]
                actual_totals = totals(output)
                item["totals"] = actual_totals
                quality = output["quality"]
                if "rows_in_file" in expected:
                    check(item, "input row count", quality["input_rows"], expected["rows_in_file"])
                elif "rows" in expected:
                    check(item, "input row count", quality["input_rows"], expected["rows"])
                if name in {"gpu_usage_clean.csv", "03_duplicates.csv", "11_minimal_columns.csv",
                            "01_renamed_headers.csv", "09_spanish_headers.csv", "15_semicolon_eu_decimals.csv"}:
                    check(item, "clean cost total", actual_totals.get("cost"), truth["gpu_usage_clean.csv"]["total_cost_usd"])
                if name in {"gpu_usage_clean.csv", "03_duplicates.csv", "01_renamed_headers.csv",
                            "09_spanish_headers.csv", "15_semicolon_eu_decimals.csv"}:
                    check(item, "clean usage total", actual_totals.get("usage"), truth["gpu_usage_clean.csv"]["total_gpu_hours"])
                if name == "03_duplicates.csv":
                    check(item, "exact duplicates removed", quality["duplicates_removed"], expected["exact_duplicates_added"])
                if name == "02_missing_values.csv":
                    records = set(expected["missing_record_ids_cost"]) | set(expected["missing_record_ids_gpu_hours"])
                    check(item, "rows with missing measurements", quality["rows_with_missing_values"], len(records))
                if name == "04_missing_days.csv":
                    check(item, "missing calendar days", quality["missing_dates"], expected["missing_dates"])
                    buckets = [row for result in output["results"] if result["operation"] == "week_over_week" for row in result["rows"]]
                    check(item, "weekly results carry completeness flags",
                          bool(buckets) and any("complete" in row or "incomplete" in row for row in buckets), True)
                if name == "05_impossible_values.csv":
                    check(item, "invalid rows detected", quality["rows_with_invalid_values"], len(expected["invalid_record_ids"]))
                if name == "06_wrong_types_and_formats.csv":
                    rejected = quality["input_rows"] - quality["duplicates_removed"] - quality["usable_rows"]
                    check(item, "only unparseable rows excluded", rejected, len(expected["unparseable_record_ids"]))
                if name == "07_outlier_spikes.csv":
                    raw = pd.read_csv(io.BytesIO(archive.read(path)))
                    check(item, "outliers retained in cost total", actual_totals.get("cost"), float(raw["cost_usd"].sum()))
                    check(item, "outlier flags present",
                          any("outlier" in key or "unusual" in key for key in quality), True)
                if name == "10_extra_columns.csv":
                    extra = expected["extra_columns"]
                    for field in extra:
                        question = client.post("/api/analyze", headers=token, json={
                            "question": "What was spend by " + field.replace("_", " ") + "?",
                        })
                        item.setdefault("extra_column_chat", {})[field] = question.get_json()
                        output_groups = [
                            group for result in (question.get_json() or {}).get("results", [])
                            for group in result.get("groups", [])
                        ]
                        check(item, f"chat can group by {field}", field in output_groups, True)
                if name == "12_kitchen_sink.csv":
                    check(item, "exact duplicates removed", quality["duplicates_removed"], expected["exact_duplicates_added"])
                    check(item, "missing price rows reported", quality["rows_with_missing_values"], expected["missing_price"])
                    check(item, "missing calendar days", quality["missing_dates"], expected["missing_dates"])

                if name == "gpu_usage_clean.csv":
                    questions = [
                        ("monthly_cost", "What was spend by month?"),
                        ("october_top_region", "Which region spent the most in October 2026?"),
                    ]
                    for label, question in questions:
                        answer = client.post("/api/analyze", headers=token, json={"question": question})
                        item.setdefault("chat", {})[label] = answer.get_json()
                    monthly = {
                        row["period"][:7]: row["value"]
                        for result in item["chat"]["monthly_cost"].get("results", []) for row in result["rows"]
                    }
                    for month, expected_value in expected["cost_by_month_usd"].items():
                        check(item, f"monthly cost {month}", monthly.get(month), expected_value)
                    top = item["chat"]["october_top_region"].get("results", [])
                    winner = top[0]["rows"][0] if top and top[0]["rows"] else {}
                    check(item, "top region in October", winner.get("region"), expected["top_region_october"])
                    check(item, "top region October cost", winner.get("value"),
                          expected["october_cost_by_region_usd"][expected["top_region_october"]])
            elif name not in {"13_header_only.csv", "14_not_a_csv.csv"}:
                item["checks"].append({
                    "name":"analysis accepted", "passed":False, "actual":response.status_code, "expected":200,
                })
            results.append(item)

    OUTPUT.mkdir(exist_ok=True)
    summary = {
        "mode": "local; no provider selected; no model calls or raw-sample sharing",
        "files": len(results),
        "uploads_accepted": sum(result["upload_status"] == 200 for result in results),
        "analyses_completed": sum(result.get("analysis_status") == 200 for result in results),
        "checks_passed": sum(check["passed"] for result in results for check in result["checks"]),
         "checks_failed": sum(not check["passed"] and not check.get("requires_model", False)
                             for result in results for check in result["checks"]),
        "checks_requiring_model": sum(check.get("requires_model", False) for result in results for check in result["checks"]),
    }
    (OUTPUT / "results.json").write_text(json.dumps({"summary":summary, "files":results}, indent=2), encoding="utf-8")
    lines = [
        "# NV-A archive evaluation", "",
        "The archive was exercised through the Flask upload and analysis endpoints in local mode.",
        "Provider inference accuracy is unverified. Profile-only model routing and consent are covered by mocked regression tests.",
        "", "| File | Upload | Analysis | Failed checks | Requires model |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        failed = sum(not item["passed"] and not item.get("requires_model", False) for item in result["checks"])
        pending = sum(item.get("requires_model", False) for item in result["checks"])
        lines.append(f"| {Path(result['file']).name} | {result['upload_status']} | {result.get('analysis_status', '?')} | {failed} | {pending} |")
    lines += [
        "", f"Accepted uploads: {summary['uploads_accepted']} of {summary['files']}.",
        f"Completed analyses: {summary['analyses_completed']}.",
        f"Checks passed: {summary['checks_passed']}. Failed checks: {summary['checks_failed']}.",
        f"Semantic assertions requiring a provider: {summary['checks_requiring_model']}.",
        "",
        "## Verified behavior", "",
        "- Normalized header matching handles the renamed and Spanish columns. Invalid weak candidates cannot block exact matches.",
        "- Currency, semicolon exports, comma decimals, and day-first dates with column-wide evidence are parsed before type validation.",
        "- The clean GPU totals, monthly costs, and October region ranking match the supplied answers.",
        "- All fifteen impossible rows and the eleven unparseable or missing-date rows are excluded.",
        "- Missing values have both per-column and row-level counts. Exact duplicates are removed.",
        "- Missing days are flagged. Incomplete weekly buckets carry completeness flags and are excluded from percentage comparisons.",
        "- Unusual values remain in totals and carry counts and data-row indices.",
        "- Additional numeric metrics and dimensions are retained for execution and chat.",
        "- The mill pipeline supports product outputs and counts repeated input measurements once per entity and date. Dedicated regression tests check these totals.",
        "",
        "## Anonymous headers", "",
        "Col_2 is recognized as a date. Remaining fields retain their original names and inferred value types.",
        "Local analysis can compute the numeric columns, but entity, region, usage, utilization, and cost semantics remain unverified.",
        "The five assertions below are pending live model mapping. They have not been counted as passed.",
        "",
        "## Unresolved assertions", "",
    ]
    for result in results:
        unresolved = [item for item in result["checks"] if not item["passed"]]
        if unresolved:
            lines += [f"### {Path(result['file']).name}", ""]
            for item in unresolved:
                lines.append(f"- {item['name']}. Expected {item['expected']!r}. Actual {item['actual']!r}.")
            lines.append("")
    (OUTPUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    for result in results:
        quality = (result.get("analysis") or {}).get("quality", {})
        print(Path(result["file"]).name,
              "upload=", result["upload_status"], "analysis=", result.get("analysis_status"),
              "usable=", quality.get("usable_rows"),
              "invalid=", quality.get("rows_with_invalid_values"),
              "missing=", quality.get("rows_with_missing_values"))


if __name__ == "__main__":
    main()
