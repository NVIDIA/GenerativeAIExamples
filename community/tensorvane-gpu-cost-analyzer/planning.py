"""Build local analytical plans and check requested breakdowns."""

import calendar
import re

from analysis_engine import Filter, Plan, calculation
from schema import ALIASES, account_dimensions, normalize_header


def clarify(message):
    return Plan(calculations=[], clarification=message)


def field_mentions(text, registry, role=None):
    normalized = normalize_header(text)
    matches = []
    for field, metadata in registry.items():
        if role and metadata["role"] != role:
            continue
        terms = {normalize_header(field), normalize_header(metadata["source"])}
        terms.update(normalize_header(alias) for alias in ALIASES.get(field, set()))
        # Units can be omitted when referring to a named metric.
        for term in list(terms):
            stripped = re.sub(r"\s+(tonnes|tons|kg|50kg)$", "", term)
            terms.add(stripped)
        for term in terms:
            if not term:
                continue
            for match in re.finditer(r"\b" + re.escape(term) + r"\b", normalized):
                matches.append((match.start(), match.end(), field))
    selected = []
    for start, end, field in sorted(matches, key=lambda item: item[1] - item[0], reverse=True):
        if not any(start < previous_end and end > previous_start for previous_start, previous_end, _ in selected):
            selected.append((start, end, field))
    return list(dict.fromkeys(field for _, _, field in sorted(selected)))


def grouping_request(question, registry):
    query = normalize_header(question)
    grain = next((grain for grain, adjective in (("day", "daily"), ("week", "weekly"), ("month", "monthly"))
                  if re.search(rf"\b({adjective}|by {grain}|per {grain}|which {grain})\b", query)), None)
    dimensions = {field: metadata for field, metadata in registry.items() if metadata["role"] in {"dimension", "identifier"}}
    groups = []
    clause = re.search(r"\b(?:by|per)\s+(.+)", question, re.I)
    if clause:
        requested = re.split(r"\b(?:in|during|for|where)\b", clause[1], maxsplit=1, flags=re.I)[0]
        requested = normalize_header(requested)
        if requested in {"account", "accounts", "billing account", "billing accounts"}:
            groups = account_dimensions(registry)
            if groups:
                return groups, grain, None
        groups = field_mentions(requested, dimensions)
        remainder = requested
        for field in groups:
            terms = {normalize_header(field), normalize_header(dimensions[field]["source"])}
            terms.update(normalize_header(alias) for alias in ALIASES.get(field, set()))
            for term in sorted(terms, key=len, reverse=True):
                remainder = re.sub(r"\b" + re.escape(term) + r"\b", " ", remainder)
        remainder = re.sub(r"\b(day|week|month|and|the|each)\b", " ", remainder)
        if remainder.strip():
            return [], grain, "No available column matches the requested breakdown: " + clause[1].rstrip("?.")
    elif re.search(r"\b(which|top|bottom|most|least|highest|lowest|each)\b", query):
        groups = field_mentions(question, dimensions)
        if re.search(r"\baccounts?\b(?!\s+(manager|id|name|code|number)\b)", query):
            groups = list(dict.fromkeys(account_dimensions(registry) + groups))
    return groups, grain, None


def default_plan(profile):
    registry = profile["fields"]
    metrics = [field for field, metadata in registry.items() if metadata["role"] == "metric"]
    priority = [field for field in ("cost", "usage", "utilization", "output_tonnes") if field in metrics]
    ordered = priority + [field for field in metrics if field not in priority]
    steps = [calculation(registry[field]["aggregation"], field) for field in ordered]
    accounts = account_dimensions(registry)
    if accounts and "usage" in metrics:
        steps.append(calculation("sum", "usage", group_by=accounts))
    for metric in ("cost", "usage", "utilization", "output_tonnes"):
        if metric not in registry:
            continue
        reduction = registry[metric]["aggregation"]
        for group in ("region", "entity"):
            if group in registry:
                steps.append(calculation("top_n", metric, group_by=[group], n=5, reduction=reduction))
        if "date" in registry:
            steps.append(calculation("week_over_week", metric, grain="week", reduction=reduction))
    return Plan(calculations=steps, clarification=None)


