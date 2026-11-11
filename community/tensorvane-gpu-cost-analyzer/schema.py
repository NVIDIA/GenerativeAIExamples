"""Field names and units recognized by the deterministic column inspector."""

import re
import unicodedata

ALIASES = {
    "cost": {"cost", "price", "spend", "spent", "bill", "amount", "total cost", "total spend",
             "monto", "importe", "wheat cost"},
    "usage": {"usage", "used", "consumption", "hours", "hrs", "gpu hours", "gpu hrs", "gpu usage", "usage hours", "horas gpu"},
    "utilization": {"utilization", "utilisation", "util", "avg utilization", "average utilization",
                    "gpu utilization", "utilizacion"},
    "date": {"date", "day", "timestamp", "recorded at", "event date", "usage date", "production date", "fecha"},
    "entity": {"entity", "partner", "client", "client name", "customer", "customer name",
               "partner name", "mill name", "mill", "cliente"},
    "account": {"account", "account name", "acct", "acct name", "billing account", "billing account name", "customer account"},
    "account_id": {"account id", "account number", "account no", "account code", "account identifier",
                   "acct id", "acct no", "acct number", "billing account id", "billing account number"},
    "region": {"region", "location", "geography", "zone", "area", "city", "ciudad"},
    "cluster_id": {"cluster id", "cluster", "cluster name", "cluster identifier"},
    "gpu_type": {"gpu type", "gpu model", "tipo gpu"},
    "contract_type": {"contract type", "plan", "contract", "contrato"},
    "gpus_allocated": {"gpus allocated", "gpus", "gpus asignadas"},
    "jobs_submitted": {"jobs submitted", "jobs", "trabajos"},
    "jobs_failed": {"jobs failed", "failed jobs", "failures", "trabajos fallidos"},
    "top_failure_reason": {"top failure reason", "main error", "error principal"},
    "rate": {"price per gpu hour", "rate", "tarifa"},
}
DIMENSION_FIELDS = {"entity", "account", "account_id", "region", "cluster_id", "gpu_type", "contract_type", "top_failure_reason"}
METRICS = set(ALIASES) - DIMENSION_FIELDS - {"date"}
NONNEGATIVE = METRICS - {"cost"}
AUTO_CONFIRM = 0.95
MIN_TYPE_FRACTION = 0.8
RESERVED_FIELDS = {"period", "_row"}

def account_dimensions(registry):
    for field in ("account_id", "account"):
        if field in registry:
            return [field]
    entity = registry.get("entity")
    if entity and normalize_header(entity["source"]) in {
        "partner", "partner name", "client", "client name", "customer", "customer name", "cliente",
    }:
        return ["entity"]
    return []


def normalize_header(header):
    header = re.sub(r"\b([A-Z]{2,})s\b", lambda match: match[1].lower() + "s", header)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", header)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))
    tokens = re.findall(r"[a-z0-9]+", text.casefold())
    return " ".join(token for token in tokens if token not in {"usd", "eur", "gbp", "pkr", "percent", "pct"})


def field_id(header):
    normalized = "".join(char for char in unicodedata.normalize("NFKD", header)
                         if not unicodedata.combining(char))
    key = re.sub(r"[^a-z0-9]+", "_", normalized.casefold()).strip("_") or "column"
    return "source__" + key if key in ALIASES or key in RESERVED_FIELDS else key


def identifier_header(header):
    return bool(re.search(r"(?:^|_)(?:id|identifier|code)(?:$|_)", field_id(header)))


def is_nonnegative(field, source):
    if field in NONNEGATIVE:
        return True
    return bool(re.search(r"\b(hours|hrs|tonnes|tons|bags|jobs|counts?)\b", normalize_header(source)))
