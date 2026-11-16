"""Pi model scope: one allowlist for orchestrator calls and the extension spawn.

The kept set is the two opencode-go DeepSeek models, free opencode models, and
NVIDIA Nemotron models. ``kimi-coding`` and the other opencode-go models must
be rejected before a process starts.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "workspace-router"))

from harness.model_scope import (
    ModelScopeError,
    model_in_scope,
    resolve_pi_model,
)
from harness.pi import PiSubagentAdapter  # noqa: E402
from orchestrator.run import _build_adapter  # noqa: E402

SCOPE_PATH = ROOT / "extensions" / "machineroom" / "model-scope.json"
KEPT = (
    "opencode-go/deepseek-v4.1-flash",
    "opencode-go/deepseek-v4-pro",
    "opencode/beam-free",
    "opencode/nemotron-3.5-super-vl-free",
    "nvidia/nvidia/llama-3.1-nemotron-70b-instruct",
    "NVIDIA/NVIDIA/nemotron-3-nano-omni-30b-a3b-reasoning",
)
DROPPED = (
    "kimi-coding/k3.1-pro",
    "kimi-coding/k3",
    "opencode-go/beam-free",
    "opencode-go/longcat-2.5-free",
    "opencode/deepseek-v4-pro",
    "opencode/deepseek-v4.1-flash",
    "nvidia/meta/llama-3.1-70b-instruct",
    "deepseek-v4.1-flash",
    "opencode/*free*",
    "nvidia/*nemotron*",
)


def test_scope_file_is_the_only_pattern_list() -> None:
    payload = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    assert payload["defaultModel"] == "opencode-go/deepseek-v4.1-flash"
    assert payload["patterns"] == [
        "opencode-go/deepseek-v4.1-flash",
        "opencode-go/deepseek-v4-pro",
        "opencode/*free*",
        "nvidia/*nemotron*",
    ]


def test_default_model_is_the_kept_deepseek_flash() -> None:
    assert resolve_pi_model(None) == "opencode-go/deepseek-v4.1-flash"
    assert resolve_pi_model("  ") == "opencode-go/deepseek-v4.1-flash"


@pytest.mark.parametrize("reference", KEPT)
def test_kept_models_stay_in_scope(reference: str) -> None:
    assert model_in_scope(reference), reference
    assert resolve_pi_model(reference) == reference.strip()


@pytest.mark.parametrize("reference", DROPPED)
def test_removed_models_stay_out_of_scope(reference: str) -> None:
    assert not model_in_scope(reference), reference


def test_disallowed_model_is_a_structured_error() -> None:
    with pytest.raises(ModelScopeError) as caught:
        resolve_pi_model("kimi-coding/k3.1-pro")
    assert caught.value.component == "model-scope"
    assert caught.value.function == "resolve_pi_model"
    assert "kimi-coding/k3.1-pro" in caught.value.detail
    assert "\n" not in str(caught.value)


def test_orchestrator_uses_the_scoped_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MR_PI_MODEL", raising=False)
    adapter = _build_adapter("pi")
    assert isinstance(adapter, PiSubagentAdapter)
    assert adapter.model == "opencode-go/deepseek-v4.1-flash"


def test_orchestrator_rejects_beam_free_on_opencode_go(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MR_PI_MODEL", "opencode-go/beam-free")
    with pytest.raises(ModelScopeError):
        _build_adapter("pi")


def test_native_script_has_one_scoped_default() -> None:
    text = (ROOT / "scripts" / "tests" / "test_pi_orchestration.sh").read_text(encoding="utf-8")
    assert "kimi-coding" not in text
    assert "beam-free" not in text
    assert text.count('MR_PI_MODEL="${MR_PI_MODEL:-') == 1
    assert "opencode-go/deepseek-v4.1-flash" in text


def test_extension_spawn_uses_the_shared_scope_and_retry() -> None:
    source = (ROOT / "extensions" / "machineroom" / "index.ts").read_text(encoding="utf-8")
    assert "apt-get|sshd" not in source
    assert "loadMatcher" in source
    assert "resolveSubagentModel" in source
    assert "buildSubagentArgs" in source
    assert "shouldRetrySpawn" in source
    assert "function runPiOnce" not in source
    call_source = (ROOT / "extensions" / "machineroom" / "call.ts").read_text(encoding="utf-8")
    assert "function runPiOnce" in call_source


def test_typescript_scope_matches_python(tmp_path: Path) -> None:
    module = ROOT / "extensions" / "machineroom" / "model-scope.ts"
    call = ROOT / "extensions" / "machineroom" / "call.ts"
    assert module.is_file() and call.is_file()
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not on PATH: TypeScript model scope is not_run here")
    probe = subprocess.run(
        [node, "--experimental-strip-types", "-e", "process.exit(0)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("node without --experimental-strip-types: TypeScript model scope is not_run here")
    samples = list(KEPT) + list(DROPPED)
    script = tmp_path / "scope.mjs"
    script.write_text(
        "import { loadModelScope, modelInScope, resolveSubagentModel } from "
        f'"{module.as_posix()}";\n'
        "import { backoffMs, buildSubagentArgs, shouldRetrySpawn } from "
        f'"{call.as_posix()}";\n'
        f"const root = {json.dumps(str(ROOT))};\n"
        f"const samples = {json.dumps(samples)};\n"
        "const scope = loadModelScope(root);\n"
        "const decisions = samples.map((ref) => modelInScope(ref, scope));\n"
        "const args = buildSubagentArgs({\n"
        "  tools: ['read'], worker: 'worker.md', skill: 'role-back', task: 'ping', model: scope.defaultModel,\n"
        "});\n"
        "const retry = shouldRetrySpawn({\n"
        "  attempt: 0, attempts: 3, timedOut: false, aborted: false, stdout: '', exitCode: 1,\n"
        "});\n"
        "const noRetry = shouldRetrySpawn({\n"
        "  attempt: 0, attempts: 3, timedOut: true, aborted: false, stdout: '', exitCode: 1,\n"
        "});\n"
        "console.log(JSON.stringify({\n"
        "  defaultModel: scope.defaultModel,\n"
        "  decisions,\n"
        "  resolved: resolveSubagentModel('  ', scope),\n"
        "  args,\n"
        "  retry,\n"
        "  noRetry,\n"
        "  delay: backoffMs(1),\n"
        "}));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    observed = json.loads(proc.stdout.strip().splitlines()[-1])
    assert observed["defaultModel"] == resolve_pi_model(None)
    assert observed["decisions"] == [model_in_scope(ref) for ref in samples]
    assert observed["resolved"] == "opencode-go/deepseek-v4.1-flash"
    assert observed["args"][-3:-1] == ["--model", "opencode-go/deepseek-v4.1-flash"]
    assert "/skill:role-back" in observed["args"][-1]
    assert observed["retry"] is True
    assert observed["noRetry"] is False
    assert observed["delay"] == 400  # noqa: PLR2004  # 200ms base doubled once