def calendar_filters(profile, question):
    query = re.sub(r'"[^"]*"', "", question.casefold())
    explicit = re.search(r"\b\d{4}(?:-\d{2}(?:-\d{2})?)?\b", query)
    months = [number for number in range(1, 13)
              if re.search(r"\b" + calendar.month_name[number].lower() + r"\b", query)]
    if len(months) > 1:
        return [], "Use one calendar period per local chat question."
    period = explicit.group() if explicit else None
    if months and (period is None or len(period) == 4):
        month = months[0]
        date_range = profile.get("date_range")
        if period is None and date_range:
            years = [year for year in range(int(date_range[0][:4]), int(date_range[1][:4]) + 1)
                     if date_range[0][:7] <= f"{year:04d}-{month:02d}" <= date_range[1][:7]]
            if len(years) == 1:
                period = str(years[0])
        if period is None:
            return [], "Include a year for the requested month."
        period = f"{period}-{month:02d}"
    return ([Filter(field="date", value=period)] if period else []), None


def equality_filters(profile, question):
    filters = []
    for match in re.finditer(r'([\w ]+)\s*=\s*"([^"]+)"', question):
        fields = field_mentions(match[1], profile["fields"])
        if not fields:
            return [], "The equality filter must name an available column."
        filters.append(Filter(field=fields[-1], value=match[2]))
    return filters, None


def local_question(profile, question):
    registry = profile["fields"]
    query = normalize_header(question)
    if re.search(r"\b(forecast|predict|correlat\w*|standard deviation|variance|compare|versus|between|excluding)\b", query):
        return clarify("Local chat supports reductions, rankings, equality filters, and weekly comparisons.")
    metrics = field_mentions(question, registry, role="metric")
    count = bool(re.search(r"\b(rows|records|entries)\b", query))
    if len(metrics) + int(count) != 1:
        return clarify("Name one available numeric metric, or ask for the number of rows.")
    metric = metrics[0] if metrics else None
    groups, grain, issue = grouping_request(question, registry)
    if issue:
        return clarify(issue)
    filters, issue = calendar_filters(profile, question)
    if issue:
        return clarify(issue)
    equalities, issue = equality_filters(profile, question)
    if issue:
        return clarify(issue)
    filters.extend(equalities)
    if not {item.field for item in filters} <= set(registry):
        return clarify("The question requires a date or filter column that is unavailable.")
    if re.search(r"\b(in|for|where|during)\b", query) and not filters:
        return clarify('Use a calendar period or an exact filter such as region="West".')
    reduction = registry[metric]["aggregation"] if metric else "sum"
    if re.search(r"\b(average|mean)\b", query):
        reduction = "mean"
    if re.search(r"week.over.week", question, re.I):
        if not metric:
            return clarify("Week-over-week comparison requires a numeric metric.")
        step = calculation("week_over_week", metric, group_by=groups, grain="week",
                           filters=filters, reduction=reduction)
    else:
        ranking = re.search(r"\b(top|bottom|most|least|highest|lowest)\b(?:\s+(\d+))?", query)
        if ranking and (groups or grain) and metric:
            op = "bottom_n" if ranking[1] in {"bottom", "least", "lowest"} else "top_n"
            step = calculation(op, metric, group_by=groups, grain=grain, filters=filters,
                               reduction=reduction, n=int(ranking[2] or 1))
        else:
            op = "count" if count else reduction
            for pattern, alternative in (
                (r"\bmedian\b", "median"), (r"\b(minimum|lowest)\b", "min"),
                (r"\b(maximum|highest)\b", "max"), (r"\b(unique|distinct)\b", "nunique"),
            ):
                if metric and re.search(pattern, query):
                    op = alternative
                    break
            step = calculation(op, metric, group_by=groups, grain=grain, filters=filters)
    if step.grain and "date" not in registry:
        return clarify("Time grouping requires an available date column.")
    return Plan(calculations=[step], clarification=None)


def check_question_plan(question, profile, plan):
    groups, grain, issue = grouping_request(question, profile["fields"])
    if issue:
        return issue
    if groups and any(not set(groups) <= set(step.group_by) for step in plan.calculations):
        return "The generated plan omitted a requested breakdown."
    if grain and any(step.grain != grain for step in plan.calculations):
        return "The generated plan omitted the requested time grouping."
    filters, issue = calendar_filters(profile, question)
    if issue:
        return issue
    equalities, issue = equality_filters(profile, question)
    if issue:
        return issue
    filters.extend(equalities)
    for predicate in filters:
        if any(predicate not in step.filters for step in plan.calculations):
            return "The generated plan omitted a requested filter."
    return None
