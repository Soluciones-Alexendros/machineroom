"""Importable facade for ``tools/skill-index/load.py`` (hyphenated directory)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_PATH = Path(__file__).resolve().parent / "skill-index" / "load.py"
_spec = importlib.util.spec_from_file_location("skill_index_load_impl", _PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_PATH}")
_mod: ModuleType = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

get_generate_module = _mod.get_generate_module
load_skill_index = _mod.load_skill_index
