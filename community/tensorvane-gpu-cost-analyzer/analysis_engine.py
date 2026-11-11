"""Validate declarative plans and execute them against the inspected field registry."""

import math
import re
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict

from intake import IntakeError, _numbers
from schema import account_dimensions

Operation = Literal[
    "sum", "mean", "count", "min", "max", "median", "std", "nunique",
    "p25", "p75", "p90", "p95", "top_n", "bottom_n", "week_over_week",
]
Field = str
MAX_CALCULATIONS = 128


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Filter(StrictModel):
    field: str
    value: str


class Calculation(StrictModel):
    op: Operation
    metric: str | None
    group_by: list[str]
    grain: Literal["day", "week", "month"] | None
    filters: list[Filter]
    n: int | None
    reduction: Literal["sum", "mean"] | None


class Plan(StrictModel):
    calculations: list[Calculation]
    clarification: str | None


def calculation(op, metric=None, *, group_by=(), grain=None, filters=(), n=None, reduction=None):
    return Calculation(op=op, metric=metric, group_by=list(group_by), grain=grain,
                       filters=list(filters), n=n, reduction=reduction)


def validate(plan, frame):
    columns = set(frame.columns)
    numeric = set(frame.attrs.get("metrics", [
        field for field in frame if pd.api.types.is_numeric_dtype(frame[field])
    ]))
    if plan.clarification or not 1 <= len(plan.calculations) <= MAX_CALCULATIONS:
        raise IntakeError(f"A plan must contain between one and {MAX_CALCULATIONS} calculations.")
    for step in plan.calculations:
        groups = set(step.group_by)
        if len(groups) != len(step.group_by) or not groups <= columns - {"date"}:
            raise IntakeError("The plan references an unavailable or duplicate breakdown.")
        if step.metric is None and step.op != "count":
            raise IntakeError("This calculation requires a metric.")
        if step.metric is not None and step.metric not in columns:
            raise IntakeError("The plan references an unavailable metric.")
        if step.op not in {"count", "nunique"} and step.metric not in numeric:
            raise IntakeError("This operation requires a numeric metric.")
        if step.grain and "date" not in columns:
            raise IntakeError("Time grouping requires a date column.")
        ranked = step.op in {"top_n", "bottom_n"}
        comparison = step.op == "week_over_week"
        if ranked and (not (groups or step.grain) or not 1 <= (step.n or 0) <= 30):
            raise IntakeError("Ranking needs a breakdown and a limit from 1 to 30.")
        if comparison and step.grain != "week":
            raise IntakeError("Week-over-week comparison requires weekly grouping.")
        if (ranked or comparison) != (step.reduction is not None) or (not ranked and step.n is not None):
            raise IntakeError("The plan contains incompatible calculation parameters.")
        if len(step.filters) > 6:
            raise IntakeError("The plan has too many filters.")
        for predicate in step.filters:
            if predicate.field not in columns:
                raise IntakeError("The plan references an unavailable filter field.")
            if not 1 <= len(predicate.value) <= 200:
                raise IntakeError("Filter values must contain between 1 and 200 characters.")
            if predicate.field == "date":
                date_filter(predicate.value)


def date_filter(value):
    if not re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", value):
        raise IntakeError("Date filters must use YYYY, YYYY-MM, or YYYY-MM-DD.")
    try:
        return pd.Period(value, freq={4: "Y", 7: "M", 10: "D"}[len(value)])
    except ValueError as exc:
        raise IntakeError("The plan contains an invalid calendar date.") from exc


def aggregate(values, op):
    if op.startswith("p") and op[1:].isdigit():
        return values.quantile(int(op[1:]) / 100)
    if op == "sum":
        return values.sum(min_count=1)
    return getattr(values, op)()


def safe_number(value):
    if pd.isna(value) or not math.isfinite(value):
        return None
    return value.item() if hasattr(value, "item") else value


def execute(frame, plan):
    validate(plan, frame)
    accounts = account_dimensions(frame.attrs.get("fields", {}))
    results = []
    for step in plan.calculations:
        all_accounts = (
            bool(accounts) and step.op == "sum" and step.metric == "usage"
            and step.group_by == accounts and step.grain is None
        )
        result = execute_calculation(frame, step, row_limit=None if all_accounts else 100,
                                     sort_by_value=all_accounts)
        if all_accounts:
            result["account_usage"] = True
        if all_accounts and accounts == ["account_id"] and "account" in frame:
            names = frame.groupby("account_id", dropna=False)["account"].agg(account_name)
            labels = {None if pd.isna(key) else str(key): None if pd.isna(value) else str(value)
                      for key, value in names.items()}
            for row in result["rows"]:
                row["account"] = labels.get(row["account_id"])
            result["display_columns"] = ["account_id", "account"]
        results.append(result)
    return results


def account_name(values):
    names = values.dropna().unique()
    if len(names) == 1:
        return str(names[0])
    if len(names) > 1:
        return "Multiple account names"
    return None


