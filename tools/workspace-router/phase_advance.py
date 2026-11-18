"""Phase advance and awaiting-agent resolution for status.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from status_io import (  # noqa: E402
    PHASE_INDEX,
    PHASES,
    STATUS_PATH_PARTS,
    STATUS_SCHEMA_VERSION,
    _ensure_tools_on_path,
    _utc_stamp,
    _with_status_lock,
    load_status,
)

def _bump_semver(version: str, kind: str) -> str:
    parts = version.strip().split(".")
    while len(parts) < STATUS_PATH_PARTS:
        parts.append("0")
    major, minor, patch = (int(parts[0]), int(parts[1]), int(parts[2]))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def bump_kind_for_phase(phase: str) -> str:
    if phase == "INTEGRATE":
        return "minor"
    return "patch"


def _assert_phase_transition(
    current: str,
    target: str,
    *,
    allow_restart: bool = False,
) -> None:
    """Explicit forward graph: same phase only for idempotent re-complete; +1 next.

    Retroceso/reinicio only when allow_restart=True (explicit reset operation).
    """
    if current not in PHASE_INDEX or target not in PHASE_INDEX:
        raise ValueError(f"unknown phase in transition {current!r} → {target!r}")
    cur_i, tgt_i = PHASE_INDEX[current], PHASE_INDEX[target]
    if tgt_i == cur_i:
        return  # same phase — idempotent re-complete handled by run_id dedup
    if tgt_i == cur_i + 1:
        return
    if allow_restart and tgt_i == 0 and cur_i == len(PHASES) - 1:
        # STATUS → DEFINE only as explicit restart
        return
    if tgt_i < cur_i:
        raise ValueError(f"phase regress {current} → {target} rejected; use explicit restart operation if authorized")
    raise ValueError(
        f"invalid phase jump {current} → {target}; "
        f"next allowed is {PHASES[cur_i + 1] if cur_i + 1 < len(PHASES) else current}"
    )


@dataclass(frozen=True)
class _AdvanceContext:
    """Everything a completion needs, resolved once."""

    root: Path
    phase: str
    skill: str
    checksum_spec: str
    note: str
    run_id: str
    target: str
    allow_restart: bool
    bump_product_version: bool
    expected_revision: int | None


def _stamp_awaiting(data: dict[str, Any], phase: str) -> dict[str, Any]:
    out = dict(data)
    out["awaiting_agent"] = True
    out["awaiting_phase"] = phase
    out["updated_at"] = _utc_stamp()
    return out


def _receipt_key(phase: str, run_id: str) -> str:
    return f"{phase}:{run_id}"


def _seen_completion(data: dict[str, Any], run_id: str, phase: str) -> bool:
    receipts = data.get("completion_receipts") or {}
    if isinstance(receipts, dict) and _receipt_key(phase, run_id) in receipts:
        return True
    # Legacy window still consulted
    completed = list(data.get("completed_run_ids") or [])
    return run_id in completed


def _validated_evidence(ctx: _AdvanceContext) -> dict[str, Any]:
    """Revalidate evidence UNDER lock so stale content cannot complete (H19)."""
    from execution.evidence import (
        load_evidence,
    )  # import opcional: requiere tools/ en sys.path

    evidence = load_evidence(
        ctx.root,
        ctx.run_id,
        revalidate_content=True,
        expected_phase=ctx.phase,
        expected_skill=ctx.skill or None,
        expected_target=ctx.target or None,
        for_complete=True,
    )
    if evidence.get("outcome") != "succeeded":
        raise ValueError("evidence outcome is not succeeded")
    return evidence


def _completion_entry(
    ctx: _AdvanceContext,
    progress: dict[str, Any],
    evidence: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    return {
        "advance": progress["advance"],
        "version": progress["product_version"],
        "state_revision": progress["state_revision"],
        "phase": ctx.phase,
        "skill": ctx.skill,
        "at": now,
        "note": ctx.note,
        "evidence_ok": True,
        "run_id": ctx.run_id,
        "work_digest": evidence.get("output_digest") or evidence.get("work_digest", ""),
    }


def _apply_completion(
    ctx: _AdvanceContext,
    data: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Return (state, idempotent_replay)."""
    out = dict(data)
    if _seen_completion(out, ctx.run_id, ctx.phase):
        return out, True
    if out.get("awaiting_agent"):
        raise ValueError("awaiting_agent must be resolved before complete")
    current = str(out.get("phase") or "DEFINE")
    _assert_phase_transition(current, ctx.phase, allow_restart=ctx.allow_restart)

    cur_rev = int(out.get("state_revision") or 0)
    if ctx.expected_revision is not None and ctx.expected_revision != cur_rev:
        raise ValueError(f"stale state_revision: expected {ctx.expected_revision}, have {cur_rev}")

    product_version = str(out.get("version") or "0.1.0")
    if ctx.bump_product_version:
        product_version = _bump_semver(product_version, bump_kind_for_phase(ctx.phase))
    state_revision = cur_rev + 1
    advance = int(out.get("advance") or 0) + 1
    now = _utc_stamp()
    progress = {
        "state_revision": state_revision,
        "advance": advance,
        "product_version": product_version,
    }

    history = list(out.get("history") or [])
    history.append(_completion_entry(ctx, progress, evidence, now))
    evidence_log = list(out.get("evidence_log") or [])
    evidence_log.append(
        {
            "state_revision": state_revision,
            "checksum_spec": ctx.checksum_spec or evidence.get("plan_digest", ""),
            "run_id": ctx.run_id,
            "at": now,
            "phase": ctx.phase,
        }
    )
    completed = list(out.get("completed_run_ids") or [])
    completed.append(ctx.run_id)
    receipts = dict(out.get("completion_receipts") or {})
    receipts[_receipt_key(ctx.phase, ctx.run_id)] = {
        "at": now,
        "state_revision": state_revision,
        "plan_digest": evidence.get("plan_digest", ""),
        "output_digest": evidence.get("output_digest", ""),
    }
    out.update(
        {
            "schema_version": STATUS_SCHEMA_VERSION,
            "version": product_version,
            "state_revision": state_revision,
            "phase": ctx.phase,
            "advance": advance,
            "last_skill": ctx.skill,
            "checksum_spec": ctx.checksum_spec or out.get("checksum_spec") or "",
            "updated_at": now,
            "history": history[-50:],
            "evidence_log": evidence_log,
            # Compact window for diagnostics; durable identity is receipts.
            "completed_run_ids": completed[-200:],
            "completion_receipts": receipts,
            "awaiting_agent": False,
        }
    )
    out.pop("awaiting_phase", None)
    return out, False


