"""Local Flask application for the Pears Analyzer workspace."""

from collections import OrderedDict
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Lock

from flask import Flask, jsonify, request, render_template_string
from dotenv import load_dotenv
from werkzeug.exceptions import RequestEntityTooLarge

from analysis_engine import execute
from column_mapping import resolve_columns
from intake import (
    IntakeError, MappingSuggestion,
    clean_data, column_profiles, mapping_samples, quality_context, read_csv, suggest_mappings,
)
from model import map_columns, narrate, plan_analysis
from providers import ProviderError
from settings_store import public_state, remove_provider, save_provider, select_model, selected_connection


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
app = Flask(__name__, static_folder="web")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["TRUSTED_HOSTS"] = ["localhost", "127.0.0.1", "[::1]"]


@dataclass
class Dataset:
    name: str
    frame: object
    profile: dict
    suggestions: dict
    lock: Lock
    mapping_target: tuple[str, str] | None = None
    resolution: dict | None = None
    resolution_target: tuple | None = None


datasets = OrderedDict()
datasets_lock = Lock()


@app.errorhandler(IntakeError)
def intake_error(exc):
    return jsonify(error=str(exc)), 400


@app.errorhandler(ProviderError)
def provider_error(exc):
    return jsonify(error=str(exc)), 502


@app.errorhandler(RequestEntityTooLarge)
def too_large(_):
    return jsonify(error="Upload a CSV under 8 MB."), 413


@app.after_request
def protect_response(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )
    if request.path.startswith("/api/") or request.path == "/":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    assets = (ROOT / "web" / "app.js").read_bytes() + (ROOT / "web" / "styles.css").read_bytes()
    return render_template_string(
        (ROOT / "web" / "index.html").read_text(encoding="utf-8"),
        asset_version=sha256(assets).hexdigest()[:12],
    )


@app.get("/api/status")
def status():
    active = public_state()["active"]
    return jsonify(model=bool(active), active=active)


@app.before_request
def protect_model_settings():
    if request.path.startswith("/api/settings") and request.headers.get("X-NVA-Settings") != "1":
        return jsonify(error="Open Model settings from the workspace."), 403


@app.get("/api/settings")
def model_settings():
    return jsonify(public_state())


@app.post("/api/settings/providers")
def connect_provider():
    return jsonify(save_provider(body()))


@app.delete("/api/settings/providers/<provider>")
def disconnect_provider(provider):
    return jsonify(remove_provider(provider))


@app.post("/api/settings/selection")
def choose_model():
    return jsonify(select_model(body()))


def dataset():
    token = request.headers.get("X-Dataset", "")
    with datasets_lock:
        entry = datasets.get(token)
        if entry is not None:
            datasets.move_to_end(token)
    if entry is None:
        raise IntakeError("Upload a dataset or open the demo to continue.")
    return entry


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise IntakeError("A JSON object is required.")
    return data


def resolve_entry(entry, connection, *, force=False, samples=None):
    target = (
        connection.provider, connection.endpoint, connection.model,
        sha256(connection.key.encode()).hexdigest(),
    ) if connection else None
    if not force and entry.resolution is not None and entry.resolution_target == target:
        return
    mapper = None
    if connection:
        def mapper(profile, unresolved, known):
            return map_columns(connection, profile, unresolved, known_mapping=known)
    sample_mapper = None
    if samples is not None:
        column, values = samples
        def sample_callback(profile, header, known):
            return map_columns(connection, profile, [header], {header: values}, known_mapping=known)
        sample_mapper = (column, sample_callback)
    result = resolve_columns(
        entry.frame, profile=entry.profile, semantic_mapper=mapper, sample_mapper=sample_mapper,
        prior_samples={
            header: decision for header, decision in entry.resolution["columns"].items()
            if decision["source"] == "model_samples" and decision["status"] == "mapped"
        } if entry.resolution is not None and entry.resolution_target == target else None,
    )
    entry.resolution = result
    entry.resolution_target = target
    entry.mapping_target = (connection.destination, connection.model) if connection else None
    entry.suggestions = {
        header: MappingSuggestion(
            header, decision["field"], decision["score"], decision["status"] != "mapped",
        )
        for header, decision in result["columns"].items()
        if decision["field"] is not None
    }


def dataset_response(entry):
    columns = [
        {"header": header, "profile": profile, "suggestion": (
            asdict(entry.suggestions[header]) if header in entry.suggestions else None
        )}
        for header, profile in entry.profile["columns"].items()
    ]
    return dict(name=entry.name, rows=len(entry.frame), columns=columns,
                column_inspection=entry.resolution)