def select_rows(frame, predicates):
    selected = frame
    for predicate in predicates:
        values = selected[predicate.field]
        if predicate.field == "date":
            period = date_filter(predicate.value)
            matches = values.dt.tz_localize(None).dt.to_period(period.freqstr).eq(period)
        elif pd.api.types.is_numeric_dtype(values):
            target = _numbers(pd.Series([predicate.value])).iloc[0]
            if pd.isna(target):
                raise IntakeError("A numeric filter requires a numeric value.")
            matches = values.eq(target)
        else:
            matches = values.str.casefold().eq(predicate.value.casefold())
        selected = selected.loc[matches.fillna(False)]
    return selected


def execute_calculation(frame, step, *, row_limit=100, sort_by_value=False):
    selected = select_rows(frame, step.filters)
    source_rows = len(selected)
    metadata = frame.attrs.get("fields", {}).get(step.metric, {})
    measure_grain = metadata.get("aggregation_grain", [])
    if measure_grain and step.op not in {"count", "nunique"}:
        for predicate in step.filters:
            if predicate.field not in measure_grain:
                distinct = frame.groupby(measure_grain, dropna=False)[predicate.field].nunique(dropna=False)
                if distinct.gt(1).any():
                    raise IntakeError(f"{step.metric} repeats at {', '.join(measure_grain)} level and cannot be filtered by {predicate.field}.")
        if step.group_by:
            distinct = selected.groupby(measure_grain, dropna=False)[step.group_by].nunique(dropna=False)
            if distinct.gt(1).any().any():
                raise IntakeError(f"{step.metric} repeats at {', '.join(measure_grain)} level and cannot be split by this breakdown.")
        selected = selected.drop_duplicates(measure_grain)
    measurement_rows = len(selected)

    groups = list(step.group_by)
    if step.grain:
        frequency = {"day": "D", "week": "W-SUN", "month": "M"}[step.grain]
        periods = selected["date"].dt.tz_localize(None).dt.to_period(frequency)
        selected = selected.assign(period=periods.dt.start_time)
        groups.append("period")
    metric = step.metric or "_row"
    if step.metric is None:
        selected = selected.assign(_row=1)
    reduction = step.reduction or step.op
    if groups:
        if selected.empty:
            table = pd.DataFrame(columns=[*groups, "value"])
        else:
            grouped = selected.groupby(groups, dropna=False, sort=True)
            table = aggregate(grouped[metric], reduction).rename("value").reset_index()
    else:
        table = pd.DataFrame({"value": [aggregate(selected[metric], reduction)]})

    if step.grain:
        if frame.attrs.get("daily_expected") and not selected.empty:
            days = selected.assign(_day=selected["date"].dt.normalize()).groupby(
                groups, dropna=False, sort=True
            )["_day"].nunique().rename("observed_days").reset_index()
            table = table.merge(days, on=groups, how="left")
            expected = table["period"].dt.days_in_month if step.grain == "month" else 7 if step.grain == "week" else 1
            table["missing_days"] = expected - table["observed_days"]
            table["complete"] = table["missing_days"].eq(0)
        else:
            table["complete"] = None
            table["missing_days"] = None

    if step.op in {"top_n", "bottom_n"}:
        table = table.dropna(subset=["value"]).sort_values(
            "value", ascending=step.op == "bottom_n", kind="stable"
        ).head(step.n)
    if step.op == "week_over_week":
        if step.group_by:
            by_group = table.groupby(step.group_by, dropna=False)
            previous = by_group["value"].shift()
            previous_period = by_group["period"].shift()
            previous_complete = by_group["complete"].shift()
        else:
            previous = table["value"].shift()
            previous_period = table["period"].shift()
            previous_complete = table["complete"].shift()
        adjacent = (pd.to_datetime(table["period"]) - pd.to_datetime(previous_period)).eq(pd.Timedelta(days=7))
        comparable = adjacent
        if frame.attrs.get("daily_expected"):
            comparable = comparable & table["complete"].eq(True) & previous_complete.eq(True)
        table["previous"] = previous.where(adjacent)
        table["change_pct"] = ((table["value"] - previous) / previous.abs() * 100).where(
            comparable & previous.ne(0)
        )

    if sort_by_value:
        table = table.sort_values("value", ascending=False, kind="stable", na_position="last")
    displayed = table if row_limit is None else table.head(row_limit)
    rows = []
    for row in displayed.to_dict("records"):
        labels = {
            field: None if pd.isna(row[field]) else str(row[field].date()) if field == "period" else str(row[field])
            for field in groups
        }
        rows.append(labels | {field: safe_number(value) for field, value in row.items() if field not in groups})
    return {
        "operation": step.op, "metric": step.metric or "rows", "groups": groups, "grain": step.grain,
        "filters": [item.model_dump() for item in step.filters],
        "matched_rows": source_rows, "measurement_rows": measurement_rows,
        "deduplicated_measurements": source_rows - measurement_rows,
        "aggregation_grain": measure_grain,
        "rows": rows, "truncated": len(displayed) < len(table),
        "group_count": len(table),
    }
