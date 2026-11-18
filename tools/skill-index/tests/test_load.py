"""Tests for tools/skill-index/load.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from skill_index_load import get_generate_module, load_skill_index  # noqa: E402


def test_load_skill_index_success(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    skills = tmp_path / "skills" / "demo-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: demo\n---\n",
        encoding="utf-8",
    )
    data = load_skill_index(tmp_path)
    names = [s["name"] for s in data["skills"]]
    assert "demo-skill" in names
    assert (tmp_path / "skill-index.json").is_file()


def test_load_skill_index_generator_failure_surfaces(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    gen = get_generate_module()

    def boom(_root: Path) -> dict[str, Any]:
        raise RuntimeError("generator exploded")

    monkeypatch.setattr(gen, "ensure_index", boom)
    with pytest.raises(RuntimeError, match="generator exploded"):
        load_skill_index(tmp_path)


def test_load_skill_index_missing_index_empty_skills(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "skills").mkdir()
    data = load_skill_index(tmp_path)
    assert data["skills"] == []
    assert (tmp_path / "skill-index.json").is_file()


def test_load_skill_index_ignores_foreign_cwd_index(tmp_path: Path, monkeypatch: Any) -> None:
    """CWD skill-index.json must not shadow or replace the repo catalog."""
    repo = tmp_path / "repo"
    skills = repo / "skills" / "from-repo"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: from-repo\ndescription: d\n---\n", encoding="utf-8")
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / "skill-index.json").write_text(
        json.dumps({"skills": [{"name": "from-cwd"}]}),
        encoding="utf-8",
    )
    monkeypatch.chdir(cwd)
    data = load_skill_index(repo)
    names = [s["name"] for s in data["skills"]]
    assert "from-repo" in names
    assert "from-cwd" not in names
    assert (repo / "skill-index.json").is_file()

    (repo / "skill-index.json").write_text(
        json.dumps({"skills": [{"name": "from-repo-index"}]}),
        encoding="utf-8",
    )
    data = load_skill_index(repo)
    assert data["skills"][0]["name"] == "from-repo-index"
