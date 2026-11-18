"""License gate: declared SPDX vs allowlist and hardcoded denylist."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "tools" / "validate" / "license_gate.py"
ALLOWLIST = ROOT / "tools" / "validate" / "license_allowlist.txt"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("license_gate_mod", GATE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["license_gate_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def _comp(
    name: str,
    *,
    ctype: str = "library",
    license_id: str | None = None,
    expression: str | None = None,
    licenses: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    entry: dict[str, object] = {"type": ctype, "name": name}
    if licenses is not None:
        entry["licenses"] = licenses
        return entry
    if expression is not None:
        entry["licenses"] = [{"expression": expression}]
        return entry
    if license_id is not None:
        entry["licenses"] = [{"license": {"id": license_id}}]
        return entry
    return entry


def _sbom(*components: dict[str, object]) -> dict[str, object]:
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": list(components)}


def test_mit_in_allowlist_passes() -> None:
    mod = _load()
    errors = mod.evaluate(_sbom(_comp("pkg", license_id="MIT")), {"MIT"})
    assert errors == []


def test_gpl_only_fails_with_name_and_id() -> None:
    mod = _load()
    errors = mod.evaluate(_sbom(_comp("evil", license_id="GPL-3.0-only")), {"MIT"})
    assert len(errors) == 1
    assert "evil" in errors[0]
    assert "GPL-3.0-only" in errors[0]


def test_mit_or_gpl_passes() -> None:
    mod = _load()
    errors = mod.evaluate(
        _sbom(_comp("dual", expression="MIT OR GPL-3.0-only")),
        {"MIT"},
    )
    assert errors == []


def test_mit_and_gpl_fails() -> None:
    mod = _load()
    errors = mod.evaluate(
        _sbom(_comp("both", expression="MIT AND GPL-3.0-only")),
        {"MIT"},
    )
    assert errors
    assert any("both" in e for e in errors)


def test_library_without_licenses_passes() -> None:
    mod = _load()
    errors = mod.evaluate(_sbom(_comp("bare")), {"MIT"})
    assert errors == []


def test_library_noassertion_passes() -> None:
    mod = _load()
    errors = mod.evaluate(_sbom(_comp("na", license_id="NOASSERTION")), {"MIT"})
    assert errors == []


def test_file_without_licenses_passes() -> None:
    mod = _load()
    errors = mod.evaluate(_sbom(_comp("readme", ctype="file")), {"MIT"})
    assert errors == []


def test_undeclared_id_fails() -> None:
    mod = _load()
    errors = mod.evaluate(_sbom(_comp("bsd", license_id="BSD-3-Clause")), {"MIT"})
    assert errors
    assert "BSD-3-Clause" in errors[0]
    assert "bsd" in errors[0]


def test_denied_even_if_in_allowlist() -> None:
    mod = _load()
    errors = mod.evaluate(
        _sbom(_comp("gpl", license_id="GPL-3.0-only")),
        {"MIT", "GPL-3.0-only"},
    )
    assert errors
    assert "GPL-3.0-only" in errors[0]


def test_malformed_sbom_cli(tmp_path: Path) -> None:
    mod = _load()
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    assert mod.main(["--sbom", str(bad), "--allowlist", str(ALLOWLIST)]) == 1


def test_cli_mit_fixture_exit_0(tmp_path: Path) -> None:
    mod = _load()
    path = tmp_path / "mit.cdx.json"
    path.write_text(json.dumps(_sbom(_comp("ok", license_id="MIT"))), encoding="utf-8")
    assert mod.main(["--sbom", str(path), "--allowlist", str(ALLOWLIST)]) == 0


def test_cli_gpl_fixture_exit_1(tmp_path: Path) -> None:
    mod = _load()
    path = tmp_path / "gpl.cdx.json"
    path.write_text(json.dumps(_sbom(_comp("bad", license_id="GPL-3.0-only"))), encoding="utf-8")
    assert mod.main(["--sbom", str(path), "--allowlist", str(ALLOWLIST)]) == 1


def test_load_allowlist_skips_comments() -> None:
    mod = _load()
    ids = mod.load_allowlist(ALLOWLIST)
    assert "MIT" in ids
