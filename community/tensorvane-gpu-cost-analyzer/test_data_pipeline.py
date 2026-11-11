"""Archive regression tests for parsing, schema handling, and calculation integrity."""

import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd

from app import app
from analysis_engine import Plan, calculation, execute
from column_mapping import resolve_columns
from intake import _dates
from model import MappingChoice
from model import plan_analysis
from providers import Connection


@unittest.skipUnless(Path("nv-a-test-data.zip").exists(), "Archive fixture is unavailable")
class ArchivePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = ZipFile("nv-a-test-data.zip")
        cls.addClassCleanup(cls.archive.close)
        cls.truth = json.loads(cls.archive.read("nv-a-data/ground_truth.json"))
        cls.client = app.test_client()
        cls.no_model = patch("app.selected_connection", return_value=None)
        cls.no_model.start()
        cls.addClassCleanup(cls.no_model.stop)

    @classmethod
    def upload(cls, filename, folder="messy"):
        content = cls.archive.read(f"nv-a-data/{folder}/{filename}")
        result = cls.client.post("/api/upload", data={"file": (io.BytesIO(content), filename)})
        if result.status_code != 200:
            raise AssertionError(result.data)
        return result.json, {"X-Dataset": result.json["token"]}

    def analyze(self, filename, folder="messy", **body):
        uploaded, headers = self.upload(filename, folder)
        response = self.client.post("/api/analyze", headers=headers, json=body)
        self.assertEqual(response.status_code, 200, response.data)
        return uploaded, response.json, headers

    @classmethod
    def raw_frame(cls, filename, folder="messy"):
        return pd.read_csv(io.BytesIO(cls.archive.read(f"nv-a-data/{folder}/{filename}")),
                           keep_default_na=False)

    def total(self, result, metric):
        return next(item["rows"][0]["value"] for item in result["results"]
                    if item["metric"] == metric and item["operation"] == "sum" and not item["groups"])

    def test_all_clean_totals_and_normalized_european_export(self):
        truth = self.truth["gpu_usage_clean.csv"]
        for name, folder in [
            ("gpu_usage_clean.csv", "clean"), ("03_duplicates.csv", "messy"),
            ("01_renamed_headers.csv", "messy"), ("09_spanish_headers.csv", "messy"),
            ("15_semicolon_eu_decimals.csv", "messy"),
        ]:
            with self.subTest(file=name):
                uploaded, result, _ = self.analyze(name, folder)
                self.assertEqual(result["quality"]["usable_rows"], truth["rows"])
                self.assertAlmostEqual(self.total(result, "cost"), truth["total_cost_usd"], places=2)
                self.assertAlmostEqual(self.total(result, "usage"), truth["total_gpu_hours"], places=2)
                self.assertIn("utilization", uploaded["column_inspection"]["mapping"])

    def test_renamed_columns_preserve_all_known_semantics(self):
        uploaded, _ = self.upload("01_renamed_headers.csv")
        expected = {
            "date": "Usage Date", "entity": "Client Name", "usage": "Hrs",
            "cost": "Price", "utilization": "Util %", "gpus_allocated": "GPUs",
            "jobs_failed": "Failed Jobs", "jobs_submitted": "Jobs",
            "rate": "Rate", "contract_type": "Plan", "top_failure_reason": "Main Error",
            "gpu_type": "GPU Model", "cluster_id": "Cluster", "region": "Region",
        }
        for field, header in expected.items():
            self.assertEqual(uploaded["column_inspection"]["mapping"].get(field), header)

    def test_invalid_rows_match_supplied_record_ids(self):
        for name, key in [
            ("05_impossible_values.csv", "invalid_record_ids"),
            ("06_wrong_types_and_formats.csv", "unparseable_record_ids"),
        ]:
            with self.subTest(file=name):
                _, result, _ = self.analyze(name)
                quality = result["quality"]
                indices = sorted(set(quality["invalid_data_rows"]) | set(quality["missing_data_rows"]))
                actual = set(self.raw_frame(name).iloc[indices]["record_id"])
                self.assertEqual(actual, set(self.truth[name][key]))
        self.assertEqual(result["quality"]["usable_rows"], 1402)

    def test_missing_values_count_per_column_and_by_record(self):
        name = "02_missing_values.csv"
        _, result, _ = self.analyze(name)
        quality = result["quality"]
        self.assertEqual(quality["missing_values_by_column"]["cost"], 37)
        self.assertEqual(quality["missing_values_by_column"]["usage"], 24)
        expected = set(self.truth[name]["missing_record_ids_cost"]) | set(self.truth[name]["missing_record_ids_gpu_hours"])
        actual = set(self.raw_frame(name).iloc[quality["missing_data_rows"]]["record_id"])
        self.assertEqual(actual, expected)

    def test_missing_weeks_are_flagged_and_not_compared(self):
        name = "04_missing_days.csv"
        uploaded, result, _ = self.analyze(name)
        self.assertEqual(uploaded["column_inspection"]["expected_frequency"], "day")
        self.assertEqual(result["quality"]["missing_dates"], self.truth[name]["missing_dates"])
        trend = next(item for item in result["results"]
                     if item["metric"] == "cost" and item["operation"] == "week_over_week")
        weeks = {row["period"]: row for row in trend["rows"]}
        for period in ["2026-08-10", "2026-10-12", "2026-10-19"]:
            self.assertFalse(weeks[period]["complete"])
            self.assertIsNone(weeks[period]["change_pct"])
        self.assertIsNone(weeks["2026-08-17"]["change_pct"])

    def test_spikes_are_retained_and_flagged_by_record(self):
        name = "07_outlier_spikes.csv"
        raw = self.raw_frame(name)
        _, result, _ = self.analyze(name)
        quality = result["quality"]
        self.assertEqual(quality["outlier_counts"]["cost"], 4)
        actual = set(raw.iloc[quality["outlier_data_rows"]["cost"]]["record_id"])
        self.assertEqual(actual, set(self.truth[name]["spike_record_ids"]))
        self.assertAlmostEqual(self.total(result, "cost"), raw["cost_usd"].sum(), places=2)

    def test_mill_output_and_repeated_inputs_have_correct_grain(self):
        name = "mill_production_clean.csv"
        raw = self.raw_frame(name, "clean")
        _, result, headers = self.analyze(name, "clean")
        grouped = self.client.post("/api/analyze", headers=headers,
                                   json={"question": "What was total output by mill?"})
        self.assertEqual(grouped.status_code, 200, grouped.data)
        self.assertNotIn("clarification", grouped.json)
        actual = {row["entity"]: row["value"] for row in grouped.json["results"][0]["rows"]}
        self.assertEqual(actual.keys(), self.truth[name]["total_output_tonnes_by_mill"].keys())
        for mill, amount in self.truth[name]["total_output_tonnes_by_mill"].items():
            self.assertEqual(round(actual[mill], 1), amount)
            self.assertAlmostEqual(actual[mill], raw.groupby("mill_name")["output_tonnes"].sum()[mill], places=2)
        expected_input = raw.drop_duplicates(["production_date", "mill_name"])["wheat_input_tonnes"].sum()
        self.assertAlmostEqual(self.total(result, "wheat_input_tonnes"), expected_input, places=2)
        self.assertEqual(result["column_inspection"]["fields"]["wheat_input_tonnes"]["aggregation_grain"], ["date", "entity"])
        blocked = self.client.post("/api/analyze", headers=headers,
                                   json={"question": "What was wheat input by product?"})
        self.assertEqual(blocked.status_code, 400)
        self.assertIn("cannot be split", blocked.json["error"])

    def test_extra_dimensions_are_used_and_unknown_dimensions_rejected(self):
        raw = self.raw_frame("10_extra_columns.csv")
        _, headers = self.upload("10_extra_columns.csv")
        for field in ["account_manager", "project_code"]:
            response = self.client.post("/api/analyze", headers=headers,
                                        json={"question": "What was spend by " + field.replace("_", " ") + "?"})
            self.assertEqual(response.status_code, 200, response.data)
            self.assertNotIn("clarification", response.json)
            result = response.json["results"][0]
            self.assertEqual(result["groups"], [field])
            actual = {row[field]: row["value"] for row in result["rows"]}
            for key, expected in raw.groupby(field)["cost_usd"].sum().items():
                self.assertAlmostEqual(actual[key], expected, places=2)
        rejected = self.client.post("/api/analyze", headers=headers, json={"question": "What was spend by banana?"})
        self.assertIn("clarification", rejected.json)

    def test_kitchen_sink_normalizes_before_mapping(self):
        uploaded, result, _ = self.analyze("12_kitchen_sink.csv")
        self.assertIn("cost", uploaded["column_inspection"]["mapping"])
        self.assertIn("date", uploaded["column_inspection"]["mapping"])
        self.assertEqual(result["quality"]["duplicates_removed"], 10)
        self.assertEqual(result["quality"]["rows_with_missing_values"], 30)
        self.assertEqual(result["quality"]["rows_with_invalid_values"], 0)
        self.assertEqual(result["quality"]["missing_dates"], ["2026-09-22"])

    def test_failure_peak_uses_the_actual_daily_aggregate(self):
        _, headers = self.upload("gpu_usage_clean.csv", "clean")
        response = self.client.post("/api/analyze", headers=headers,
                                    json={"question": "Which day had the most failed jobs?"})
        self.assertEqual(response.status_code, 200, response.data)
        row = response.json["results"][0]["rows"][0]
        expected = self.truth["gpu_usage_clean.csv"]["highest_failure_day"]
        self.assertEqual(row["period"], expected["date"])
        self.assertEqual(row["value"], expected["jobs_failed"])

    def test_anonymous_columns_are_preserved_without_inventing_meanings(self):
        uploaded, result, _ = self.analyze("08_meaningless_headers.csv")
        inspection = uploaded["column_inspection"]
        self.assertNotIn("cost", inspection["mapping"])
        self.assertIn("col_15", inspection["metrics"])
        self.assertEqual(len(inspection["mapping"]), 15)
        self.assertAlmostEqual(self.total(result, "col_15"),
                               self.truth["gpu_usage_clean.csv"]["total_cost_usd"], places=2)

    def test_anonymous_semantics_can_use_profile_only_model_mapping(self):
        expected = {
            "Col_2": "date", "Col_3": "entity", "Col_4": "region",
            "Col_9": "usage", "Col_10": "utilization", "Col_15": "cost",
        }
        connection = Connection("compatible", "https://test.example/v1", "mock", "mock")
        def mapper(connection, profile, unresolved, samples=None, known_mapping=None):
            self.assertIsNone(samples)
            self.assertNotIn("Atlas Genomics", json.dumps(profile))
            return [MappingChoice(column=header, field=expected[header], confidence=0.99)
                    for header in unresolved if header in expected]
        with patch("app.selected_connection", return_value=connection), patch("app.map_columns", side_effect=mapper):
            uploaded, _ = self.upload("08_meaningless_headers.csv")
            for header, field in expected.items():
                self.assertEqual(uploaded["column_inspection"]["mapping"][field], header)


