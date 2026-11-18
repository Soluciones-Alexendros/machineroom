"""Status.yaml I/O helpers shared by lifecycle and phase advance (no cycle)."""

from __future__ import annotations

import fcntl
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from state_paths import state_file as _state_file

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: uv sync --frozen") from exc

STATUS_PATH_PARTS = 3
STATUS_SCHEMA_VERSION = 2
PHASES = ("DEFINE", "SCHEMAS", "IMPLEMENT", "VALIDATE", "INTEGRATE", "STATUS")
PHASE_INDEX = {p: i for i, p in enumerate(PHASES)}


def status_path(repo: Path) -> Path:
    root = Path(repo).resolve()
    return _state_file(root, "status.yaml")


def _default_status() -> dict[str, Any]:
    return {
        "schema_version": STATUS_SCHEMA_VERSION,
        "version": "0.1.0",
        "phase": "DEFINE",
        "advance": 0,
        "last_skill": "",
        "checksum_spec": "",
        "updated_at": "",
        "state_revision": 0,
        "history": [],
        "completed_run_ids": [],
        "active_plan": None,
        "plan_digest": "",
        "tasks": {},
    }


def _migrate_status_data(data: dict[str, Any]) -> dict[str, Any]:
    version = data.get("schema_version", 1)
    if version not in (1, STATUS_SCHEMA_VERSION):
        raise ValueError(f"unsupported status schema_version: {version}")
    migrated = _default_status()
    migrated.update(data)
    migrated["schema_version"] = STATUS_SCHEMA_VERSION
    migrated.setdefault("active_plan", None)
    migrated.setdefault("plan_digest", "")
    migrated.setdefault("tasks", {})
    return migrated


def load_status(repo: Path | str) -> dict[str, Any]:
    path = status_path(Path(repo))
    if not path.is_file():
        return _default_status()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("status.yaml must be a mapping")
    return _migrate_status_data(data)


def migrate_status(repo: Path | str, *, write: bool = True) -> dict[str, Any]:
    """Explicitly persist the current status schema without selecting a plan."""
    root = Path(repo).resolve()
    if not write:
        return load_status(root)
    return _with_status_lock(root, lambda data: data)


def _with_status_lock(root: Path, fn: Callable[[dict[str, Any]], dict[str, Any] | None]):
    """Acquire exclusive lock, load status, run fn(data) -> data, write, release."""
    path = status_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with open(lock_path, "a+", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            if path.is_file():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if not isinstance(data, dict):
                    raise ValueError("status.yaml must be a mapping")
            else:
                data = _default_status()
            data = _migrate_status_data(data)
            new_data = fn(data)
            if new_data is None:
                return data
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(
                yaml.safe_dump(new_data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            os.replace(tmp, path)
            return new_data
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Legacy helper — prefer _with_status_lock for transactional updates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(lock_path, "a+", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            tmp.write_text(
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            os.replace(tmp, path)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_tools_on_path() -> None:
    from _bootstrap import ensure_tools_on_path  # noqa: PLC0415

    ensure_tools_on_path()
