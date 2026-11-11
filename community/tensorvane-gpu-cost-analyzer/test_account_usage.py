"""Regression checks for complete, identity-safe account usage breakdowns."""

import io
import unittest
from unittest.mock import patch

from app import app, datasets
from analysis_engine import Plan, calculation
from model import plan_analysis
from providers import Connection


class AccountUsageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.local = patch("app.selected_connection", return_value=None)
        self.local.start()
        self.addCleanup(self.local.stop)
        datasets.clear()

    def upload(self, csv):
        uploaded = self.client.post("/api/upload", data={
            "file": (io.BytesIO(csv.encode()), "accounts.csv"),
        })
        self.assertEqual(uploaded.status_code, 200, uploaded.data)
        headers = {"X-Dataset": uploaded.json["token"]}
        analyzed = self.client.post("/api/analyze", headers=headers, json={})
        self.assertEqual(analyzed.status_code, 200, analyzed.data)
        return uploaded.json, analyzed.json, headers

    def rollup(self, analysis):
        return next(result for result in analysis["results"] if result.get("account_usage"))

    def test_account_ids_preserve_identity_and_renamed_labels(self):
        _, analysis, _ = self.upload(
            "Account ID,Account Name,Client Name,GPU_Hrs\n"
            "001,Alpha,Client X,10\n001,Alpha renamed,Client Y,20\n"
            "002,Beta,Client X,5\n003,,Client Z,7\n"
        )
        result = self.rollup(analysis)
        self.assertEqual(result["groups"], ["account_id"])
        values = {row["account_id"]: row for row in result["rows"]}
        self.assertEqual(values["001"]["value"], 30)
        self.assertEqual(values["001"]["account"], "Multiple account names")
        self.assertEqual(values["002"]["value"], 5)
        self.assertIsNone(values["003"]["account"])
        self.assertEqual([row["value"] for row in result["rows"]], [30, 7, 5])

    def test_every_account_is_returned_beyond_one_hundred(self):
        csv = "Billing Account ID,GPU_Hours\n" + "\n".join(
            f"{index:03d},{index + 1}" for index in range(130)
        )
        uploaded, analysis, headers = self.upload(csv)
        self.assertEqual(uploaded["column_inspection"]["mapping"]["account_id"], "Billing Account ID")
        result = self.rollup(analysis)
        self.assertFalse(result["truncated"])
        self.assertEqual(result["group_count"], 130)
        self.assertEqual(len(result["rows"]), 130)
        self.assertEqual(result["rows"][0], {"account_id": "129", "value": 130})
        self.assertEqual(result["rows"][-1], {"account_id": "000", "value": 1})
        answer = self.client.post("/api/analyze", headers=headers, json={"question": "Show total usage by account"})
        self.assertEqual(answer.status_code, 200, answer.data)
        self.assertEqual(len(self.rollup(answer.json)["rows"]), 130)

    def test_account_name_and_customer_fallback(self):
        for header, group in [("Account Name", "account"), ("Partner", "entity")]:
            with self.subTest(header=header):
                _, analysis, _ = self.upload(f"{header},Hours\nAlpha,10\nBeta,7\nAlpha,5\n")
                result = self.rollup(analysis)
                self.assertEqual(result["groups"], [group])
                self.assertEqual({row[group]: row["value"] for row in result["rows"]}, {"Alpha": 15, "Beta": 7})

    def test_unknown_account_rows_are_visible(self):
        _, analysis, _ = self.upload("Account ID,Hours\n001,10\n,4\n002,7\n")
        result = self.rollup(analysis)
        self.assertIn({"account_id": None, "value": 4}, result["rows"])
        self.assertEqual(sum(row["value"] for row in result["rows"]), 21)

    def test_explicit_account_id_override_preserves_identifiers(self):
        _, _, headers = self.upload("A,B\n001,10\n002,7\n")
        response = self.client.post("/api/analyze", headers=headers,
                                    json={"mapping": {"account_id": "A", "usage": "B"}})
        self.assertEqual(response.status_code, 200, response.data)
        result = self.rollup(response.json)
        self.assertEqual({row["account_id"]: row["value"] for row in result["rows"]}, {"001": 10, "002": 7})
        self.assertEqual(response.json["column_inspection"]["fields"]["account_id"]["role"], "dimension")

    def test_other_dimensions_are_not_assumed_to_be_accounts(self):
        for header in ["Region", "Mill Name"]:
            with self.subTest(header=header):
                _, analysis, _ = self.upload(f"{header},Hours\nEast,10\nWest,7\n")
                self.assertFalse(any(result.get("account_usage") for result in analysis["results"]))

    def test_model_report_includes_required_account_totals(self):
        registry = {
            "usage": {"source": "GPU_Hrs", "role": "metric", "aggregation": "sum"},
            "account_id": {"source": "Account ID", "role": "dimension", "aggregation": "sum"},
        }
        response = Plan(calculations=[calculation("sum", "usage")], clarification=None)
        connection = Connection("compatible", "https://test.example/v1", "mock", "mock")
        with patch("model.generate", return_value=response):
            plan = plan_analysis({"fields": registry}, None, registry, connection)
        self.assertTrue(any(step.metric == "usage" and step.op == "sum"
                            and step.group_by == ["account_id"] for step in plan.calculations))


if __name__ == "__main__":
    unittest.main()
