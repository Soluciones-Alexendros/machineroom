"""Shared loader for skill-index.json (phase router + intent router)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

_GENERATE: ModuleType | None = None


def get_generate_module() -> ModuleType:
    """Load tools/skill-index/generate.py once for callers and the CLI shim."""
    global _GENERATE
    if _GENERATE is not None:
        return _GENERATE
    gen_path = Path(__file__).resolve().with_name("generate.py")
    spec = importlib.util.spec_from_file_location("skill_index_generate", gen_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {gen_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _GENERATE = mod
    return mod


def _scan_skills_fallback(root: Path) -> dict[str, Any]:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return {"skills": []}
    names = sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    return {"skills": [{"name": n} for n in names]}


def _resolve_index_path(root: Path) -> Path | None:
    """Only ``<repo>/skill-index.json`` — never CWD (avoids foreign-index poison)."""
    path = root / "skill-index.json"
    return path if path.is_file() else None


def load_skill_index(repo: Path | str) -> dict[str, Any]:
    """Load ``<repo>/skill-index.json``; generate if missing; fail loud on errors.

    Does not consult ``./skill-index.json`` from CWD: a foreign working directory must
    not shadow the repo catalog used by workspace-router / skill-router. Generator /
    ``RuntimeError`` failures raise (fail-fast). Falls back to scanning ``skills/`` only when
    the index is still absent after a successful ensure, or when ensure is not applicable.
    """
    root = Path(repo).resolve()
    index_path = _resolve_index_path(root)
    if index_path is not None:
        return json.loads(index_path.read_text(encoding="utf-8"))

    generate = get_generate_module()
    generate.ensure_index(root)

    index_path = _resolve_index_path(root)
    if index_path is None:
        return _scan_skills_fallback(root)
    return json.loads(index_path.read_text(encoding="utf-8"))
