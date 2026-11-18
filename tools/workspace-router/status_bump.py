"""Declarative status bump for .machineroom/status.yaml — transactional."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_BC = Path(__file__).resolve().parents[1] / "bootstrap_cli.py"
_spec = importlib.util.spec_from_file_location("mr_bootstrap_cli", _BC)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_BC}")
_bc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bc)
_bc.boot(__file__, extra=(Path(__file__).resolve().parent,))

from status_io import (  # noqa: E402
    PHASES,
    STATUS_SCHEMA_VERSION,
    load_status,
    migrate_status,
    status_path,
)
from task_lifecycle import (  # noqa: E402
    activate_plan,
    await_task,
    block_task,
    cancel_task,
    complete_task,
    fail_task,
    load_active_plan,
    ready_tasks,
    retry_task,
    start_task,
)
from phase_advance import (  # noqa: E402
    advance_status,
    bump_kind_for_phase,
    resolve_awaiting_agent,
)

__all__ = [
    "PHASES",
    "STATUS_SCHEMA_VERSION",
    "activate_plan",
    "advance_status",
    "await_task",
    "block_task",
    "bump_kind_for_phase",
    "cancel_task",
    "complete_task",
    "fail_task",
    "load_active_plan",
    "load_status",
    "migrate_status",
    "ready_tasks",
    "resolve_awaiting_agent",
    "retry_task",
    "start_task",
    "status_path",
]
