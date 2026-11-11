"""CSV parsing, column profiles, and deterministic data quality checks."""

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

from schema import (
    ALIASES, AUTO_CONFIRM, DIMENSION_FIELDS, METRICS, MIN_TYPE_FRACTION, RESERVED_FIELDS,
    identifier_header, is_nonnegative, normalize_header,
)


class IntakeError(ValueError):
    """An upload or plan needs correction."""


@dataclass(frozen=True)
class MappingSuggestion:
    column: str
    field: str
    confidence: float
    needs_confirmation: bool


@dataclass(frozen=True)
class QualitySummary:
    input_rows: int
    usable_rows: int
    duplicates_removed: int
    rows_with_missing_values: int
    rows_with_invalid_values: int
    missing_dates: tuple[str, ...]
    missing_values_by_column: dict
    invalid_values_by_column: dict
    invalid_data_rows: list
    missing_data_rows: list
    outlier_counts: dict
    outlier_data_rows: dict


def read_csv(path: Path, *, max_rows=None, max_columns=None):
    message = "Cannot read file. Please upload a CSV."
    if path.suffix.casefold() != ".csv":
        raise IntakeError(message)
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            sample = stream.read(65536)
            stream.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                separator = dialect.delimiter
            except csv.Error:
                separator = ","
            reader = csv.reader(stream, delimiter=separator, strict=True)
            headers = [header.strip() for header in next(reader, [])]
            if not headers:
                raise IntakeError(message)
            if any(not header for header in headers):
                raise IntakeError("The CSV must have a header for each column.")
            if len(set(headers)) != len(headers):
                raise IntakeError("The CSV contains duplicate column names.")
            if max_columns is not None and len(headers) > max_columns:
                raise IntakeError(f"Use a CSV with up to {max_columns:,} columns.")
            rows = []
            for row in reader:
                if not row:
                    continue
                if max_rows is not None and len(rows) >= max_rows:
                    raise IntakeError(f"Use a CSV with up to {max_rows:,} rows.")
                if len(row) != len(headers):
                    raise IntakeError(f"CSV record ending on line {reader.line_num} has the wrong number of fields.")
                rows.append(row)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise IntakeError(message) from exc
    if not rows:
        raise IntakeError(message)
    frame = pd.DataFrame(rows, columns=headers, dtype="string")
    frame.attrs["separator"] = separator
    frame.attrs["decimal"] = "," if separator == ";" else None
    return frame


def _values(series):
    values = series.astype("string").str.strip()
    return values.mask(values.eq(""))


def _numbers(series, decimal=None):
    values = _values(series).str.replace(r"[$€£]", "", regex=True)
    values = values.str.replace(r"(?i)\b(?:USD|EUR|GBP|PKR)\b", "", regex=True)
    values = values.str.replace(r"[\s\u00a0\u202f]", "", regex=True)
    values = values.str.replace(r"^\((.+)\)$", r"-\1", regex=True).str.removesuffix("%")
    comma_only = values.str.contains(",", regex=False, na=False) & ~values.str.contains(".", regex=False, na=False)
    decimal_comma = decimal == "," or bool(values.loc[comma_only].str.match(r"^[+-]?\d+,\d{1,2}$").any())

    def normalize(value):
        if pd.isna(value):
            return pd.NA
        if "," in value and "." in value:
            if value.rfind(",") > value.rfind("."):
                return value.replace(".", "").replace(",", ".")
            return value.replace(",", "")
        if "," in value:
            if decimal_comma and value.count(",") == 1:
                return value.replace(",", ".")
            if re.fullmatch(r"[+-]?\d{1,3}(?:,\d{3})+", value):
                return value.replace(",", "")
            return pd.NA
        return value

    numbers = pd.to_numeric(values.map(normalize), errors="coerce").astype("Float64")
    return numbers.where(np.isfinite(numbers))


