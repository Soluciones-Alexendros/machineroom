"""Contract fixtures for the public catalog. Counts and phase order come from the tree."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
SHA = "a" * 40
NOTE = "declarada en la plantilla, no la devuelve el router de fase"

ROUTER = """\
PHASES = ("DEFINE", "IMPLEMENT")

def handoff_for_phase(project, phase):
    h = project.get("handoffs") or {}
    mapping = {
        "DEFINE": h.get("define", "plan-specification"),
        "IMPLEMENT": h.get("implement_back") or h.get("implement_front") or "role-back",
    }
    return mapping.get(phase)
"""

TEMPLATE = """\
handoffs:
  define: plan-specification
  implement_back: role-back
  implement_front: role-front
  implement_linux: role-linux
"""

REGISTRY = """\
tools:
  - tool_id: plan-specification
    skill: plan-specification
    operations:
      - id: write_spec
        effect: read
        approval_required: false
        dry_run: "yes"
"""

SKILL = """\
---
name: plan-specification
description: Write a spec
metadata:
  domain: plan
  type: atomic
  language: en
  keywords: spec
  version: 1.2.3
compatibility: cursor, pi
---

## Overview

Public overview.

## When to Use

When a change is large.
"""

INSTALL = """\
# Install

The repository is public.

```bash
pi install git:github.com/Soluciones-Alexendros/machineroom@v9.0.1
```

