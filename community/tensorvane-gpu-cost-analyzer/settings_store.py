"""Persist model selections and keep API keys in the OS credential store."""

import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from uuid import uuid4

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

from intake import IntakeError
from providers import Connection, MODEL_ID, PROVIDERS, ProviderError, discover, endpoint_for


SETTINGS = Path(os.getenv("LOCALAPPDATA", Path.home() / ".config")) / "NV-A" / "models.json"
SERVICE = "NV-A model settings"
LOCK = RLock()


def vault():
    if sys.platform == "win32":
        from keyring.backends.Windows import WinVaultKeyring
        return WinVaultKeyring()
    return keyring.get_keyring()


def read_state():
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"providers": {}, "active": {"provider": "environment"} if environment() else None}
    except (OSError, ValueError) as exc:
        raise ProviderError("Could not read saved model settings.") from exc


def write_state(state):
    pending = None
    try:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=SETTINGS.parent, delete=False) as stream:
            pending = Path(stream.name)
            json.dump(state, stream, indent=2)
        pending.replace(SETTINGS)
    except OSError as exc:
        raise ProviderError("Could not save model settings.") from exc
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)


def environment():
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return Connection("openai", endpoint_for("openai"), os.getenv("OPENAI_MODEL") or "gpt-5-mini", key)
    return None


def secret(profile):
    slot = profile.get("credential")
    if slot is None:
        return ""
    try:
        key = vault().get_password(SERVICE, slot)
    except (KeyringError, OSError) as exc:
        raise ProviderError("Could not read the system credential store.") from exc
    if not key:
        raise ProviderError("The saved API key is unavailable. Reconnect the provider in Model settings.")
    return key


def connection_for(state):
    selection = state["active"]
    if selection is None:
        return None
    provider = selection["provider"]
    if provider == "environment":
        return environment()
    profile = state["providers"][provider]
    return Connection(provider, profile["endpoint"], selection["model"], secret(profile))


def selected_connection():
    with LOCK:
        return connection_for(read_state())


def public_state():
    with LOCK:
        state = read_state()
        selection = state["active"]
        active = None
        env = environment()
        if selection and selection["provider"] == "environment":
            if env:
                active = {"provider": "environment", "model": env.model, "destination": env.destination}
        elif selection:
            profile = state["providers"][selection["provider"]]
            connection = Connection(selection["provider"], profile["endpoint"], selection["model"], "")
            active = selection | {"destination": connection.destination}
        return {
            "active": active,
            "environment": {"model": env.model} if env else None,
            "providers": {
                provider: {
                    "endpoint": profile["endpoint"] if provider == "compatible" else "",
                    "models": profile["models"],
                    "has_key": bool(profile.get("credential")),
                }
                for provider, profile in state["providers"].items()
            },
        }


def delete_secret(slot):
    if slot:
        try:
            vault().delete_password(SERVICE, slot)
        except PasswordDeleteError:
            pass


def save_provider(data):
    provider = data.get("provider")
    endpoint = data.get("endpoint", "")
    new_key = data.get("key", "")
    manual = data.get("model", "")
    if not all(isinstance(value, str) for value in (provider, endpoint, new_key, manual)):
        raise IntakeError("Enter a provider, API key, and optional model ID.")
    if provider not in PROVIDERS:
        raise IntakeError("Choose a supported provider.")
    new_key = new_key.strip()
    manual = manual.strip()
    if len(new_key) > 1200 or any(not 33 <= ord(char) <= 126 for char in new_key):
        raise IntakeError("Enter a valid API key without spaces.")
    if manual and not MODEL_ID.fullmatch(manual):
        raise IntakeError("Enter a valid model ID.")
    if provider == "gemini":
        manual = manual.removeprefix("models/")
        if manual and not MODEL_ID.fullmatch(manual):
            raise IntakeError("Enter a valid Gemini model ID.")
    try:
        endpoint = endpoint_for(provider, endpoint)
    except ValueError as exc:
        raise IntakeError(str(exc)) from exc

    with LOCK:
        state = read_state()
        previous = state["providers"].get(provider)
        same_endpoint = previous and previous["endpoint"] == endpoint
        existing_slot = previous.get("credential") if same_endpoint else None
        key = new_key or (secret(previous) if existing_slot else "")
        if not key and provider != "compatible":
            raise IntakeError("Enter an API key for this provider.")
        try:
            models = discover(Connection(provider, endpoint, "", key))
        except ProviderError as exc:
            # Some compatible endpoints implement inference without a models catalog.
            if not manual or provider != "compatible" or "HTTP 404" not in str(exc):
                raise
            models = []
        manual_models = set(previous.get("manual_models", [])) if same_endpoint else set()
        if manual:
            manual_models.add(manual)
        models = sorted(set(models) | manual_models)
        if not models:
            raise IntakeError("No text models were listed. Enter a model ID manually.")

        slot = uuid4().hex if new_key else existing_slot
        try:
            if new_key:
                vault().set_password(SERVICE, slot, new_key)
            state["providers"][provider] = {
                "endpoint": endpoint, "models": models, "manual_models": sorted(manual_models),
                "credential": slot,
            }
            active = state["active"]
            if active and active["provider"] == provider and (not same_endpoint or active["model"] not in models):
                state["active"] = None
            try:
                write_state(state)
            except ProviderError:
                if new_key:
                    delete_secret(slot)
                raise
            old_slot = previous.get("credential") if previous else None
            if old_slot != slot:
                delete_secret(old_slot)
        except (KeyringError, OSError) as exc:
            raise ProviderError("Could not update the system credential store.") from exc
    return public_state()


def select_model(data):
    provider = data.get("provider")
    model = data.get("model")
    with LOCK:
        state = read_state()
        if provider is None:
            state["active"] = None
        elif provider == "environment" and environment():
            state["active"] = {"provider": provider}
        elif isinstance(provider, str) and provider in state["providers"]:
            profile = state["providers"][provider]
            if not isinstance(model, str) or model not in profile["models"]:
                raise IntakeError("Choose a saved model.")
            secret(profile)
            state["active"] = {"provider": provider, "model": model}
        else:
            raise IntakeError("Choose a saved provider.")
        write_state(state)
    return public_state()


def remove_provider(provider):
    with LOCK:
        state = read_state()
        profile = state["providers"].pop(provider, None)
        if profile is None:
            raise IntakeError("This provider is not saved.")
        if state["active"] and state["active"]["provider"] == provider:
            state["active"] = None
        slot = profile.get("credential")
        try:
            old_key = secret(profile) if slot else ""
        except ProviderError:
            old_key = ""
        try:
            delete_secret(slot)
            try:
                write_state(state)
            except ProviderError:
                if slot and old_key:
                    vault().set_password(SERVICE, slot, old_key)
                raise
        except (KeyringError, OSError) as exc:
            raise ProviderError("Could not remove the API key from the credential store.") from exc
    return public_state()

