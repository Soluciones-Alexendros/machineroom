#!/usr/bin/env python3
"""Shim. The generator lives in tools/skill-index/generate.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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

from skill_index_load import get_generate_module  # noqa: E402

_gen = get_generate_module()
build_index = _gen.build_index
main = _gen.main


if __name__ == "__main__":
    raise SystemExit(main())
