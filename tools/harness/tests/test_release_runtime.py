"""The operator home runtime accepts a verified release, not the development checkout."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.runtime import (  # noqa: E402
    PAYLOAD_CURSOR,
    PAYLOAD_DIRS,
    PAYLOAD_FILES,
    InstallFailure,
    install_verified_runtime,
    sync_payload,
)


def _package_version() -> str:
    return str(json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"])


def _release_like(tmp_path: Path) -> Path:
    """Payload copy with no checkout marker. A published archive has no ``.git``."""
    dest = tmp_path / f"machineroom-{_package_version()}"
    for relative in (*PAYLOAD_DIRS, *PAYLOAD_CURSOR):
        shutil.copytree(ROOT / relative, dest / relative, symlinks=False)
    for relative in PAYLOAD_FILES:
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    assert not (dest / ".git").exists()
    return dest


def _hook_commands(runtime: Path) -> list[str]:
    data = json.loads((runtime / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
    return [entry["command"] for entries in data["hooks"].values() for entry in entries]


def test_home_sync_command_refuses_development_checkout(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)
    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "runtime-sync.sh"),
            "sync",
            "--from",
            str(ROOT),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0, proc.stdout
    combined = f"{proc.stdout}\n{proc.stderr}".lower()
    assert "release" in combined or "development" in combined
    assert "traceback" not in combined
    assert not (home / ".machineroom").exists()


def test_home_sync_payload_refuses_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    with pytest.raises(InstallFailure) as caught:
        sync_payload(ROOT, home / ".machineroom", origin="sync")
    assert caught.value.function == "sync_payload"
    detail = caught.value.detail.lower()
    assert "release" in detail or "development" in detail
    assert not (home / ".machineroom").exists()


def test_home_rejects_checkout_marked_as_release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    with pytest.raises(InstallFailure) as caught:
        sync_payload(ROOT, home / ".machineroom", origin=f"release:{_package_version()}")
    assert "development" in caught.value.detail.lower() or ".git" in caught.value.detail
    assert not (home / ".machineroom").exists()


def test_home_release_version_must_match_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    release = _release_like(tmp_path)
    assert _package_version() != "9.9.9"
    with pytest.raises(InstallFailure) as caught:
        sync_payload(release, home / ".machineroom", origin="release:9.9.9")
    assert "9.9.9" in caught.value.detail
    assert not (home / ".machineroom").exists()


def test_home_release_records_stable_source_and_rewrites_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    version = _package_version()
    manifest = install_verified_runtime(_release_like(tmp_path), home / ".machineroom", version)
    runtime = home / ".machineroom"
    assert manifest["origin"] == f"release:{version}"
    assert manifest["source"] == f"release:{version}"
    assert manifest["version"] == version
    commands = _hook_commands(runtime)
    assert commands
    assert all(command.startswith("python3 hooks/") for command in commands)
    stored = json.loads((runtime / ".runtime-manifest.json").read_text(encoding="utf-8"))
    assert stored["source"] == f"release:{version}"


def test_version_mismatch_leaves_existing_home_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    version = _package_version()
    runtime = home / ".machineroom"
    release = _release_like(tmp_path)
    install_verified_runtime(release, runtime, version)
    before = (runtime / ".runtime-manifest.json").read_text(encoding="utf-8")
    with pytest.raises(InstallFailure):
        sync_payload(release, runtime, origin="release:9.9.9")
    assert (runtime / ".runtime-manifest.json").read_text(encoding="utf-8") == before


def test_other_destinations_still_accept_a_checkout_sync(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    manifest = sync_payload(ROOT, home / ".machineroom", origin="sync")
    assert manifest["origin"] == "sync"
    assert manifest["source"] == str(ROOT.resolve())
    commands = _hook_commands(home / ".machineroom")
    assert any(".cursor/hooks/" in command for command in commands)
