"""Resolve semantic fields and retain additional CSV metrics and dimensions."""

import argparse
import json
from collections import Counter
from pathlib import Path

from intake import _dates, column_profiles, read_csv, suggest_mappings
from schema import (
    ALIASES, AUTO_CONFIRM, METRICS, MIN_TYPE_FRACTION,
    field_id, identifier_header,
)


def compatible(field, profile):
    if profile["null_rate"] == 1:
        return False
    if field in METRICS:
        return profile["numeric_fraction"] >= MIN_TYPE_FRACTION
    if field == "date":
        return profile["date_fraction"] >= MIN_TYPE_FRACTION
    return field in ALIASES


def apply_choices(choices, profile, decisions, mapping, allowed, source):
    candidates = [
        choice for choice in choices
        if choice.column in allowed and choice.field in ALIASES and 0 <= choice.confidence <= 1
    ]
    eligible = [
        choice for choice in candidates
        if choice.confidence >= AUTO_CONFIRM and compatible(choice.field, profile["columns"][choice.column])
    ]
    columns = Counter(choice.column for choice in eligible)
    fields = Counter(choice.field for choice in eligible)
    for choice in candidates:
        decision = decisions[choice.column]
        decision.update(field=choice.field, score=choice.confidence, source=source)
        if choice.confidence < AUTO_CONFIRM:
            decision.update(status="low_score", reason="Semantic mapping remains uncertain.")
        elif not compatible(choice.field, profile["columns"][choice.column]):
            decision.update(status="invalid_type", reason="Values do not support the proposed field.")
        elif (choice.field in mapping or columns[choice.column] > 1 or fields[choice.field] > 1):
            decision.update(status="ambiguous", reason="Multiple validated candidates target this field.")
        else:
            decision.update(status="mapped", reason="Semantic mapping and value-type validation passed.")
            mapping[choice.field] = choice.column


def resolve_columns(frame, *, profile=None, semantic_mapper=None, sample_mapper=None, prior_samples=None):
    profile = profile if profile is not None else column_profiles(frame)
    decisions = {
        header: {"field": None, "score": None, "source": "rules", "status": "unrecognized",
                 "reason": "Retained using its original column name."}
        for header in frame.columns
    }
    proposals = suggest_mappings(frame)
    eligible = [
        item for item in proposals if item.confidence >= AUTO_CONFIRM
        and not item.needs_confirmation and compatible(item.field, profile["columns"][item.column])
    ]
    field_counts = Counter(item.field for item in eligible)
    mapping = {}
    for item in proposals:
        decision = decisions[item.column]
        decision.update(field=item.field, score=item.confidence)
        if not compatible(item.field, profile["columns"][item.column]):
            decision.update(status="invalid_type", reason="Values do not support the matched field.")
        elif item.confidence < AUTO_CONFIRM:
            decision.update(status="low_score", reason="Header similarity is below the semantic threshold.")
        elif item.needs_confirmation or field_counts[item.field] > 1:
            decision.update(status="ambiguous", reason="Multiple validated candidates or meanings match this field.")
        else:
            decision.update(status="mapped", reason="Header matching and value-type validation passed.")
            mapping[item.field] = item.column

    if "date" not in mapping:
        candidates = [
            header for header, info in profile["columns"].items()
            if decisions[header]["status"] != "mapped" and info["date_fraction"] >= AUTO_CONFIRM
        ]
        if len(candidates) == 1:
            header = candidates[0]
            mapping["date"] = header
            decisions[header].update(field="date", score=profile["columns"][header]["date_fraction"],
                                     source="value_profile", status="mapped",
                                     reason="The only consistently parseable unassigned date column.")

    for header, previous in (prior_samples or {}).items():
        field = previous["field"]
        if (header in decisions and decisions[header]["status"] != "mapped"
                and field not in mapping and previous["score"] >= AUTO_CONFIRM
                and compatible(field, profile["columns"][header])):
            mapping[field] = header
            decisions[header].update(
                field=field, score=previous["score"], source="model_samples", status="mapped",
                reason="Sample-assisted mapping retained for this unchanged dataset and model.",
            )

    unresolved = [header for header, item in decisions.items() if item["status"] != "mapped"]
    if semantic_mapper is not None and unresolved:
        choices = list(semantic_mapper(profile, unresolved, dict(mapping)))
        apply_choices(choices, profile, decisions, mapping, unresolved, "model_profile")
    if sample_mapper is not None:
        header, callback = sample_mapper
        if decisions[header]["status"] != "mapped":
            apply_choices(list(callback(profile, header, dict(mapping))), profile, decisions,
                          mapping, [header], "model_samples")

    fields, warnings, blocking = {}, [], []
    for header, decision in decisions.items():
        info = profile["columns"][header]
        accepted = decision["status"] == "mapped"
        semantic = decision["field"]
        if accepted:
            field = semantic
            role = "date" if field == "date" else "metric" if field in METRICS else "dimension"
        else:
            field = field_id(header)
            original = field
            suffix = 2
            while field in mapping:
                field = f"{original}_{suffix}"
                suffix += 1
            mapping[field] = header
            role = "identifier" if identifier_header(header) else "metric" if info["type"] == "numeric" else "dimension"
            if decision["status"] == "invalid_type" and semantic in METRICS | {"date"} and info["null_rate"] < 1:
                blocking.append(f"{header}: values could not be validated as {semantic}.")
            if semantic is not None or info["type"] == "empty":
                warnings.append(f"{header}: {decision['reason']} Retained as {field}.")
            elif header.casefold().startswith("col_"):
                warnings.append(f"{header}: semantic meaning is unverified; retained under its original name.")
        decision["key"] = field
        decision["role"] = role
        fields[field] = {
            "source": header, "role": role, "semantic": semantic if accepted else None,
            "aggregation": "mean" if semantic in {"utilization", "rate"} and accepted else "sum",
        }

    metrics = [field for field, info in fields.items() if info["role"] == "metric"]
    expected_frequency = None
    if "date" in mapping:
        dates = _dates(frame[mapping["date"]]).dropna().dt.normalize().drop_duplicates().sort_values()
        differences = dates.diff().dropna().dt.total_seconds().div(86400)
        if len(dates) >= 7 and differences.eq(1).mean() >= 0.8 and dates.dt.day_of_week.ge(5).any():
            expected_frequency = "day"
    return {
        "mapping": mapping, "columns": decisions, "fields": fields, "metrics": metrics,
        "unmapped_columns": [header for header, item in decisions.items() if item["status"] != "mapped"],
        "warnings": warnings, "blocking_issues": blocking, "ready": bool(metrics) and not blocking,
        "expected_frequency": expected_frequency,
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect and map CSV columns.")
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    print(json.dumps(resolve_columns(read_csv(args.csv)), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
