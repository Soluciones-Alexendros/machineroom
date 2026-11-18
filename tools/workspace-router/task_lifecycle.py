"""Plan/task lifecycle for .machineroom/status.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from status_io import (  # noqa: E402
    _ensure_tools_on_path,
    _utc_stamp,
    _with_status_lock,
    load_status,
)

if TYPE_CHECKING:
    from contracts.plan import PlanDocument


def _confined_plan_path(repo: Path, path: Path | str) -> tuple[Path, str]:
    root = repo.resolve()
    candidate = Path(path)
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"plan outside repo rejected: {path}") from exc
    if not resolved.is_file():
        raise ValueError(f"plan is not a file: {resolved}")
    return resolved, relative


def activate_plan(repo: Path | str, plan_path: Path | str) -> dict[str, Any]:
    """Select exactly one parsed plan and initialize its task states."""
    _ensure_tools_on_path()
    from contracts.plan import load_plan

    root = Path(repo).resolve()
    resolved, relative = _confined_plan_path(root, plan_path)
    document = load_plan(resolved)

    def activate(data: dict[str, Any]) -> dict[str, Any]:
        current = data.get("active_plan")
        if current:
            if current.get("path") == relative and current.get("digest") == document.digest:
                return data
            raise ValueError("another active plan or plan revision exists; explicit reset required")
        out = dict(data)
        out["active_plan"] = {
            "plan_id": document.plan_id,
            "path": relative,
            "base_revision": document.base_revision,
            "digest": document.digest,
        }
        out["plan_digest"] = document.digest
        out["tasks"] = {
            str(task["id"]): {
                "state": "pending",
                "depends_on": list(task["depends_on"]),
            }
            for task in document.tasks
        }
        out["phase"] = str(document.tasks[0]["phase"])
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        out["updated_at"] = _utc_stamp()
        return out

    return _with_status_lock(root, activate)


def load_active_plan(repo: Path | str) -> PlanDocument:
    """Load the selected plan and reject identity drift."""
    _ensure_tools_on_path()
    from contracts.plan import load_plan

    root = Path(repo).resolve()
    status = load_status(root)
    active = status.get("active_plan")
    if not isinstance(active, dict) or not active:
        raise ValueError("no active plan")
    resolved, relative = _confined_plan_path(root, str(active.get("path") or ""))
    document = load_plan(resolved)
    expected = {
        "plan_id": document.plan_id,
        "base_revision": document.base_revision,
        "digest": document.digest,
    }
    if any(active.get(key) != value for key, value in expected.items()) or relative != active.get("path"):
        raise ValueError("active plan identity or digest changed")
    if status.get("plan_digest") != document.digest:
        raise ValueError("active plan digest binding mismatch")
    return document


def _task_definition(document: Any, task_id: str) -> dict[str, Any]:
    for task in document.tasks:
        if task["id"] == task_id:
            return task
    raise ValueError(f"unknown task in active plan: {task_id}")


def _task_entry(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    tasks = data.get("tasks") or {}
    entry = tasks.get(task_id)
    if not isinstance(entry, dict):
        raise ValueError(f"task not initialized in status: {task_id}")
    return entry


def _dependencies_complete(data: dict[str, Any], task: dict[str, Any]) -> bool:
    return all(_task_entry(data, str(dependency)).get("state") == "succeeded" for dependency in task["depends_on"])


def _set_task_state(data: dict[str, Any], task_id: str, state: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(data)
    tasks = dict(out.get("tasks") or {})
    entry = dict(_task_entry(out, task_id))
    entry["state"] = state
    entry["updated_at"] = _utc_stamp()
    tasks[task_id] = entry
    out["tasks"] = tasks
    return out, entry


def ready_tasks(repo: Path | str) -> list[dict[str, Any]]:
    document = load_active_plan(repo)
    status = load_status(repo)
    return [
        task
        for task in document.tasks
        if _task_entry(status, str(task["id"])).get("state") in {"pending", "ready"}
        and _dependencies_complete(status, task)
    ]


def start_task(repo: Path | str, task_id: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    task = _task_definition(document, task_id)

    def start(data: dict[str, Any]) -> dict[str, Any]:
        entry = _task_entry(data, task_id)
        if not _dependencies_complete(data, task):
            raise ValueError(f"task dependencies not succeeded: {task_id}")
        if entry.get("state") not in {"pending", "ready"}:
            raise ValueError(f"task {task_id} cannot start from {entry.get('state')}")
        out, updated = _set_task_state(data, task_id, "running")
        updated["attempts"] = int(updated.get("attempts") or 0) + 1
        out["tasks"][task_id] = updated
        out["phase"] = str(task["phase"])
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        out["updated_at"] = _utc_stamp()
        return out

    return _with_status_lock(root, start)


def await_task(repo: Path | str, task_id: str, *, state: str = "awaiting_agent") -> dict[str, Any]:
    if state not in {"awaiting_agent", "awaiting_approval"}:
        raise ValueError(f"invalid awaiting state: {state}")
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def await_state(data: dict[str, Any]) -> dict[str, Any]:
        if _task_entry(data, task_id).get("state") != "running":
            raise ValueError(f"task {task_id} must be running before {state}")
        out, _entry = _set_task_state(data, task_id, state)
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, await_state)


def _apply_task_completion(  # noqa: PLR0913  # locked completion context
    data: dict[str, Any],
    *,
    root: Path,
    task_id: str,
    run_id: str,
    target: str,
    skill: str,
    replay: dict[str, bool],
) -> dict[str, Any]:
    """Pure-ish status mutation for one successful task (load_evidence under lock)."""
    from execution.evidence import load_evidence

    current_document = load_active_plan(root)
    current_task = _task_definition(current_document, task_id)
    evidence = load_evidence(
        root,
        run_id,
        revalidate_content=True,
        expected_phase=str(current_task["phase"]),
        expected_skill=skill,
        expected_target=target,
        expected_operation=str(current_task["operation"]),
        for_complete=True,
    )
    if evidence.get("plan_id") != current_document.plan_id:
        raise ValueError(f"evidence plan_id mismatch: {evidence.get('plan_id')}")
    if evidence.get("task_id") != task_id:
        raise ValueError(f"evidence task_id mismatch: {evidence.get('task_id')}")
    receipt_key = f"{task_id}:{run_id}"
    receipts = dict(data.get("task_receipts") or {})
    if receipt_key in receipts:
        replay["idempotent"] = True
        return data
    entry = _task_entry(data, task_id)
    if entry.get("state") != "running":
        raise ValueError(f"task {task_id} cannot complete from {entry.get('state')}")
    out, updated = _set_task_state(data, task_id, "succeeded")
    updated.update(
        {
            "run_id": run_id,
            "output_digest": evidence["output_digest"],
            "completed_at": _utc_stamp(),
        }
    )
    out["tasks"][task_id] = updated
    receipts[receipt_key] = {
        "plan_id": current_document.plan_id,
        "plan_digest": current_document.digest,
        "output_digest": evidence["output_digest"],
        "at": _utc_stamp(),
    }
    out["task_receipts"] = receipts
    out["state_revision"] = int(out.get("state_revision") or 0) + 1
    out["advance"] = int(out.get("advance") or 0) + 1
    out["last_skill"] = skill
    out["updated_at"] = _utc_stamp()
    remaining = [item for item in current_document.tasks if out["tasks"][str(item["id"])].get("state") != "succeeded"]
    out["phase"] = str(remaining[0]["phase"]) if remaining else "STATUS"
    history = list(out.get("history") or [])
    history.append(
        {
            "phase": current_task["phase"],
            "task_id": task_id,
            "plan_id": current_document.plan_id,
            "run_id": run_id,
            "state_revision": out["state_revision"],
            "at": out["updated_at"],
            "evidence_ok": True,
        }
    )
    out["history"] = history[-50:]
    return out


def complete_task(
    repo: Path | str,
    task_id: str,
    *,
    run_id: str,
    target: str,
) -> dict[str, Any]:
    """Task-level closure with evidence + receipts (not phase ``advance_status``)."""
    root = Path(repo).resolve()
    document = load_active_plan(root)
    task = _task_definition(document, task_id)
    _ensure_tools_on_path()
    from execution.registry import get_operation

    spec = get_operation(str(task["operation"]))
    replay = {"idempotent": False}

    def complete(data: dict[str, Any]) -> dict[str, Any]:
        return _apply_task_completion(
            data,
            root=root,
            task_id=task_id,
            run_id=run_id,
            target=target,
            skill=spec.skill,
            replay=replay,
        )

    result = _with_status_lock(root, complete)
    if replay["idempotent"]:
        result = dict(result)
        result["_idempotent_replay"] = True
    return result


def fail_task(repo: Path | str, task_id: str, *, detail: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def fail(data: dict[str, Any]) -> dict[str, Any]:
        state = _task_entry(data, task_id).get("state")
        if state not in {"running", "awaiting_agent", "awaiting_approval"}:
            raise ValueError(f"task {task_id} cannot fail from {state}")
        out, entry = _set_task_state(data, task_id, "failed")
        entry["detail"] = detail[:500]
        out["tasks"][task_id] = entry
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, fail)


def _interrupt_task(repo: Path | str, task_id: str, *, state: str, detail: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def interrupt(data: dict[str, Any]) -> dict[str, Any]:
        current = _task_entry(data, task_id).get("state")
        if current not in {"running", "awaiting_agent", "awaiting_approval"}:
            raise ValueError(f"task {task_id} cannot transition to {state} from {current}")
        out, entry = _set_task_state(data, task_id, state)
        entry["detail"] = detail[:500]
        out["tasks"][task_id] = entry
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, interrupt)


def block_task(repo: Path | str, task_id: str, *, detail: str) -> dict[str, Any]:
    return _interrupt_task(repo, task_id, state="blocked", detail=detail)


def cancel_task(repo: Path | str, task_id: str, *, detail: str) -> dict[str, Any]:
    return _interrupt_task(repo, task_id, state="cancelled", detail=detail)


def retry_task(repo: Path | str, task_id: str) -> dict[str, Any]:
    root = Path(repo).resolve()
    document = load_active_plan(root)
    _task_definition(document, task_id)

    def retry(data: dict[str, Any]) -> dict[str, Any]:
        state = _task_entry(data, task_id).get("state")
        if state not in {"failed", "blocked", "cancelled"}:
            raise ValueError(f"task {task_id} cannot retry from {state}")
        out, _entry = _set_task_state(data, task_id, "ready")
        out["state_revision"] = int(out.get("state_revision") or 0) + 1
        return out

    return _with_status_lock(root, retry)
