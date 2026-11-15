"""A Pi process is settled once: a later close must not erase output or cause a retry."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

CALL = ROOT / "extensions" / "machineroom" / "call.ts"


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not on PATH: spawn settlement is not_run here")
    probe = subprocess.run(
        [node, "--experimental-strip-types", "-e", "process.exit(0)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("node without --experimental-strip-types: spawn settlement is not_run here")
    return node


def _observe(tmp_path: Path, notices: list[dict[str, object]]) -> dict[str, object]:
    node = _node()
    script = tmp_path / "spawn-once.mjs"
    script.write_text(
        "import { noteSpawn, openSpawn, shouldRetrySpawn } from "
        f'"{CALL.as_posix()}";\n'
        f"const notices = {json.dumps(notices)};\n"
        "let state = openSpawn();\n"
        "for (const notice of notices) state = noteSpawn(state, notice);\n"
        "const retry = shouldRetrySpawn({\n"
        "  attempt: 0, attempts: 3, timedOut: state.timedOut, aborted: state.aborted,\n"
        "  stdout: state.stdout, exitCode: state.exitCode,\n"
        "});\n"
        "console.log(JSON.stringify({ state, retry }));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    observed: dict[str, object] = json.loads(proc.stdout.strip().splitlines()[-1])
    return observed


def test_error_then_close_with_output_is_one_close_and_not_retried(tmp_path: Path) -> None:
    observed = _observe(
        tmp_path,
        [
            {"kind": "output", "text": '{"type":"message_end"}\n'},
            {"kind": "error"},
            {"kind": "close", "code": 0},
            {"kind": "close", "code": 1},
        ],
    )
    state = observed["state"]
    assert isinstance(state, dict)
    assert state["closes"] == 1
    assert state["exitCode"] == 0
    assert "message_end" in str(state["stdout"])
    assert observed["retry"] is False


def test_error_then_empty_close_can_retry(tmp_path: Path) -> None:
    observed = _observe(tmp_path, [{"kind": "error"}, {"kind": "close", "code": None}])
    state = observed["state"]
    assert isinstance(state, dict)
    assert state["closes"] == 1
    assert state["exitCode"] == 1
    assert state["stdout"] == ""
    assert observed["retry"] is True


def test_timeout_settles_before_a_later_close(tmp_path: Path) -> None:
    observed = _observe(tmp_path, [{"kind": "timeout"}, {"kind": "close", "code": 0}])
    state = observed["state"]
    assert isinstance(state, dict)
    assert state["timedOut"] is True
    assert state["closes"] == 0
    assert observed["retry"] is False
