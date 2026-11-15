"""Pi subagent process behavior with an isolated fake executable."""

from __future__ import annotations

import json
import stat
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.model_scope import ModelScopeError  # noqa: E402
from harness.pi import PiSubagentAdapter  # noqa: E402
from orchestrator.model import RunContext  # noqa: E402
from orchestrator.ports import AdapterResult  # noqa: E402


def _binary(tmp_path: Path, behavior: str) -> Path:
    path = tmp_path / "pi-fixture"
    body = """import json, sys, time
behavior = "__BEHAVIOR__"
args = sys.argv[1:]
if behavior == 'args':
    print(json.dumps({'args': args}))
elif behavior == 'invalid':
    print('not-json')
elif behavior in {'timeout', 'cancel'}:
    time.sleep(10)
else:
    stop = 'error' if behavior == 'error' else 'stop'
    payload = {
        'type': 'message_end',
        'message': {
            'role': 'assistant',
            'content': [{'type': 'text', 'text': behavior}],
            'stopReason': stop,
        },
    }
    print(json.dumps(payload))
""".replace("__BEHAVIOR__", behavior)
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _context(tmp_path: Path) -> RunContext:
    return RunContext(tmp_path, "fixture-plan", "a" * 64, "0" * 40, "run-fixture", "pi")


def _task(write: bool = True) -> dict[str, Any]:
    return {
        "id": "fixture-task",
        "phase": "IMPLEMENT",
        "operation": "implement_api",
        "roles": ["role-back"],
        "write_scope": ["out.txt"] if write else [],
    }


def _execute(tmp_path: Path, behavior: str, **kwargs: Any) -> AdapterResult:
    adapter = PiSubagentAdapter(binary=str(_binary(tmp_path, behavior)), **kwargs)
    return adapter.execute(_task(), _context(tmp_path))


def test_subagent_success_returns_actual_operation_result(tmp_path: Path) -> None:
    result = _execute(tmp_path, "success")
    assert result.outcome == "succeeded"
    assert result.operation_result is not None
    assert result.operation_result.operation_id == "implement_api"
    assert result.operation_result.run_id


def test_model_error_is_failed(tmp_path: Path) -> None:
    result = _execute(tmp_path, "error")
    assert result.outcome == "failed"
    assert "error" in result.detail


def test_invalid_json_is_failed(tmp_path: Path) -> None:
    result = _execute(tmp_path, "invalid")
    assert result.outcome == "failed"


def test_timeout_kills_process_and_requires_reconciliation(tmp_path: Path) -> None:
    started = time.monotonic()
    result = _execute(tmp_path, "timeout", timeout=1)
    assert result.outcome == "cancelled"
    assert "reconciliation" in result.detail
    assert time.monotonic() - started < 4  # noqa: PLR2004  # timeout bound


def test_spawn_failure_retries_then_succeeds(tmp_path: Path) -> None:
    """A process that exits before producing output is retried. A model error is not."""
    counter = tmp_path / "starts"
    path = tmp_path / "pi-flaky"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        f"counter = pathlib.Path({str(counter)!r})\n"
        "n = int(counter.read_text()) if counter.exists() else 0\n"
        "n += 1\n"
        "counter.write_text(str(n))\n"
        "if n < 3:\n"
        "    sys.exit(2)\n"
        "print(json.dumps({'type': 'message_end', 'message': {'role': 'assistant', "
        "'content': [{'type': 'text', 'text': 'ok'}], 'stopReason': 'stop'}}))\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    delays: list[float] = []
    adapter = PiSubagentAdapter(binary=str(path), attempts=3, retry_sleep=delays.append)
    result = adapter.execute(_task(write=False), _context(tmp_path))
    assert result.outcome == "succeeded", result.detail
    assert counter.read_text(encoding="utf-8") == "3"
    assert delays == [0.2, 0.4]
    with pytest.raises(ModelScopeError):
        PiSubagentAdapter(binary=str(path), model="kimi-coding/k3.1-pro")


def test_default_model_is_passed_to_the_child(tmp_path: Path) -> None:
    recorded = tmp_path / "argv.json"
    path = tmp_path / "pi-args"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        f"pathlib.Path({str(recorded)!r}).write_text(json.dumps(sys.argv[1:]))\n"
        "print(json.dumps({'type': 'message_end', 'message': {'role': 'assistant', "
        "'content': [{'type': 'text', 'text': 'ok'}], 'stopReason': 'stop'}}))\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    adapter = PiSubagentAdapter(binary=str(path))
    result = adapter.execute(_task(write=False), _context(tmp_path))
    assert result.outcome == "succeeded", result.detail
    argv = json.loads(recorded.read_text(encoding="utf-8"))
    assert argv[-3:-1] == ["--model", "opencode-go/deepseek-v4.1-flash"]


def test_cancellation_kills_process_group(tmp_path: Path) -> None:
    adapter = PiSubagentAdapter(binary=str(_binary(tmp_path, "cancel")), timeout=30)
    context = _context(tmp_path)
    timer = threading.Timer(0.2, context.cancel_event.set)
    timer.start()
    started = time.monotonic()
    result = adapter.execute(_task(), context)
    timer.join()
    assert result.outcome == "cancelled"
    assert time.monotonic() - started < 4  # noqa: PLR2004  # cancel bound