def register(frame, name):
    if len(frame.columns) > 100 or len(frame) > 100_000:
        raise IntakeError("Use a CSV with up to 100 columns and 100,000 rows.")
    entry = Dataset(name, frame, column_profiles(frame),
                    {item.column: item for item in suggest_mappings(frame)}, Lock())
    resolve_entry(entry, selected_connection())
    token = token_urlsafe(24)
    with datasets_lock:
        previous = request.headers.get("X-Dataset", "")
        datasets.pop(previous, None)
        datasets[token] = entry
        while len(datasets) > 8:
            datasets.popitem(last=False)
    return jsonify(dataset_response(entry) | {"token": token})


@app.post("/api/upload")
def upload():
    file = request.files.get("file")
    if not file or not file.filename or Path(file.filename).suffix.casefold() != ".csv":
        raise IntakeError("Cannot read file. Please upload a CSV.")
    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "upload.csv"
        file.save(path)
        frame = read_csv(path, max_rows=100_000, max_columns=100)
    return register(frame, Path(file.filename).name)


@app.post("/api/demo")
def demo():
    path = ROOT / "demo.csv"
    return register(read_csv(path), path.name)


@app.post("/api/columns")
def inspect_columns():
    entry = dataset()
    connection = selected_connection()
    with entry.lock:
        resolve_entry(entry, connection, force=True)
        return jsonify(dataset_response(entry))


@app.post("/api/map")
def model_mapping():
    entry = dataset()
    connection = selected_connection()
    if connection is None:
        raise IntakeError("Choose a model in Model settings to enable assisted mapping.")
    data = body()
    column = data.get("column")
    target = (connection.destination, connection.model)
    with entry.lock:
        if column is not None and (data.get("destination"), data.get("model")) != target:
            raise IntakeError("The selected model changed. Review the recipient before sharing samples.")
        unresolved = entry.resolution["unmapped_columns"] if entry.resolution else list(entry.frame.columns)
        if column is None:
            resolve_entry(entry, connection, force=True)
        else:
            if not isinstance(column, str) or column not in unresolved:
                raise IntakeError("Choose one unresolved CSV column.")
            if entry.mapping_target != target:
                raise IntakeError("Request profile-based suggestions before sharing samples.")
            suggestion = entry.suggestions.get(column)
            confidence = suggestion.confidence if suggestion else 0
            samples = mapping_samples(entry.frame, column, confidence=confidence,
                                      consent=data.get("consent") is True)
            if not samples:
                raise IntakeError("Samples require explicit consent, low confidence, and enough values.")
            resolve_entry(entry, connection, force=True, samples=(column, samples))
        return jsonify(dataset_response(entry))


@app.post("/api/analyze")
def analyze():
    entry = dataset()
    data = body()
    mapping = data.get("mapping")
    connection = selected_connection()
    with entry.lock:
        resolve_entry(entry, connection)
        inspection = dict(entry.resolution)
        if mapping is None:
            if inspection["blocking_issues"]:
                raise IntakeError("Column validation failed. " + " ".join(inspection["blocking_issues"]))
            mapping = dict(inspection["mapping"])
    if not isinstance(mapping, dict) or any(not isinstance(value, str) for value in mapping.values()):
        raise IntakeError("A column mapping override must be an object of field names and column names.")
    question = data.get("question")
    if question is not None and (not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000):
        raise IntakeError("Enter a question of up to 1,000 characters.")
    daily = data.get("daily", inspection["expected_frequency"] == "day")
    if not isinstance(daily, bool):
        raise IntakeError("The daily gap check must be true or false.")
    frame, summary = clean_data(entry.frame, mapping, daily=daily,
                                field_metadata=inspection["fields"])
    inspection["fields"] = frame.attrs["fields"]
    quality = asdict(summary)
    if frame.empty:
        return jsonify(quality=quality, results=[], summary="No usable rows remain after quality checks.",
                       plan=None, column_inspection=inspection)
    profile = column_profiles(frame.astype("string"))
    profile["quality"] = quality_context(quality)
    profile["fields"] = frame.attrs["fields"]
    if "date" in frame:
        profile["date_range"] = [
            frame["date"].min().date().isoformat(), frame["date"].max().date().isoformat()
        ]
    plan = plan_analysis(profile, question, frame.columns, connection)
    if plan.clarification:
        if plan.calculations:
            raise IntakeError("The planner returned conflicting instructions.")
        return jsonify(clarification=plan.clarification)
    results = execute(frame, plan)
    narrative = narrate(results, quality, question=question, connection=connection)
    if inspection["warnings"]:
        narrative += " Column detection notes: " + " ".join(inspection["warnings"])
    return jsonify(quality=quality, results=results, plan=plan.model_dump(), column_inspection=inspection,
                   summary=narrative)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

