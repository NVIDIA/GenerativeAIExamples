"""Regression checks for backend-owned column detection and consent boundaries."""

import io
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app import app, datasets
from column_mapping import resolve_columns
from model import MappingChoice
from providers import Connection


def frame(values):
    return pd.DataFrame(values, dtype="string")


class AutomaticMappingTests(unittest.TestCase):
    def test_headers_and_types_resolve_without_confirmation(self):
        result = resolve_columns(frame({
            "TotalCost_USD": ["10", "20"], "GPUHours": ["2", "3"],
            "RecordedAt": ["2026-10-01", "2026-10-02"], "Zone": ["East", "West"],
        }))
        self.assertEqual(result["mapping"], {
            "cost": "TotalCost_USD", "usage": "GPUHours", "date": "RecordedAt", "region": "Zone",
        })
        self.assertTrue(result["ready"])

    def test_numeric_identifier_does_not_become_cost(self):
        result = resolve_columns(frame({"id": ["100", "200"], "unknown": ["1", "2"]}))
        self.assertNotIn("cost", result["mapping"])
        self.assertEqual(result["fields"]["id"]["role"], "identifier")
        self.assertEqual(result["metrics"], ["unknown"])

    def test_colliding_fields_and_invalid_types_remain_unmapped(self):
        result = resolve_columns(frame({
            "Cost": ["10", "20"], "Spend": ["30", "40"], "Date": ["bad", "data"],
        }))
        self.assertNotIn("cost", result["mapping"])
        self.assertNotIn("date", result["mapping"])
        self.assertEqual(result["columns"]["Cost"]["status"], "ambiguous")
        self.assertEqual(result["columns"]["Date"]["status"], "invalid_type")

    def test_unique_date_can_be_detected_from_values(self):
        result = resolve_columns(frame({
            "x": ["2026-10-01", "2026-10-02"], "Cost": ["10", "20"],
        }))
        self.assertEqual(result["mapping"]["date"], "x")
        self.assertEqual(result["columns"]["x"]["source"], "value_profile")

    def test_model_only_receives_profile_and_must_pass_validation(self):
        def mapper(profile, unresolved, known):
            self.assertNotIn("HiddenCustomer", str(profile))
            self.assertIn("unfamiliar", unresolved)
            self.assertEqual(known, {"region": "Region"})
            return [MappingChoice(column="unfamiliar", field="cost", confidence=0.99)]
        result = resolve_columns(
            frame({"unfamiliar": ["10", "20"], "Region": ["HiddenCustomer", "Other"]}),
            semantic_mapper=mapper,
        )
        self.assertEqual(result["mapping"]["cost"], "unfamiliar")

    def test_model_cannot_assign_same_field_twice_or_override_rules(self):
        def mapper(*_):
            return [
                MappingChoice(column="x", field="cost", confidence=1.0),
                MappingChoice(column="y", field="usage", confidence=1.0),
                MappingChoice(column="z", field="usage", confidence=1.0),
            ]
        result = resolve_columns(
            frame({"Cost": ["10"], "x": ["20"], "y": ["3"], "z": ["4"]}),
            semantic_mapper=mapper,
        )
        self.assertEqual(result["mapping"]["cost"], "Cost")
        self.assertNotIn("usage", result["mapping"])

    def test_model_score_and_type_must_both_pass(self):
        for values, score in [(["10", "20"], 0.8), (["10", "bad", "bad"], 0.99)]:
            def mapper(*_):
                return [MappingChoice(column="x", field="cost", confidence=score)]
            result = resolve_columns(frame({"x": values}), semantic_mapper=mapper)
            self.assertNotIn("cost", result["mapping"])


class MappingApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.connection_patch = patch("app.selected_connection", return_value=None)
        self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)
        datasets.clear()

    def upload(self, content):
        response = self.client.post("/api/upload", data={
            "file": (io.BytesIO(content.encode()), "test.csv"),
        })
        self.assertEqual(response.status_code, 200, response.data)
        return response.json, {"X-Dataset": response.json["token"]}

    def test_upload_and_analysis_need_no_browser_mapping(self):
        uploaded, headers = self.upload("Price,Region\n10,East\n20,West\n")
        self.assertEqual(uploaded["column_inspection"]["mapping"], {"cost": "Price", "region": "Region"})
        response = self.client.post("/api/analyze", headers=headers, json={})
        self.assertEqual(response.status_code, 200, response.data)
        total = response.json["results"][0]["rows"][0]["value"]
        self.assertEqual(total, 30)

    def test_existing_mapping_override_still_works(self):
        _, headers = self.upload("x\n10\n20\n")
        response = self.client.post("/api/analyze", headers=headers, json={"mapping": {"cost": "x"}})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.json["results"][0]["rows"][0]["value"], 30)

    def test_unknown_metric_has_a_status_and_does_not_guess(self):
        uploaded, headers = self.upload("x\n10\n20\n")
        self.assertTrue(uploaded["column_inspection"]["ready"])
        self.assertNotIn("cost", uploaded["column_inspection"]["mapping"])
        response = self.client.post("/api/analyze", headers=headers, json={})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.json["results"][0]["metric"], "x")
        response = self.client.post("/api/analyze", headers=headers, json={"question": "What is total spend?"})
        self.assertIn("clarification", response.json)

    def test_automatic_model_fallback_and_sample_consent(self):
        connection = Connection("compatible", "https://provider.example/v1", "test-model", "test-key")
        calls = []
        def mapping_model(connection, profile, unresolved, samples=None, known_mapping=None):
            calls.append(samples)
            return [MappingChoice(column="x", field="cost", confidence=0.99 if samples else 0.8)]
        with patch("app.selected_connection", return_value=connection), patch("app.map_columns", side_effect=mapping_model):
            uploaded, headers = self.upload("x,Customer\n11.111,HiddenCustomer\n22.222,Other\n33.333,Third\n")
            self.assertEqual(calls, [None])
            self.assertNotIn("cost", uploaded["column_inspection"]["mapping"])
            consent = {"column": "x", "destination": connection.destination, "model": connection.model}
            response = self.client.post("/api/map", headers=headers, json=consent)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(calls, [None])
            response = self.client.post("/api/map", headers=headers, json=consent | {"consent": True})
            self.assertEqual(response.status_code, 200, response.data)
            self.assertTrue(response.json["column_inspection"]["ready"])
            self.assertEqual(calls[-1], {"x": ["11.111", "22.222"]})
            self.assertNotIn("HiddenCustomer", str(calls))
            refreshed = self.client.post("/api/columns", headers=headers)
            self.assertEqual(refreshed.status_code, 200)
            self.assertEqual(refreshed.json["column_inspection"]["mapping"]["cost"], "x")


if __name__ == "__main__":
    unittest.main()