def _dates(series):
    """Parse ISO and slash dates using column-wide evidence for date order."""
    values = _values(series)
    iso = values.where(values.str.match(r"^\d{4}-\d{2}-\d{2}(?:$|[T ])", na=False))
    result = pd.to_datetime(iso, format="ISO8601", errors="coerce", utc=True)
    slash = values.str.extract(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
    first = pd.to_numeric(slash[0], errors="coerce")
    second = pd.to_numeric(slash[1], errors="coerce")
    day_first = bool(first.gt(12).any())
    month_first = bool(second.gt(12).any())
    selected = slash[0].notna()
    if day_first and month_first:
        # Mixed locale evidence only permits slash dates with a unique interpretation.
        formats = [("%d/%m/%Y", selected & first.gt(12)), ("%m/%d/%Y", selected & second.gt(12))]
    elif day_first:
        formats = [("%d/%m/%Y", selected)]
    elif month_first:
        formats = [("%m/%d/%Y", selected)]
    else:
        formats = [("%d/%m/%Y", selected & first.eq(second))]
    for pattern, mask in formats:
        result.loc[mask] = pd.to_datetime(values.loc[mask], format=pattern, errors="coerce", utc=True)
    return result.where(result.dt.year.between(1, 9999))


def _shape(value):
    return "".join(
        "L" if char.isalpha() else "D" if char.isdecimal()
        else "S" if char.isspace() else "P" for char in value[:80]
    )


def column_profiles(frame):
    profiles = {}
    for header in frame.columns:
        values = _values(frame[header])
        present = values.dropna()
        numeric = _numbers(present, frame.attrs.get("decimal")).dropna()
        dates = _dates(present).dropna()
        fraction = len(numeric) / len(present) if len(present) else 0.0
        date_fraction = len(dates) / len(present) if len(present) else 0.0
        kind = "empty"
        if len(present):
            kind = "numeric" if fraction >= MIN_TYPE_FRACTION else "text"
            if date_fraction >= MIN_TYPE_FRACTION:
                kind = "date"
        profiles[header] = {
            "type": kind,
            "numeric_fraction": fraction,
            "null_rate": float(values.isna().mean()),
            "numeric_range": [float(numeric.min()), float(numeric.max())] if len(numeric) else None,
            "date_range": [dates.min().date().isoformat(), dates.max().date().isoformat()] if len(dates) else None,
            "date_fraction": date_fraction,
            "masked_value_shapes": [shape for shape, _ in Counter(_shape(value) for value in present).most_common(5)],
        }
    return {"row_count": len(frame), "columns": profiles}


def suggest_mappings(frame):
    candidates = []
    for header in frame.columns:
        normalized = normalize_header(header)
        scores = sorted((
            (max(SequenceMatcher(None, normalized, normalize_header(alias)).ratio() for alias in aliases), field)
            for field, aliases in ALIASES.items()
        ), reverse=True)
        score, field = scores[0]
        if score >= 0.75:
            candidates.append(MappingSuggestion(
                header, field, round(score, 3),
                score < AUTO_CONFIRM or (score < 1 and score - scores[1][0] < 0.1) or scores[1][0] == 1,
            ))
    return candidates


def mapping_samples(frame, column, *, confidence, consent=False):
    if not 0 <= confidence <= 1:
        raise IntakeError("Mapping confidence must be between zero and one.")
    if consent is not True or confidence >= AUTO_CONFIRM:
        return []
    values = _values(frame[column]).dropna()
    return values.head(min(5, max(0, len(values) - 1))).tolist()


def detect_outliers(frame, metrics):
    """Flag large upper-tail deviations per entity while retaining their values."""
    counts, positions = {}, {}
    context = [field for field in ("entity", "product", "gpu_type", "contract_type") if field in frame]
    group_fields = context[0] if len(context) == 1 else context
    groups = [group.index for _, group in frame.groupby(group_fields, dropna=False)] if context else [frame.index]
    for metric in metrics:
        flagged = []
        for index in groups:
            values = frame.loc[index, metric].dropna()
            if len(values) < 16:
                continue
            q1, q3 = values.quantile([0.25, 0.75])
            spread = q3 - q1
            if spread <= 0:
                continue
            flagged.extend(values.index[values.gt(q3 + 6 * spread)].tolist())
        counts[metric] = len(flagged)
        positions[metric] = sorted(int(index) for index in flagged)
    return counts, positions


def clean_data(frame, mapping, *, daily=False, field_metadata=None):
    if not isinstance(mapping, dict) or any(not isinstance(field, str) or not isinstance(header, str)
                                            for field, header in mapping.items()):
        raise IntakeError("A mapping must contain field names and CSV column names.")
    if RESERVED_FIELDS.intersection(mapping):
        raise IntakeError("The mapping contains a reserved execution field.")
    missing = set(mapping.values()) - set(frame.columns)
    if missing:
        raise IntakeError("Unknown CSV columns: " + ", ".join(sorted(missing)))
    if len(set(mapping.values())) != len(mapping):
        raise IntakeError("Each field needs a distinct CSV column.")
    if daily and "date" not in mapping:
        raise IntakeError("A date column is required to check for missing days.")

    profile = column_profiles(frame)
    metadata = {}
    for field, header in mapping.items():
        existing = (field_metadata or {}).get(field)
        if existing and existing["source"] == header:
            metadata[field] = dict(existing)
            continue
        role = "dimension"
        if field == "date":
            role = "date"
        elif field in DIMENSION_FIELDS:
            role = "dimension"
        elif field in METRICS or (
            profile["columns"][header]["type"] == "numeric" and not identifier_header(header)
        ):
            role = "metric"
        elif identifier_header(header):
            role = "identifier"
        metadata[field] = {"source": header, "role": role, "aggregation": "mean" if field in {"utilization", "rate"} else "sum"}

    metrics = [field for field, info in metadata.items() if info["role"] == "metric"]
    if not metrics:
        raise IntakeError("Automatic inspection found no compatible numeric metrics.")
    unique = frame.drop_duplicates()
    clean = pd.DataFrame(index=unique.index)
    missing_rows = pd.Series(False, index=unique.index)
    invalid_rows = pd.Series(False, index=unique.index)
    missing_by_column, invalid_by_column = {}, {}
    observed_days = pd.DatetimeIndex([])
    for field, header in mapping.items():
        values = _values(unique[header])
        clean[field] = values
        role = metadata[field]["role"]
        if role == "metric":
            converted = _numbers(values, frame.attrs.get("decimal"))
            if is_nonnegative(field, header):
                converted = converted.where(converted.ge(0))
            if field == "utilization":
                converted = converted.where(converted.le(100))
        elif role == "date":
            converted = _dates(values)
            observed_days = pd.DatetimeIndex(converted.dropna().dt.normalize().unique())
        else:
            continue
        clean[field] = converted
        blank = values.isna()
        invalid = values.notna() & converted.isna()
        missing_by_column[field] = int(blank.sum())
        invalid_by_column[field] = int(invalid.sum())
        missing_rows |= blank
        invalid_rows |= invalid

    if {"jobs_failed", "jobs_submitted"} <= set(clean.columns):
        failed_check = clean["jobs_failed"].gt(clean["jobs_submitted"]).fillna(False)
        invalid_rows |= failed_check
        invalid_by_column["jobs_failed"] += int(failed_check.sum())
    clean = clean.loc[~(missing_rows | invalid_rows)].copy()
    missing_dates = ()
    if daily and len(observed_days):
        expected = pd.date_range(observed_days.min(), observed_days.max(), freq="D", unit="s")
        missing_dates = tuple(expected.difference(observed_days).strftime("%Y-%m-%d"))

    if {"date", "entity"} <= set(clean.columns):
        for field in metrics:
            terms = normalize_header(mapping[field])
            if not (re.search(r"\binput\b", terms) or re.search(r"\b(machine|downtime) hours\b", terms)):
                continue
            grouped = clean.groupby(["date", "entity"], dropna=False)[field]
            sizes = grouped.size()
            repeated = sizes.gt(1)
            if repeated.any() and grouped.nunique().loc[repeated].eq(1).all():
                metadata[field]["aggregation_grain"] = ["date", "entity"]

    outlier_counts, outlier_positions = detect_outliers(clean, metrics)
    clean = clean.reset_index(drop=True)
    clean.attrs.update(
        fields=metadata, metrics=metrics, daily_expected=daily,
        observed_dates=sorted(str(day.date()) for day in observed_days),
        missing_dates=list(missing_dates),
    )
    summary = QualitySummary(
        input_rows=len(frame), usable_rows=len(clean),
        duplicates_removed=len(frame) - len(unique),
        rows_with_missing_values=int(missing_rows.sum()), rows_with_invalid_values=int(invalid_rows.sum()),
        missing_dates=missing_dates, missing_values_by_column=missing_by_column,
        invalid_values_by_column=invalid_by_column,
        invalid_data_rows=[int(index) for index in invalid_rows.index[invalid_rows]],
        missing_data_rows=[int(index) for index in missing_rows.index[missing_rows]],
        outlier_counts=outlier_counts, outlier_data_rows=outlier_positions,
    )
    return clean, summary


def quality_context(summary):
    return {key: value for key, value in summary.items() if not key.endswith("_data_rows")}


def main():
    from column_mapping import resolve_columns
    parser = argparse.ArgumentParser(description="Inspect an NV-A CSV upload.")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--map", action="append", default=[], metavar="FIELD=HEADER")
    parser.add_argument("--daily", action="store_true")
    args = parser.parse_args()
    try:
        frame = read_csv(args.csv)
        profile = column_profiles(frame)
        inspection = resolve_columns(frame, profile=profile)
        mapping = dict(inspection["mapping"])
        for entry in args.map:
            field, separator, header = entry.partition("=")
            if not separator or not field or not header:
                raise IntakeError("Mappings must use FIELD=HEADER.")
            mapping[field] = header
        result = {"profile": profile, "column_inspection": inspection, "mapping": mapping}
        if inspection["ready"] or args.map:
            _, quality = clean_data(frame, mapping, daily=args.daily, field_metadata=inspection["fields"])
            result["quality"] = asdict(quality)
    except IntakeError as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