See [the readme](../README.md) and [Pi](https://pi.dev/docs/latest/skills).

## Machine runtime

This historical note says 99 skills and is not the lead.

```bash
pi install git:github.com/Soluciones-Alexendros/machineroom@v9.0.1
```
"""

README = """\
**Machineroom** es un pipeline.

Versión 1. 99 skills en 5 dominios.
"""

PYPROJECT = """\
[dependency-groups]
dependencies = [
  "beta",
]

[project]
name = "fixture"
version = "0.0.0"
dependencies = [
  "alpha",
]
"""


def _load() -> Any:
    path = Path(__file__).resolve().parents[1] / "generate.py"
    spec = importlib.util.spec_from_file_location("site_catalog_generate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load()


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo(tmp_path: Path) -> Path:
    _write(tmp_path, "package.json", json.dumps({"version": "9.0.1", "devDependencies": {"prettier": "1.0.0"}}))
    _write(tmp_path, "README.md", README)
    _write(tmp_path, "tools/pyproject.toml", PYPROJECT)
    _write(tmp_path, "tools/workspace-router/project_load.py", ROUTER)
    _write(tmp_path, "templates/harness/project.yaml", TEMPLATE)
    _write(tmp_path, "templates/product/.keep", "")
    _write(tmp_path, "tools/execution/registry.yaml", REGISTRY)
    _write(tmp_path, "skills/plan-specification/SKILL.md", SKILL)
    _write(tmp_path, "docs/harness-setup.md", INSTALL)
    _write(tmp_path, "stacks/.keep", "")
    _write(tmp_path, ".github/workflows/.keep", "")
    _write(
        tmp_path,
        "site/manifest.yaml",
        """\
allowed_hosts:
  - github.com
  - pi.dev
images: []
docs:
  - source: docs/harness-setup.md
    slug: instalar
    group: instalar
    lang: en
consult_on_github:
  - source: README.md
""",
    )
    _write(tmp_path, "site/portal.pin", f"sha: {SHA}\n")
    return tmp_path


def _build(root: Path) -> dict[str, Any]:
    catalog = GEN.build_catalog(root, sha=SHA)
    assert isinstance(catalog, dict)
    return catalog


def test_new_skill_appears_without_a_site(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    first = _build(root)
    assert [item["name"] for item in first["skills"]] == ["plan-specification"]
    extra = SKILL.replace("name: plan-specification", "name: plan-testing").replace("domain: plan", "domain: plan")
    _write(root, "skills/plan-testing/SKILL.md", extra)
    second = _build(root)
    assert [item["name"] for item in second["skills"]] == ["plan-specification", "plan-testing"]
    assert second["skill_count"] == len(second["skills"])


def test_public_skill_hides_triggers_and_metadata_version(tmp_path: Path) -> None:
    catalog = _build(_repo(tmp_path))
    skill = catalog["skills"][0]
    assert "triggers" not in skill
    assert "1.2.3" not in json.dumps(skill)
    assert (
        skill["source_url"]
        == f"https://github.com/Soluciones-Alexendros/machineroom/blob/{SHA}/skills/plan-specification/SKILL.md"
    )
    assert skill["overview_markdown"] == "Public overview."


def test_phase_order_matches_the_ast_tuple(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    catalog = _build(root)
    source = root / "tools/workspace-router/project_load.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    order: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PHASES" for target in node.targets
        ):
            assert isinstance(node.value, ast.Tuple)
            order = [
                elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    assert [item["id"] for item in catalog["phases"]] == order
    implement = next(item for item in catalog["phases"] if item["id"] == "IMPLEMENT")
    assert implement["skill"] == "role-back"
    assert implement["template_key"] == "implement_back"
    assert {item["skill"]: item["note"] for item in implement["others"]} == {"role-front": NOTE, "role-linux": NOTE}


def test_direct_python_deps_ignore_later_tables(tmp_path: Path) -> None:
    catalog = _build(_repo(tmp_path))
    assert catalog["dependencies"]["tools"] == [{"name": "alpha", "spec": "alpha", "kind": "directa"}]
    assert all(item["kind"] == "desarrollo" for item in catalog["dependencies"]["root"])
    assert catalog["dependencies"]["site"] == []


def test_parent_link_inside_the_tree_is_kept(tmp_path: Path) -> None:
    catalog = _build(_repo(tmp_path))
    page = catalog["docs"][0]["markdown"]
    assert f"https://github.com/Soluciones-Alexendros/machineroom/blob/{SHA}/README.md" in page
    assert "https://pi.dev/docs/latest/skills" in page
    assert "99 skills" not in catalog["hero_markdown"]


def test_duplicate_slug_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/other.md", "# Other\n\nText.\n")
    text = (root / "site/manifest.yaml").read_text(encoding="utf-8")
    text = text.replace(
        "    lang: en\nconsult_on_github:",
        "    lang: en\n  - source: docs/other.md\n    slug: instalar\n    group: canon\n    lang: es\nconsult_on_github:",
    )
    _write(root, "site/manifest.yaml", text)
    with pytest.raises(GEN.CatalogError, match="slug repetido: instalar"):
        _build(root)


def test_unpublished_reference_names_origin_and_target(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/harness-setup.md", INSTALL + "\nSee [secret](../tools/pyproject.toml).\n")
    with pytest.raises(
        GEN.CatalogError, match=r"docs/harness-setup.md enlaza \.\./tools/pyproject.toml: destino no publicado"
    ):
        _build(root)


def test_absolute_link_is_rejected(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/harness-setup.md", INSTALL + "\nSee [root](/README.md).\n")
    with pytest.raises(GEN.CatalogError, match=r"enlaza fuera del árbol: /README\.md"):
        _build(root)


def test_missing_pin_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "site/portal.pin").unlink()
    with pytest.raises(GEN.CatalogError, match=r"falta site/portal\.pin"):
        _build(root)


def test_missing_overview_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "skills/plan-specification/SKILL.md", SKILL.replace("## Overview\n\nPublic overview.\n\n", ""))
    with pytest.raises(GEN.CatalogError, match="plan-specification no tiene Overview"):
        _build(root)


def test_forbidden_host_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/harness-setup.md", INSTALL + "\nSee [spec](https://agentskills.io/specification).\n")
    with pytest.raises(GEN.CatalogError, match=r"host no permitido: agentskills\.io"):
        _build(root)


def test_install_fence_must_match_package_version(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/harness-setup.md", INSTALL.replace("@v9.0.1", "@v1.0.0", 1))
    with pytest.raises(GEN.CatalogError, match=r"la guía fija 1\.0\.0 y package\.json es 9\.0\.1"):
        _build(root)


def test_home_path_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/harness-setup.md", INSTALL + "\nClone /home/alex/machineroom.\n")
    with pytest.raises(GEN.CatalogError, match=r"docs/harness-setup.md contiene una ruta /home/"):
        _build(root)


def test_unnamed_image_fails_and_named_image_stays_same_origin(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(root, "docs/map.png", "png")
    _write(root, "docs/harness-setup.md", INSTALL + "\n![map](map.png)\n")
    with pytest.raises(GEN.CatalogError, match="imagen no nombrada"):
        _build(root)
    _write(root, "docs/map.png", "png")
    manifest = (
        (root / "site/manifest.yaml")
        .read_text(encoding="utf-8")
        .replace("images: []", "images:\n  - source: docs/map.png\n    href: /assets/map.png")
    )
    _write(root, "site/manifest.yaml", manifest)
    catalog = _build(root)
    assert "![map](/assets/map.png)" in catalog["docs"][0]["markdown"]


def test_unknown_resolution_shape_names_the_phase(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(
        root, "tools/workspace-router/project_load.py", ROUTER.replace('h.get("define", "plan-specification")', "other")
    )
    with pytest.raises(GEN.CatalogError, match="fase DEFINE"):
        _build(root)


def test_live_catalog_follows_the_repository() -> None:
    catalog = GEN.build_catalog(ROOT, sha=SHA)
    source = ROOT / "tools/workspace-router/project_load.py"
    assert [item["id"] for item in catalog["phases"]] == GEN._parse_phases(source)
    assert catalog["skill_count"] == len(catalog["skills"])
    assert catalog["product_version"] == json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    assert catalog["hero_markdown"].startswith("**Machineroom**")
    assert "Versión" not in catalog["hero_markdown"]
    pin = yaml.safe_load((ROOT / "site/portal.pin").read_text(encoding="utf-8"))
    assert catalog["portal_sha"] == pin["sha"]
    implement = next(item for item in catalog["phases"] if item["id"] == "IMPLEMENT")
    assert implement["skill"] == "role-back"
    assert {item["skill"]: item["note"] for item in implement["others"]} == {"role-front": NOTE, "role-linux": NOTE}
    for skill in catalog["skills"]:
        assert "triggers" not in skill
        assert skill["source_url"].endswith(skill["entry"])
        assert skill["domain"] in GEN.DOMAINS
    root_deps = catalog["dependencies"]["root"]
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert {item["name"] for item in root_deps} == set(package.get("devDependencies") or {})
    assert all(item["kind"] == "desarrollo" for item in root_deps)
    project = (ROOT / "tools/pyproject.toml").read_text(encoding="utf-8").split("[project]", 1)[1].split("\n[", 1)[0]
    for dep in catalog["dependencies"]["tools"]:
        assert dep["name"] in project
    slugs = [item["slug"] for item in catalog["docs"]]
    assert slugs[0] == "instalar"
    assert len(slugs) == len(set(slugs))
    install = next(item for item in catalog["docs"] if item["slug"] == "instalar")
    assert f"@v{catalog['product_version']}" in install["markdown"]
    assert "/home/" not in install["markdown"]


def test_excluded_sentinel_stays_out_of_the_manifest(tmp_path: Path) -> None:
    check = Path(__file__).resolve().parents[1] / "check_dist.py"
    spec = importlib.util.spec_from_file_location("site_catalog_check_dist", check)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    phrase = module.EXCLUDED_SENTINEL
    source = (ROOT / "docs/runbooks/rotate-secrets.md").read_text(encoding="utf-8")
    manifest = (ROOT / "site/manifest.yaml").read_text(encoding="utf-8")
    assert phrase in source
    assert "docs/runbooks/rotate-secrets.md" not in manifest
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "page.js").write_text("allowed", encoding="utf-8")
    dirty = tmp_path / "dirty"
    dirty.mkdir()
    (dirty / "page.js").write_text(phrase, encoding="utf-8")
    assert module.contains_excluded_sentinel(clean) is False
    assert module.contains_excluded_sentinel(dirty) is True