def _advance_once(ctx: _AdvanceContext) -> dict[str, Any]:
    evidence = _validated_evidence(ctx)
    data, idempotent = _apply_completion(ctx, load_status(ctx.root), evidence)
    if idempotent:
        data = dict(data)
        data["_idempotent_replay"] = True
    return data


def _advance_locked(ctx: _AdvanceContext) -> dict[str, Any]:
    replay: dict[str, bool] = {"idempotent": False}

    def _run(data: dict[str, Any]) -> dict[str, Any]:
        evidence = _validated_evidence(ctx)
        out, idempotent = _apply_completion(ctx, data, evidence)
        replay["idempotent"] = idempotent
        return out

    result = _with_status_lock(ctx.root, _run)
    if replay["idempotent"]:
        result = dict(result)
        result["_idempotent_replay"] = True
    return result


def advance_status(  # noqa: PLR0913  # API pública: keyword-only, espejo del contrato de estado
    repo: Path | str,
    *,
    phase: str,
    skill: str = "",
    checksum_spec: str = "",
    note: str = "",
    write: bool = True,
    bump_product_version: bool = False,
    evidence_ok: bool = False,
    run_id: str = "",
    allow_awaiting: bool = False,
    allow_restart: bool = False,
    expected_revision: int | None = None,
    target: str = "",
) -> dict[str, Any]:
    """Advance bookkeeping under a full read→validate→write lock.

    Completing a phase requires validated evidence bound to phase/skill/target.
    Repeating the same run_id is idempotent (no double advance).
    """
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}")

    root = Path(repo).resolve()

    if allow_awaiting and not evidence_ok:
        if not write:
            return _stamp_awaiting(load_status(root), phase)
        return _with_status_lock(root, lambda data: _stamp_awaiting(data, phase))

    if not evidence_ok:
        raise ValueError(
            "refusing status advance without evidence_ok=True "
            "(simulated/awaiting_agent/blocked must not complete a phase)"
        )
    if not run_id:
        raise ValueError("refusing status advance without validated run_id evidence")

    _ensure_tools_on_path()
    ctx = _AdvanceContext(
        root=root,
        phase=phase,
        skill=skill,
        checksum_spec=checksum_spec,
        note=note,
        run_id=run_id,
        target=target,
        allow_restart=allow_restart,
        bump_product_version=bump_product_version,
        expected_revision=expected_revision,
    )
    if not write:
        return _advance_once(ctx)
    return _advance_locked(ctx)


def resolve_awaiting_agent(  # noqa: PLR0913  # API pública: keyword-only
    repo: Path | str,
    *,
    run_id: str,
    phase: str,
    skill: str = "",
    target: str = "",
    write: bool = True,
) -> dict[str, Any]:
    """Clear awaiting_agent after validated evidence (H14/C11).

    Does not advance the phase by itself — call ``advance_status`` after resolve.
    Task-level closure uses ``complete_task`` (evidence + receipts); phase-level
    closure uses ``advance_status`` / CLI ``--complete``. Editing status.yaml
    manually is not required.
    """
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}")
    if not run_id:
        raise ValueError("run_id required to resolve awaiting_agent")

    root = Path(repo).resolve()
    _ensure_tools_on_path()
    from execution.evidence import (
        load_evidence,
    )  # import opcional: requiere tools/ en sys.path

    def _resolve(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)
        if not data.get("awaiting_agent"):
            data["_resolve_noop"] = True
            return data
        awaiting_phase = str(data.get("awaiting_phase") or phase)
        if awaiting_phase != phase:
            raise ValueError(f"awaiting_phase mismatch: status has {awaiting_phase}, got {phase}")
        # Validate evidence under lock
        evidence = load_evidence(
            root,
            run_id,
            revalidate_content=True,
            expected_phase=phase,
            expected_skill=skill or None,
            expected_target=target or None,
            for_complete=True,
        )
        if evidence.get("outcome") != "succeeded":
            raise ValueError("evidence outcome is not succeeded")
        now = _utc_stamp()
        data["awaiting_agent"] = False
        data.pop("awaiting_phase", None)
        data["updated_at"] = now
        data["last_resolve_run_id"] = run_id
        return data

    if not write:
        return _resolve(load_status(root))
    return _with_status_lock(root, _resolve)
