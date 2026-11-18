"""Ensure production CLIs can import from ``tools/`` (and sibling package dirs)."""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parent


def ensure_on_path(directory: Path | str) -> Path:
    """Insert ``directory`` at the front of ``sys.path`` at most once. Return it."""
    root = Path(directory).resolve()
    key = str(root)
    if key not in sys.path:
        sys.path.insert(0, key)
    return root


def ensure_tools_on_path() -> Path:
    """Insert ``tools/`` at the front of ``sys.path`` at most once. Return it."""
    return ensure_on_path(_TOOLS_ROOT)
