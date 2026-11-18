"""Load and validate .machineroom/project.yaml.

Legacy ``.autoworkspace`` is not a silent fallback: call ``migrate_state`` first.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_TOOLS = Path(__file__).resolve().parents[1]
_boot_spec = importlib.util.spec_from_file_location(
    "mr_tools_bootstrap",
    _TOOLS / "_bootstrap.py",
)
if _boot_spec is None or _boot_spec.loader is None:
    raise RuntimeError(f"cannot load {_TOOLS / '_bootstrap.py'}")
_boot = importlib.util.module_from_spec(_boot_spec)
_boot_spec.loader.exec_module(_boot)
_boot.ensure_tools_on_path()

from state_paths import state_dir as _state_dir  # noqa: E402
from state_paths import state_file as _state_file  # noqa: E402

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: uv sync --frozen") from exc

PHASES = ("DEFINE", "SCHEMAS", "IMPLEMENT", "VALIDATE", "INTEGRATE", "STATUS")
PROFILES = ("P0", "P1", "P2")


class ProjectConfigError(ValueError):
    pass


def find_project_file(repo: Path) -> Path | None:
    candidate = _state_file(repo, "project.yaml")
    return candidate if candidate.is_file() else None


def load_project(repo: Path | str) -> dict[str, Any]:
    root = Path(repo).resolve()
    path = find_project_file(root)
    if path is None:
        raise ProjectConfigError(f"missing {_state_dir(root) / 'project.yaml'}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ProjectConfigError("project.yaml must be a mapping")
    validate_project(data)
    data["_root"] = str(root)
    data["_path"] = str(path)
    return data


def validate_project(data: dict[str, Any]) -> None:
    profile = data.get("profile", "P1")
    if profile not in PROFILES:
        raise ProjectConfigError(f"profile must be one of {PROFILES}, got {profile!r}")
    phases = data.get("phases") or list(PHASES)
    if not isinstance(phases, list) or not phases:
        raise ProjectConfigError("phases must be a non-empty list")
    for p in phases:
        if p not in PHASES:
            raise ProjectConfigError(f"unknown phase {p!r}; allowed {PHASES}")
    skills = data.get("skills") or {}
    if not isinstance(skills, dict):
        raise ProjectConfigError("skills must be a mapping")
    for key in ("enabled", "disabled"):
        val = skills.get(key, [])
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            raise ProjectConfigError(f"skills.{key} must be a list of strings")


def filter_skills(catalog: list[str], project: dict[str, Any]) -> list[str]:
    """Apply enabled/disabled against the real catalog.

    - enabled absent / null → default catalog
    - enabled: [] → allow none (blocks routing)
    - disabled always wins
    - names not in catalog are rejected (ProjectConfigError via validate or here)
    """
    catalog_set = set(catalog)
    skills = project.get("skills") or {}
    if "enabled" in skills and skills["enabled"] is not None:
        enabled = skills["enabled"]
        if not isinstance(enabled, list):
            raise ProjectConfigError("skills.enabled must be a list")
        unknown = [s for s in enabled if s not in catalog_set]
        if unknown:
            raise ProjectConfigError(f"skills.enabled not in catalog: {unknown}")
        base = list(enabled)
    else:
        base = list(catalog)
    disabled = skills.get("disabled") or []
    unknown_dis = [s for s in disabled if s not in catalog_set]
    if unknown_dis:
        raise ProjectConfigError(f"skills.disabled not in catalog: {unknown_dis}")
    disabled_set = set(disabled)
    return [s for s in base if s not in disabled_set]


def handoff_for_phase(project: dict[str, Any], phase: str) -> str | None:
    h = project.get("handoffs") or {}
    mapping = {
        "DEFINE": h.get("define", "plan-specification"),
        "SCHEMAS": h.get("continue", "project-status"),
        "IMPLEMENT": h.get("implement_back") or h.get("implement_front") or "role-back",
        "VALIDATE": h.get("validate", "plan-testing"),
        "INTEGRATE": (
            h.get("integrate_release") or h.get("integrate_publish") or h.get("integrate_hooks") or "project-status"
        ),
        "STATUS": h.get("continue", "project-status"),
    }
    return mapping.get(phase)


# Skills removed or renamed in 9.0.0. A project.yaml that still names them routes
# nowhere, so the router reports the exact replacement instead of failing silently.
HANDOFF_MIGRATIONS: dict[str, str] = {
    "plan-continue": "project-status",
    "project-audit": "project-status",
    "project-publish": "project-status",
    "plan-validators": "plan-testing",
    "project-libraries": "role-linux",
    "role-design": "",
}


def stale_handoffs(project: dict[str, Any], catalog: list[str]) -> list[dict[str, str]]:
    """Return handoff entries that no longer resolve, with the documented replacement."""
    known = set(catalog)
    handoffs = project.get("handoffs") or {}
    if not isinstance(handoffs, dict):
        return []
    findings: list[dict[str, str]] = []
    for key, raw in sorted(handoffs.items()):
        if not isinstance(raw, str) or not raw:
            continue
        if raw in known:
            continue
        findings.append(
            {
                "key": str(key),
                "skill": raw,
                "replacement": HANDOFF_MIGRATIONS.get(raw, ""),
            }
        )
    return findings
