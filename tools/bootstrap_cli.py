"""Compact bootstrap for tools/ CLI entry points (avoids repeating the importlib preamble)."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def boot(
    caller_file: str,
    *,
    tools_parents: int = 1,
    extra: tuple[Path | str, ...] = (),
) -> Path:
    """Load ``_bootstrap.py`` for the caller's ``tools/`` tree and put it on ``sys.path``.

    ``tools_parents`` is the ``Path.parents`` index from ``caller_file`` to ``tools/``
    (1 for ``tools/<pkg>/entry.py``). Optional ``extra`` directories are prepended too.
    """
    tools_dir = Path(caller_file).resolve().parents[tools_parents]
    boot_path = tools_dir / "_bootstrap.py"
    spec = importlib.util.spec_from_file_location("mr_tools_bootstrap", boot_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {boot_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ensure_tools_on_path()
    for directory in extra:
        mod.ensure_on_path(directory)
    return tools_dir