class ParserAndPlanTests(unittest.TestCase):
    def test_ambiguous_slash_dates_are_not_assumed(self):
        dates = _dates(pd.Series(["03/04/2026", "05/06/2026"]))
        self.assertTrue(dates.isna().all())

    def test_model_cannot_ignore_a_requested_group_or_filter(self):
        profile = {"fields": {
            "cost": {"source": "Price", "role": "metric", "aggregation": "sum"},
            "region": {"source": "Region", "role": "dimension", "aggregation": "sum"},
        }}
        connection = Connection("compatible", "https://test.example/v1", "mock", "mock")
        for question in ["What was spend by region?", 'What was spend for region="West"?']:
            with self.subTest(question=question), patch("model.generate", return_value=Plan(
                calculations=[calculation("sum", "cost")], clarification=None,
            )):
                result = plan_analysis(profile, question, profile["fields"], connection)
                self.assertIsNotNone(result.clarification)
                self.assertEqual(result.calculations, [])

    def test_all_operations_work_with_registry_metrics(self):
        values = pd.DataFrame({
            "amount": [10.0, 20.0, 30.0, 40.0],
            "team": pd.Series(["A", "A", "B", "B"], dtype="string"),
            "date": pd.to_datetime(["2026-10-05", "2026-10-12", "2026-10-05", "2026-10-12"], utc=True),
        })
        values.attrs["metrics"] = ["amount"]
        for op in ["sum", "mean", "count", "min", "max", "median", "std", "nunique",
                   "p25", "p75", "p90", "p95", "top_n", "bottom_n", "week_over_week"]:
            options = {"group_by": ["team"]}
            if op in {"top_n", "bottom_n"}:
                options.update(n=2, reduction="sum")
            if op == "week_over_week":
                options.update(grain="week", reduction="sum")
            with self.subTest(operation=op):
                result = execute(values, Plan(calculations=[calculation(op, "amount", **options)], clarification=None))
                self.assertTrue(result[0]["rows"])


if __name__ == "__main__":
    unittest.main()
