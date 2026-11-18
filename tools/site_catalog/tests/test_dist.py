"""Fingerprint of the built directory and the CI job that produces it."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _load() -> Any:
    path = Path(__file__).resolve().parents[1] / "check_dist.py"
    spec = importlib.util.spec_from_file_location("site_catalog_check_dist_fp", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fingerprint_ignores_identity_file(tmp_path: Path) -> None:
    module = _load()
    (tmp_path / "index.html").write_text("<p>ok</p>\n", encoding="utf-8")
    first = module.fingerprint_tree(tmp_path)
    (tmp_path / "build-identity.json").write_text('{"artifact_sha256": "no"}\n', encoding="utf-8")
    assert module.fingerprint_tree(tmp_path) == first


def test_bare_table_is_rejected() -> None:
    module = _load()
    wrapped = '<div class="table-wrap">\n<table><tr><td>a</td></tr></table></div>'
    assert module.unwrapped_tables(wrapped) == 0
    assert module.unwrapped_tables("<table><tr><td>a</td></tr></table>") == 1


def test_site_job_is_required_by_ci_gate() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    needs = workflow["jobs"]["ci-gate"]["needs"]
    assert "site" in needs
    site = workflow["jobs"]["site"]
    assert "paths" not in site
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "site" not in text.split("ALLOWED_SKIPS", 1)[1].split("\n", 1)[0]
