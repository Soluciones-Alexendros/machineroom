"""Project state directory (``.machineroom``).

D3/H2: new projects use ``.machineroom``. The silent ``.autoworkspace`` fallback
was announced for removal in 9.0.0 and is removed in 9.2.0. Call
``migrate_state`` (dry-run supported) to rename a legacy directory.

Failure modes (``StateDirError``, fields ``component``/``function``/``detail``):

- ``state_dir``: only the legacy directory is present (use ``migrate_state``).
- ``migrate_state``: both directories present, or the legacy path is a symlink,
  or the move fails. Nothing is deleted on failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.naming import LEGACY_PROJECT_DIRNAME, PROJECT_DIRNAME
from structured_failure import StructuredFailure

DEPRECATION_WINDOW = "8.x"
REMOVAL_VERSION = "9.2.0"
ANNOUNCED_REMOVAL = "9.0.0"


class StateDirError(StructuredFailure):
    """Structured state-directory failure: component + function + detail."""


def format_state_failure(component: str, function: str, detail: str) -> str:
    return f"FAIL {component} {function}: {detail}"


def state_dir(repo: Path | str, *, warn: bool = True) -> Path:
    """Return the ``.machineroom`` state directory for ``repo``.

    The path is not created. When only the legacy ``.autoworkspace`` directory
    exists, raise ``StateDirError`` naming ``migrate_state``. ``warn`` is kept
    for call-site compatibility and ignored.
    """
    del warn  # API compatibility; fallback no longer warns
    root = Path(repo).resolve()
    current = root / PROJECT_DIRNAME
    if current.is_dir():
        return current
    legacy = root / LEGACY_PROJECT_DIRNAME
    if legacy.is_dir():
        raise StateDirError(
            "state",
            "state_dir",
            f"legacy state at {legacy}; call migrate_state "
            f"(fallback removed in {REMOVAL_VERSION}, announced {ANNOUNCED_REMOVAL})",
        )
    return current


def state_file(repo: Path | str, *parts: str, warn: bool = True) -> Path:
    """Return ``<state_dir>/<parts>`` without creating anything."""
    return state_dir(repo, warn=warn).joinpath(*parts)


def migrate_state(repo: Path | str, *, dry_run: bool = False) -> dict[str, Any]:
    """Move ``.autoworkspace`` to ``.machineroom`` once.

    Returns ``{"migrated", "from", "to", "detail"}``. Raises ``StateDirError``
    when both directories exist, when the legacy path is a symlink, or when the
    move fails; in every failure the legacy directory stays in place.
    """
    root = Path(repo).resolve()
    target = root / PROJECT_DIRNAME
    legacy = root / LEGACY_PROJECT_DIRNAME
    if target.exists() or target.is_symlink():
        if legacy.exists() or legacy.is_symlink():
            raise StateDirError(
                "state",
                "migrate_state",
                f"two state directories present: {legacy} and {target}; remove one before migrating",
            )
        return {
            "migrated": False,
            "from": str(legacy),
            "to": str(target),
            "detail": "already migrated",
        }
    if not legacy.exists() and not legacy.is_symlink():
        return {
            "migrated": False,
            "from": str(legacy),
            "to": str(target),
            "detail": "no legacy state",
        }
    if legacy.is_symlink():
        raise StateDirError("state", "migrate_state", f"legacy state must be a real directory: {legacy}")
    if dry_run:
        return {
            "migrated": False,
            "from": str(legacy),
            "to": str(target),
            "detail": "dry-run",
        }
    try:
        legacy.rename(target)
    except OSError as exc:
        raise StateDirError("state", "migrate_state", f"cannot move {legacy} to {target}: {exc}") from exc
    return {
        "migrated": True,
        "from": str(legacy),
        "to": str(target),
        "detail": "migrated legacy state",
    }


def excluded_prefixes() -> tuple[str, ...]:
    """Posix prefixes excluded from content identity (current and legacy names)."""
    prefixes: list[str] = []
    for name in (PROJECT_DIRNAME, LEGACY_PROJECT_DIRNAME):
        prefixes.extend(
            (
                f"{name}/evidence/",
                f"{name}/status.yaml",
                f"{name}/status.yaml.lock",
                f"{name}/status.yaml.tmp",
                f"{name}/journal/",
                f"{name}/diary/",
                f"{name}/runs/",
            )
        )
    return tuple(prefixes)
