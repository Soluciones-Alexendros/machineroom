"""Shared Pi model allowlist.

``extensions/machineroom/model-scope.json`` is the only pattern list. A glob
matches ``provider/id`` or the bare id, and ``*`` does not cross ``/``. An exact
pattern matches one ``provider/id``. Callers reject anything else before spawn.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

COMPONENT = "model-scope"
SCOPE_NAME = Path("extensions") / "machineroom" / "model-scope.json"
_GLOB_CHARS = frozenset("*?[]")


class ModelScopeError(ValueError):
    """Structured model-scope failure: component + function + detail."""

    def __init__(self, function: str, detail: str) -> None:
        self.component = COMPONENT
        self.function = function
        self.detail = detail
        super().__init__(f"FAIL {COMPONENT} {function}: {detail}")


@dataclass(frozen=True)
class ModelScope:
    """Loaded allowlist."""

    default_model: str
    patterns: tuple[str, ...]


def scope_path() -> Path:
    """Return the scope file next to the catalog, not a caller-supplied path."""
    return Path(__file__).resolve().parents[2] / SCOPE_NAME


def load_scope(path: Path | None = None) -> ModelScope:
    """Load and validate the scope. Raises ``ModelScopeError`` on any problem."""
    function = "load_scope"
    target = path or scope_path()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ModelScopeError(function, f"unreadable model scope: {target}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ModelScopeError(function, f"invalid JSON in {target}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ModelScopeError(function, "model scope must be an object")
    default_model = str(raw.get("defaultModel", "")).strip()
    patterns_raw = raw.get("patterns")
    if not default_model or not isinstance(patterns_raw, list) or not patterns_raw:
        raise ModelScopeError(function, "model scope needs defaultModel and a non-empty patterns list")
    patterns: list[str] = []
    for item in patterns_raw:
        if not isinstance(item, str) or not item.strip():
            raise ModelScopeError(function, "model scope patterns must be non-empty strings")
        patterns.append(item.strip())
    scope = ModelScope(default_model, tuple(patterns))
    if not model_in_scope(default_model, scope):
        raise ModelScopeError(function, f"default model is outside the scope: {default_model}")
    return scope


def _is_glob(pattern: str) -> bool:
    return any(char in pattern for char in _GLOB_CHARS)


def _glob_regex(pattern: str) -> re.Pattern[str]:
    parts = ["[^/]*" if char == "*" else re.escape(char) for char in pattern]
    return re.compile("^" + "".join(parts) + "$", re.IGNORECASE)


def model_in_scope(reference: str, scope: ModelScope | None = None) -> bool:
    """Return whether one concrete ``provider/id`` is kept."""
    candidate = reference.strip()
    if not candidate or any(char.isspace() for char in candidate):
        return False
    if any(char in candidate for char in _GLOB_CHARS):
        return False
    slash = candidate.find("/")
    if slash <= 0 or slash == len(candidate) - 1:
        return False
    loaded = scope or load_scope()
    model_id = candidate[slash + 1 :]
    for pattern in loaded.patterns:
        if _is_glob(pattern):
            regex = _glob_regex(pattern)
            if regex.fullmatch(candidate) or regex.fullmatch(model_id):
                return True
        elif candidate.casefold() == pattern.casefold():
            return True
    return False


def resolve_pi_model(raw: str | None, scope: ModelScope | None = None) -> str:
    """Return the default or a kept model. Reject every other reference."""
    loaded = scope or load_scope()
    candidate = (raw or "").strip()
    if not candidate:
        return loaded.default_model
    if not model_in_scope(candidate, loaded):
        raise ModelScopeError("resolve_pi_model", f"model out of scope: {candidate}")
    return candidate
