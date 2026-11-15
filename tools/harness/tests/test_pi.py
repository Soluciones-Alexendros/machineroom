"""Pi RPC discovery parsing and capability outcomes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import pi  # noqa: E402


def _commands(names: list[str], origin: str = "package") -> list[dict[str, Any]]:
    return [
        {
            "name": f"skill:{name}",
            "source": "skill",
            "sourceInfo": {"origin": origin, "path": f"/package/skills/{name}/SKILL.md"},
        }
        for name in names
    ]


def test_rpc_response_requires_successful_get_commands() -> None:
    response = {
        "type": "response",
        "command": "get_commands",
        "success": True,
        "data": {"commands": _commands(["one"])},
    }
    assert pi.skill_commands(response) == _commands(["one"])
    with pytest.raises(ValueError, match="get_commands"):
        pi.skill_commands({"type": "response", "success": False})


def test_discovery_checks_names_and_package_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/pi")
    monkeypatch.setattr(pi, "rpc_commands", lambda cwd: _commands(["one", "two"]))
    check = pi.pi_discovery_check(Path("."), {"one", "two"})
    assert check.outcome == "pass"


def test_discovery_rejects_missing_or_non_package_skill(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/pi")
    monkeypatch.setattr(pi, "rpc_commands", lambda cwd: _commands(["one"], origin="top-level"))
    check = pi.pi_discovery_check(Path("."), {"one", "two"})
    assert check.outcome == "fail"
    assert "two" in check.detail or "package" in check.detail


def test_missing_binary_is_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    check = pi.pi_discovery_check(Path("."), {"one"})
    assert check.outcome == "not_run"


def _rpc_body() -> str:
    return json.dumps(
        {
            "type": "response",
            "command": "get_commands",
            "success": True,
            "data": {"commands": _commands(["role-back"])},
        }
    )


def test_rpc_retries_a_transient_startup_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An empty non-zero startup is retried. A timeout spends its budget once."""
    calls = {"n": 0}
    sleeps: list[float] = []

    class _Process:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls["n"] += 1
            self.pid = 4242
            self.returncode = 0

        def communicate(self, _payload: str, timeout: int | None = None) -> tuple[str, str]:
            del timeout
            if calls["n"] < 3:  # noqa: PLR2004  # fail the first two of three attempts
                self.returncode = 1
                return "", "startup failed"
            self.returncode = 0
            return _rpc_body() + "\n", ""

        def wait(self, timeout: int | None = None) -> int:
            del timeout
            return self.returncode

    monkeypatch.setattr("harness.pi.subprocess.Popen", _Process)
    monkeypatch.setattr("harness.pi.os.killpg", lambda *_args: None)
    commands = pi.rpc_commands(tmp_path, sleep=sleeps.append)
    assert [item["name"] for item in commands] == ["skill:role-back"]
    assert calls["n"] == 3  # noqa: PLR2004  # two failures plus the successful attempt
    assert sleeps == [0.2, 0.4]


def test_rpc_timeout_is_not_retried(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = {"n": 0}

    class _Process:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls["n"] += 1
            self.pid = 4242
            self.returncode = -9

        def communicate(self, _payload: str, timeout: int | None = None) -> tuple[str, str]:
            raise subprocess.TimeoutExpired(cmd="pi", timeout=timeout or 1)

        def wait(self, timeout: int | None = None) -> int:
            del timeout
            return self.returncode

    monkeypatch.setattr("harness.pi.subprocess.Popen", _Process)
    monkeypatch.setattr("harness.pi.os.killpg", lambda *_args: None)
    with pytest.raises(pi.PiCallError) as caught:
        pi.rpc_commands(tmp_path, timeout=1, sleep=lambda _delay: None)
    assert caught.value.retryable is False
    assert caught.value.component == "pi-call"
    assert calls["n"] == 1
