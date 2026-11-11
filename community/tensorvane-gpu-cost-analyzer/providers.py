"""Provider-specific discovery and structured text generation."""

import json
import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import quote, urlsplit

import httpx
from openai import OpenAI, OpenAIError
from pydantic import ValidationError


PROVIDERS = {
    "openai": ("OpenAI", "https://api.openai.com/v1"),
    "anthropic": ("Anthropic / Claude", "https://api.anthropic.com/v1"),
    "gemini": ("Google Gemini", "https://generativelanguage.googleapis.com/v1beta"),
    "compatible": ("OpenAI-compatible", ""),
}
MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,199}")


class ProviderError(RuntimeError):
    """An inference or discovery request failed."""


@dataclass(frozen=True)
class Connection:
    provider: str
    endpoint: str
    model: str
    key: str = field(repr=False)

    @property
    def destination(self):
        name = PROVIDERS[self.provider][0]
        return f"{name} ({self.endpoint})" if self.provider == "compatible" else name


def endpoint_for(provider, value=""):
    if provider not in PROVIDERS:
        raise ValueError("Choose a supported provider.")
    if provider != "compatible":
        return PROVIDERS[provider][1]
    try:
        url = urlsplit(value.strip())
        port = url.port
    except ValueError as exc:
        raise ValueError("Enter a valid base URL.") from exc
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not url.hostname or url.username is not None or url.password is not None
            or url.query or url.fragment or "\\" in value or any(char.isspace() for char in value.strip())
            or not (url.scheme == "https" or (url.scheme == "http" and local))
            or port == 0):
        raise ValueError("Use an HTTPS base URL, or HTTP on localhost, without credentials or query parameters.")
    return value.strip().rstrip("/")


def headers(connection):
    if connection.provider == "anthropic":
        return {"x-api-key": connection.key, "anthropic-version": "2023-06-01"}
    if connection.provider == "gemini":
        return {"x-goog-api-key": connection.key}
    return {"Authorization": f"Bearer {connection.key}"} if connection.key else {}


def request_json(connection, method, path, **kwargs):
    try:
        response = httpx.request(
            method, connection.endpoint + path, headers=headers(connection),
            timeout=httpx.Timeout(90, connect=10), follow_redirects=False, **kwargs,
        )
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise ValueError("Invalid response")
        return value
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code in {401, 403}:
            raise ProviderError("The provider rejected the API key or denied access.") from exc
        if code == 429:
            raise ProviderError("The provider rate limit or quota was reached.") from exc
        raise ProviderError(f"The provider returned HTTP {code}. Check the endpoint and model compatibility.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise ProviderError("Could not read a response from the configured provider.") from exc


def discover(connection):
    models = set()
    params = {}
    for _ in range(10):
        response = request_json(connection, "GET", "/models", params=params)
        if connection.provider == "gemini":
            items = response.get("models", [])
            if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
                raise ProviderError("The provider returned an invalid model catalog.")
            for item in items:
                if "generateContent" in item.get("supportedGenerationMethods", []):
                    models.add(item.get("name", "").removeprefix("models/"))
            cursor = response.get("nextPageToken")
            params = {"pageToken": cursor}
        else:
            items = response.get("data", [])
            if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
                raise ProviderError("The provider returned an invalid model catalog.")
            for item in items:
                model = item.get("id", "")
                if not isinstance(model, str):
                    continue
                shutdown = item.get("shutdown_date")
                if connection.provider == "openai" and (
                    (isinstance(shutdown, str) and shutdown <= date.today().isoformat()) or re.search(
                        r"embedding|moderation|image|dall-e|tts|whisper|audio|realtime|sora|transcri|codex|search", model
                    )
                ):
                    continue
                models.add(model)
            cursor = response.get("last_id") if connection.provider == "anthropic" and response.get("has_more") else None
            params = {"after_id": cursor}
        if not cursor:
            break
    return sorted(model for model in models
                  if isinstance(model, str) and model != connection.key and MODEL_ID.fullmatch(model))


def generate(connection, schema, instructions, payload):
    content = json.dumps(payload, allow_nan=False)
    definition = schema.model_json_schema()
    try:
        if connection.provider == "openai":
            with httpx.Client(follow_redirects=False, timeout=90) as http:
                response = OpenAI(
                    api_key=connection.key, base_url=connection.endpoint,
                    http_client=http, timeout=90, max_retries=1,
                ).responses.parse(
                    model=connection.model, instructions=instructions, input=content,
                    text_format=schema, store=False,
                )
                if response.output_parsed is not None:
                    return response.output_parsed
                raise ProviderError("The model did not return a usable response.")
        if connection.provider == "anthropic":
            response = request_json(connection, "POST", "/messages", json={
                "model": connection.model, "max_tokens": 4096, "system": instructions,
                "messages": [{"role": "user", "content": content}],
                "output_config": {"format": {"type": "json_schema", "schema": definition}},
            })
            answer = "".join(item["text"] for item in response["content"] if item["type"] == "text")
        elif connection.provider == "gemini":
            path = "/models/" + quote(connection.model, safe="") + ":generateContent"
            response = request_json(connection, "POST", path, json={
                "systemInstruction": {"parts": [{"text": instructions}]},
                "contents": [{"role": "user", "parts": [{"text": content}]}],
                "generationConfig": {
                    "responseMimeType": "application/json", "responseJsonSchema": definition,
                },
            })
            parts = response["candidates"][0]["content"]["parts"]
            answer = "".join(item.get("text", "") for item in parts if not item.get("thought"))
        else:
            response = request_json(connection, "POST", "/chat/completions", json={
                "model": connection.model,
                "messages": [
                    {"role": "system", "content": instructions + "\nReturn one JSON object matching this schema: " + json.dumps(definition)},
                    {"role": "user", "content": content},
                ],
            })
            answer = response["choices"][0]["message"]["content"]
        if not isinstance(answer, str):
            raise ValueError("Expected text")
        answer = answer.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", answer, flags=re.S | re.I)
        return schema.model_validate_json(fenced[1] if fenced else answer)
    except (ValidationError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProviderError("The selected model did not return valid structured JSON. Try another text model.") from exc
    except OpenAIError as exc:
        raise ProviderError("OpenAI could not complete the request. Check the key, quota, and selected model.") from exc

