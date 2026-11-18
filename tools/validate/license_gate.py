#!/usr/bin/env python3
"""CycloneDX license gate: declared SPDX ids must pass allowlist and denylist.

Only declared licenses are judged. Empty, NONE, and NOASSERTION are ignored.
Denied families (GPL, AGPL, SSPL, CPAL) fail even if listed in the allowlist,
except when they appear as a non-chosen disjunct of a pure OR expression.

Exit 0 when the SBOM complies; exit 1 on policy violations or unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_DENY_PREFIXES = ("GPL", "AGPL", "SSPL", "CPAL")
_IGNORED = frozenset({"", "NONE", "NOASSERTION"})
_TOKEN_SPLIT = re.compile(r"\s+(?:OR|AND|WITH)\s+", re.IGNORECASE)
_HAS_OR = re.compile(r"(?<![A-Za-z0-9_+.-])OR(?![A-Za-z0-9_+.-])", re.IGNORECASE)
_HAS_AND = re.compile(r"(?<![A-Za-z0-9_+.-])AND(?![A-Za-z0-9_+.-])", re.IGNORECASE)
_HAS_WITH = re.compile(r"(?<![A-Za-z0-9_+.-])WITH(?![A-Za-z0-9_+.-])", re.IGNORECASE)


def load_allowlist(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    ids: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids.add(stripped)
    return ids


def is_denied(spdx_id: str) -> bool:
    upper = spdx_id.upper()
    return any(upper == prefix or upper.startswith(prefix + "-") for prefix in _DENY_PREFIXES)


def _normalize_token(token: str) -> str:
    return token.strip().strip("()")


def _expression_kind(expr: str) -> str:
    """Return 'or', 'and', 'with', 'mixed', or 'simple'."""
    has_or = bool(_HAS_OR.search(expr))
    has_and = bool(_HAS_AND.search(expr))
    has_with = bool(_HAS_WITH.search(expr))
    count = sum((has_or, has_and, has_with))
    if count == 0:
        return "simple"
    if count > 1:
        return "mixed"
    if has_or:
        return "or"
    if has_and:
        return "and"
    return "with"


def _tokens(expr: str) -> list[str]:
    return [t for t in (_normalize_token(p) for p in _TOKEN_SPLIT.split(expr)) if t]


def _license_strings(entry: dict[str, Any]) -> list[str]:
    """Extract raw license strings from one CycloneDX licenses[] item."""
    out: list[str] = []
    if "expression" in entry and isinstance(entry["expression"], str):
        out.append(entry["expression"].strip())
        return out
    lic = entry.get("license")
    if isinstance(lic, dict):
        for key in ("id", "name"):
            val = lic.get(key)
            if isinstance(val, str) and val.strip():
                out.append(val.strip())
                break
    return out


def _component_name(comp: dict[str, Any]) -> str:
    name = comp.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    bom_ref = comp.get("bom-ref")
    if isinstance(bom_ref, str) and bom_ref.strip():
        return bom_ref.strip()
    return "<unnamed>"


def _accept_id(spdx_id: str, allowlist: set[str]) -> bool:
    if is_denied(spdx_id):
        return False
    return spdx_id in allowlist


def _judge_expression(name: str, expr: str, allowlist: set[str]) -> list[str]:
    kind = _expression_kind(expr)
    if kind == "mixed":
        return [f"{name}: mixed OR/AND/WITH expression not allowed in v1: {expr}"]
    tokens = _tokens(expr)
    if not tokens:
        return []
    declared = [t for t in tokens if t.upper() not in _IGNORED]
    if not declared:
        return []
    if kind == "or":
        if any(_accept_id(t, allowlist) for t in declared):
            return []
        return [f"{name}: no OR disjunct allowed: {expr}"]
    # simple, and, with — every declared token must be accepted
    errors: list[str] = []
    for token in declared:
        if is_denied(token):
            errors.append(f"{name}: denied license {token}")
        elif token not in allowlist:
            errors.append(f"{name}: license {token} not in allowlist")
    return errors


def evaluate(sbom: dict[str, Any], allowlist: set[str]) -> list[str]:
    """Return policy errors for a CycloneDX document. Empty list means pass."""
    components = sbom.get("components")
    if components is None:
        return []
    if not isinstance(components, list):
        return ["sbom: components must be a list"]
    errors: list[str] = []
    for comp in components:
        if not isinstance(comp, dict):
            errors.append("sbom: component entry is not an object")
            continue
        name = _component_name(comp)
        licenses = comp.get("licenses")
        if licenses is None:
            continue
        if not isinstance(licenses, list):
            errors.append(f"{name}: licenses must be a list")
            continue
        for entry in licenses:
            if not isinstance(entry, dict):
                errors.append(f"{name}: license entry is not an object")
                continue
            for raw in _license_strings(entry):
                if raw.upper() in _IGNORED:
                    continue
                errors.extend(_judge_expression(name, raw, allowlist))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail if CycloneDX SBOM has disallowed licenses")
    parser.add_argument("--sbom", required=True, type=Path, help="CycloneDX JSON path")
    parser.add_argument("--allowlist", required=True, type=Path, help="SPDX allowlist path")
    args = parser.parse_args(argv)

    try:
        allowlist = load_allowlist(args.allowlist)
    except OSError as exc:
        print(f"license-gate: cannot read allowlist: {exc}", file=sys.stderr)
        return 1

    try:
        raw = args.sbom.read_text(encoding="utf-8")
        sbom = json.loads(raw)
    except OSError as exc:
        print(f"license-gate: cannot read sbom: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"license-gate: malformed sbom JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(sbom, dict):
        print("license-gate: sbom root must be an object", file=sys.stderr)
        return 1

    errors = evaluate(sbom, allowlist)
    if errors:
        for err in errors:
            print(f"license-gate: {err}", file=sys.stderr)
        return 1
    print("license-gate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
