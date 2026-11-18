"""Perf budget for skill-router and workspace-router route() (stdlib + pytest)."""

from __future__ import annotations

import importlib.util
import statistics
import time
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
SKILL_ROUTE = ROOT / "tools" / "skill-router" / "route.py"
WORKSPACE_ROUTE = ROOT / "tools" / "workspace-router" / "run.py"

# Generous ceiling in seconds: catches catastrophic regressions without CI flake.
PERF_CEILING_SECONDS = 5.0
RUNS = 5
PROMPT = "audita la salud del sistema"


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _scaffold_repo(repo: Path) -> None:
    """Minimal read-only .machineroom for workspace-router route(DEFINE)."""
    state = repo / ".machineroom"
    state.mkdir()
    (state / "project.yaml").write_text(
        "schema_version: 1\n"
        "name: perf-budget\n"
        "profile: P1\n"
        "phases: [DEFINE]\n"
        "handoffs:\n"
        "  define: plan-specification\n",
        encoding="utf-8",
    )


def _timed_routes(skill_mod: ModuleType, workspace_mod: ModuleType, repo: Path) -> float:
    started = time.perf_counter()
    skill_mod.route(PROMPT, top=3)
    workspace_mod.route(repo, "DEFINE", bump=False, note="")
    return time.perf_counter() - started


def test_route_median_under_perf_ceiling(tmp_path: Path) -> None:
    skill_mod = _load(SKILL_ROUTE, "skill_route_perf")
    workspace_mod = _load(WORKSPACE_ROUTE, "workspace_route_perf")
    _scaffold_repo(tmp_path)

    samples = [_timed_routes(skill_mod, workspace_mod, tmp_path) for _ in range(RUNS)]
    median = statistics.median(samples)
    assert median <= PERF_CEILING_SECONDS, (
        f"route() median {median:.3f}s exceeds ceiling {PERF_CEILING_SECONDS}s (samples={samples!r})"
    )
