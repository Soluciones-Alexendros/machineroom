"""Native Pi package discovery through the model-free RPC get_commands API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from execution.ops import OpResult  # noqa: E402
from execution.registry import OpSpec, get_operation  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402

from harness.base import Check, build_report, report_exit_code  # noqa: E402
from harness.model_scope import resolve_pi_model  # noqa: E402
from harness.policy import (
    ExecutionPolicy,
    assert_argv_policy,
    build_policy,
)
from harness.subprocess_run import (
    CancellableRun,
    run_cancellable_subprocess,
)


def response_commands(response: dict[str, Any]) -> list[dict[str, Any]]:
    if (
        response.get("type") != "response"
        or response.get("command") != "get_commands"
        or response.get("success") is not True
    ):
        raise ValueError("Pi get_commands response missing or unsuccessful")
    commands = response.get("data", {}).get("commands")
    if not isinstance(commands, list):
        raise ValueError("Pi get_commands commands must be a list")
    return [command for command in commands if isinstance(command, dict)]


def skill_commands(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for command in response_commands(response) if command.get("source") == "skill"]


class PiCallError(ValueError):
    """Structured Pi connection failure. Timeouts are not retryable."""

    def __init__(self, function: str, detail: str, *, retryable: bool) -> None:
        self.component = "pi-call"
        self.function = function
        self.detail = detail
        self.retryable = retryable
        super().__init__(f"FAIL pi-call {function}: {detail}")


def _backoff_seconds(attempt: int) -> float:
    delay = 0.2 * float(2**attempt)
    if delay > 2.0:  # noqa: PLR2004  # retry cap, seconds
        return 2.0
    return delay


def _rpc_once(cwd: Path, *, timeout: int, env: dict[str, str] | None) -> list[dict[str, Any]]:
    function = "rpc_commands"
    process = subprocess.Popen(
        ["pi", "--mode", "rpc", "--no-session"],
        cwd=str(cwd),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(
            json.dumps({"id": "mr-skills", "type": "get_commands"}) + "\n",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
        raise PiCallError(function, f"Pi RPC timeout after {timeout}s", retryable=False) from None
    if process.returncode != 0:
        raise PiCallError(
            function,
            f"Pi RPC exited {process.returncode}: {stderr[:500]}",
            retryable=True,
        )
    responses: list[Any] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            responses.append(json.loads(line))
        except json.JSONDecodeError:
            raise PiCallError(function, "Pi RPC returned invalid JSONL", retryable=True) from None
    for response in responses:
        if isinstance(response, dict) and response.get("command") == "get_commands":
            return response_commands(response)
    raise PiCallError(function, "Pi RPC did not return get_commands", retryable=True)


def rpc_commands(
    cwd: Path,
    *,
    timeout: int = 20,
    env: dict[str, str] | None = None,
    attempts: int = 3,
    sleep: Callable[[float], None] | None = None,
) -> list[dict[str, Any]]:
    """Call get_commands. Transient startup failures retry with backoff; a timeout does not."""
    if attempts < 1:
        raise PiCallError("rpc_commands", "attempts must be at least 1", retryable=False)
    pause = time.sleep if sleep is None else sleep
    last: PiCallError | None = None
    for attempt in range(attempts):
        try:
            return _rpc_once(cwd, timeout=timeout, env=env)
        except PiCallError as exc:
            last = exc
            if not exc.retryable or attempt + 1 == attempts:
                if exc.retryable:
                    detail = f"after {attempts} attempts: {exc.detail}"
                    raise PiCallError(exc.function, detail, retryable=False) from None
                raise
            pause(_backoff_seconds(attempt))
    raise PiCallError(
        "rpc_commands",
        "Pi RPC produced no result" if last is None else last.detail,
        retryable=False,
    )


def pi_discovery_check(cwd: Path, expected_skills: set[str], *, require_package: bool = True) -> Check:
    if shutil.which("pi") is None:
        return Check("pi-native-discovery", "B", "not_run", "Pi binary not found")
    try:
        commands = rpc_commands(cwd)
    except (OSError, ValueError) as exc:
        return Check("pi-native-discovery", "B", "fail", str(exc)[:500])
    by_name = {
        str(command.get("name", "")).removeprefix("skill:"): command
        for command in commands
        if str(command.get("name", "")).startswith("skill:")
    }
    missing = sorted(expected_skills - set(by_name))
    if missing:
        return Check("pi-native-discovery", "B", "fail", f"missing skills: {missing}")
    if require_package:
        wrong_origin = sorted(
            name
            for name in expected_skills
            if by_name[name].get("sourceInfo", {}).get("origin") not in {"package", "top-level"}
        )
        if wrong_origin:
            return Check(
                "pi-native-discovery",
                "B",
                "fail",
                f"skills not loaded from a package: {wrong_origin}",
            )
    return Check(
        "pi-native-discovery",
        "B",
        "pass",
        f"{len(expected_skills)} skills discovered natively",
    )


def _retryable_spawn(run: CancellableRun) -> bool:
    """True only when the process died before producing output."""
    if run.timed_out or run.cancelled or run.stdout.strip():
        return False
    return run.returncode != 0


def _interpret_pi_output(run: CancellableRun) -> tuple[str, str]:
    if run.timed_out:
        return (
            "cancelled",
            "timeout; process group killed; reconciliation_required before retry",
        )
    stop_reason = ""
    final_text = ""
    try:
        for line in run.stdout.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("type") != "message_end":
                continue
            message = event.get("message", {})
            if message.get("role") != "assistant":
                continue
            stop_reason = str(message.get("stopReason") or stop_reason)
            content = message.get("content") or []
            final_text = "".join(
                str(part.get("text", "")) for part in content if isinstance(part, dict) and part.get("type") == "text"
            )
    except (json.JSONDecodeError, AttributeError) as exc:
        stop_reason = "error"
        final_text = f"invalid Pi JSONL: {exc}"
    if run.cancelled:
        outcome = "cancelled"
    elif run.returncode != 0 or stop_reason in {"error", "aborted"}:
        outcome = "failed"
    else:
        outcome = "succeeded"
    return outcome, (final_text or run.stderr or "")[:500]


class PiSubagentAdapter:
    """Execute one task in an isolated Pi JSON-mode subprocess."""

    def __init__(  # noqa: PLR0913  # keyword-only call budget: binary/model/timeout/creds/attempts/sleep
        self,
        *,
        binary: str = "pi",
        model: str | None = None,
        timeout: int = 300,
        credential_names: tuple[str, ...] = (),
        attempts: int = 3,
        retry_sleep: Callable[[float], None] | None = None,
    ) -> None:
        if attempts < 1:
            raise PiCallError("PiSubagentAdapter", "attempts must be at least 1", retryable=False)
        self.binary = binary
        self.model = resolve_pi_model(model)
        self.timeout = timeout
        self.credential_names = credential_names
        self.attempts = attempts
        self.retry_sleep = time.sleep if retry_sleep is None else retry_sleep

    def _argv(
        self,
        operation: OpSpec,
        packet: str,
        task: dict[str, Any],
        policy: ExecutionPolicy,
    ) -> list[str]:
        prompt = f"/skill:{operation.skill}\n\nExecute exactly this task packet:\n{packet}"
        if policy.write_scope:
            paths = ", ".join(policy.write_scope)
            expected = "\n".join(f"{path} must contain exactly: {task['id']}" for path in policy.write_scope)
            prompt += (
                f"\nWrite only these files under the workspace ({paths}).\n"
                f"{expected}\n"
                "Do not publish, push, tag or open PRs. Stop when the files exist."
            )
        return [
            self.binary,
            "--mode",
            "json",
            "-p",
            "--no-session",
            "--tools",
            ",".join(policy.tools),
            "--model",
            self.model,
            prompt,
        ]

    def _run_with_retry(self, argv: list[str], cwd: str, env: dict[str, str], context: RunContext) -> CancellableRun:
        for attempt in range(self.attempts):
            try:
                run = run_cancellable_subprocess(
                    argv,
                    cwd=cwd,
                    env=env,
                    timeout=self.timeout,
                    cancel_event=context.cancel_event,
                )
            except OSError:
                if attempt + 1 == self.attempts:
                    raise
                self.retry_sleep(_backoff_seconds(attempt))
                continue
            if not _retryable_spawn(run) or attempt + 1 == self.attempts:
                return run
            self.retry_sleep(_backoff_seconds(attempt))
        raise PiCallError("execute", "Pi spawn produced no result", retryable=False)

    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        started = time.monotonic()
        run_id = str(uuid.uuid4())
        operation = get_operation(str(task["operation"]))
        packet = json.dumps(
            {"task": task, "plan_id": context.plan_id, "run_id": context.run_id},
            sort_keys=True,
        )
        plan_digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
        policy = build_policy(
            harness="pi",
            task=task,
            timeout_s=self.timeout,
            credential_names=self.credential_names,
        )
        argv = self._argv(operation, packet, task, policy)
        assert_argv_policy(argv)

        def finish(outcome: str, returncode: int | None, detail: str) -> AdapterResult:
            operation_result = OpResult(
                operation.operation_id,
                outcome,
                returncode,
                int((time.monotonic() - started) * 1000),
                detail,
                operation.effect,
                run_id=run_id,
                plan_digest=plan_digest,
            )
            return AdapterResult(outcome, detail=detail, operation_result=operation_result)

        try:
            run = self._run_with_retry(argv, str(context.repo), policy.env_mapping(), context)
        except OSError as exc:
            return finish("failed", None, f"Pi spawn failed: {exc}")
        outcome, detail = _interpret_pi_output(run)
        returncode = 124 if run.timed_out else run.returncode
        return finish(outcome, returncode, detail)


def _version() -> str | None:
    if shutil.which("pi") is None:
        return None
    try:
        result = subprocess.run(["pi", "--version"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pi native package discovery check")
    parser.add_argument("--cwd", type=Path, default=Path("."))
    parser.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--allow-top-level", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    skills_dir = args.catalog.resolve() / "skills"
    expected = {path.name for path in skills_dir.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    check = pi_discovery_check(args.cwd.resolve(), expected, require_package=not args.allow_top_level)
    report = build_report(
        "pi",
        [check],
        harness_version=_version(),
        source=str(args.catalog.resolve()),
        target=str(args.cwd.resolve()),
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"pi: {report['outcome']}: {check.detail}")
    return report_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
