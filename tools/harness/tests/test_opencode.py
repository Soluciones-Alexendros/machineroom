"""OpenCode checks: opt-in honesty, V2 gate, catalog ids and source collision."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.doctor import collect_checks  # noqa: E402
from harness.opencode import (  # noqa: E402
    NATIVE_OPT_IN,
    opencode_discovery_check,
    opencode_source_collision_check,
)


def _response(ids: set[str]) -> subprocess.CompletedProcess[str]:
    payload = {"data": [{"id": skill_id} for skill_id in sorted(ids)]}
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")


def test_native_discovery_requires_opt_in(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv(NATIVE_OPT_IN, raising=False)
    check = opencode_discovery_check(tmp_path, {"role-linux"})
    assert check.level == "B"
    assert check.outcome == "not_run"
    assert NATIVE_OPT_IN in check.detail


def test_native_discovery_requires_binary(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv(NATIVE_OPT_IN, "1")
    monkeypatch.setattr("harness.opencode.shutil.which", lambda _name: None)
    assert opencode_discovery_check(tmp_path, {"role-linux"}).outcome == "not_run"


def test_v1_is_blocked_not_pass(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv(NATIVE_OPT_IN, "1")
    monkeypatch.setattr("harness.opencode.shutil.which", lambda _name: "/usr/bin/opencode")
    monkeypatch.setattr("harness.opencode._version_parts", lambda _binary: (1, "opencode v1.18.34"))
    check = opencode_discovery_check(tmp_path, {"role-linux"})
    assert check.outcome == "blocked"
    assert "V2 required" in check.detail


def test_v2_lists_all_catalog_ids(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv(NATIVE_OPT_IN, "1")
    monkeypatch.setattr("harness.opencode.shutil.which", lambda _name: "/usr/bin/opencode")
    monkeypatch.setattr("harness.opencode._version_parts", lambda _binary: (2, "opencode v2.3.2"))
    monkeypatch.setattr("harness.opencode.subprocess.run", lambda *_a, **_k: _response({"role-linux", "web-owasp"}))
    check = opencode_discovery_check(tmp_path, {"role-linux", "web-owasp"})
    assert check.outcome == "pass"
    assert "v2.3.2" in check.detail


def test_v2_missing_id_is_failure(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv(NATIVE_OPT_IN, "1")
    monkeypatch.setattr("harness.opencode.shutil.which", lambda _name: "/usr/bin/opencode")
    monkeypatch.setattr("harness.opencode._version_parts", lambda _binary: (2, "opencode v2.3.2"))
    monkeypatch.setattr("harness.opencode.subprocess.run", lambda *_a, **_k: _response({"role-linux"}))
    check = opencode_discovery_check(tmp_path, {"role-linux", "web-owasp"})
    assert check.outcome == "fail"
    assert "web-owasp" in check.detail


def test_source_collision_detects_duplicate_catalog(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = tmp_path / "catalog" / "skills"
    skill = catalog / "role-linux"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: role-linux\n---\n", encoding="utf-8")
    config_home = tmp_path / "xdg" / "opencode"
    config_home.mkdir(parents=True)
    (config_home / "opencode.json").write_text(json.dumps({"skills": [str(catalog)]}), encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    check = opencode_source_collision_check(tmp_path, tmp_path / "catalog", {"role-linux"})
    assert check.outcome == "fail"
    assert "role-linux" in check.detail
    (config_home / "opencode.json").unlink()
    assert opencode_source_collision_check(tmp_path, tmp_path / "catalog", {"role-linux"}).outcome == "pass"


def test_jsonc_comments_are_tolerated(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = tmp_path / "catalog" / "skills" / "role-linux"
    catalog.mkdir(parents=True)
    (catalog / "SKILL.md").write_text("---\nname: role-linux\n---\n", encoding="utf-8")
    config_home = tmp_path / "xdg" / "opencode"
    config_home.mkdir(parents=True)
    (config_home / "opencode.json").write_text(
        '{\n // comment\n "skills": ["' + str(catalog.parent) + '"]\n}\n', encoding="utf-8"
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    check = opencode_source_collision_check(tmp_path, tmp_path / "catalog", {"role-linux"})
    assert check.outcome == "fail"


def test_jsonc_trailing_commas_are_tolerated(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = tmp_path / "catalog" / "skills" / "role-linux"
    catalog.mkdir(parents=True)
    (catalog / "SKILL.md").write_text("---\nname: role-linux\n---\n", encoding="utf-8")
    config_home = tmp_path / "xdg" / "opencode"
    config_home.mkdir(parents=True)
    (config_home / "opencode.jsonc").write_text(
        '{\n  "skills": ["' + str(catalog.parent) + '",],\n}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    check = opencode_source_collision_check(tmp_path, tmp_path / "catalog", {"role-linux"})
    assert check.outcome == "fail"
    assert "role-linux" in check.detail


def test_relative_skills_path_resolves_against_root(tmp_path: Path, monkeypatch: Any) -> None:
    ext = tmp_path / "ext" / "skills" / "role-linux"
    ext.mkdir(parents=True)
    (ext / "SKILL.md").write_text("---\nname: role-linux\n---\n", encoding="utf-8")
    src = tmp_path / "catalog-src" / "skills" / "role-linux"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\nname: role-linux\n---\n", encoding="utf-8")
    (tmp_path / "opencode.json").write_text(json.dumps({"skills": ["ext/skills"]}), encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty-xdg"))
    (tmp_path / "empty-xdg").mkdir()
    check = opencode_source_collision_check(tmp_path, tmp_path / "catalog-src", {"role-linux"})
    assert check.outcome == "fail"
    assert "role-linux" in check.detail


def test_doctor_registers_opencode_checks(tmp_path: Path, monkeypatch: Any) -> None:
    skill = tmp_path / "skills" / "role-linux"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: role-linux\n---\n", encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv(NATIVE_OPT_IN, raising=False)
    isolated = tmp_path / "isolated-home"
    isolated.mkdir()
    monkeypatch.setattr(Path, "home", lambda: isolated)
    static = collect_checks(tmp_path, "opencode", None)
    ids = {check.check_id for check in static}
    assert "opencode-skill-links" in ids
    assert "opencode-source-collision" in ids
    native = collect_checks(tmp_path, "opencode", None, native=True)
    native_ids = {check.check_id for check in native}
    assert "opencode-native-discovery" in native_ids
    assert "opencode-skill-links" in native_ids
