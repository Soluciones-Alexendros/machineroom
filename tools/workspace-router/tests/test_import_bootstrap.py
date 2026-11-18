"""tools/_bootstrap.ensure_tools_on_path is idempotent."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOOTSTRAP = ROOT / "tools" / "_bootstrap.py"


def _load_bootstrap():
    spec = importlib.util.spec_from_file_location("mr_tools_bootstrap", BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ensure_tools_on_path_idempotent() -> None:
    mod = _load_bootstrap()
    tools = str(ROOT / "tools")
    while tools in sys.path:
        sys.path.remove(tools)
    first = mod.ensure_tools_on_path()
    second = mod.ensure_tools_on_path()
    assert first == second == ROOT / "tools"
    assert sys.path.count(tools) == 1


def test_ensure_on_path_idempotent(tmp_path: Path) -> None:
    mod = _load_bootstrap()
    key = str(tmp_path.resolve())
    while key in sys.path:
        sys.path.remove(key)
    first = mod.ensure_on_path(tmp_path)
    second = mod.ensure_on_path(tmp_path)
    assert first == second == tmp_path.resolve()
    assert sys.path.count(key) == 1
