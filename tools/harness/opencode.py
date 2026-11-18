"""OpenCode V2 checks: read-only native discovery and source-collision guard.

Loading a skill is not authorization. These checks only read the OpenCode CLI,
the user config and installed symlinks; they never change permissions or host
state.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from harness.base import Check

NATIVE_OPT_IN = "MR_OPENCODE_NATIVE_OPT_IN"
SKILL_API = "/api/skill"
_VERSION_RE = re.compile(r"\bv?(\d+)\.\d+")
_TIMEOUT_SECONDS = 60


def _strip_jsonc_comments(text: str) -> str:
    """Strip // and /* */ comments, then trailing commas before } or ]."""
    out: list[str] = []
    index, length = 0, len(text)
    in_string = False
    escaped = False
    while index < length:
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if text.startswith("//", index):
            while index < length and text[index] != "\n":
                index += 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = length if end == -1 else end + 2
            continue
        out.append(char)
        index += 1
    stripped = "".join(out)
    # Trailing commas are common in JSONC; strip outside strings only.
    cleaned: list[str] = []
    in_string = False
    escaped = False
    i = 0
    while i < len(stripped):
        ch = stripped[i]
        if in_string:
            cleaned.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            cleaned.append(ch)
            i += 1
            continue
        if ch == ",":
            j = i + 1
            while j < len(stripped) and stripped[j] in " \t\r\n":
                j += 1
            if j < len(stripped) and stripped[j] in "}]":
                i += 1
                continue
        cleaned.append(ch)
        i += 1
    return "".join(cleaned)


def _config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")) / "opencode"


def _config_sources(root: Path) -> list[Path]:
    names = ("opencode.json", "opencode.jsonc")
    candidates = [_config_home() / name for name in names]
    candidates.extend(root / name for name in names)
    candidates.extend(root / ".opencode" / name for name in names)
    return [path for path in candidates if path.is_file()]


def _registered_skills(path: Path) -> list[str]:
    try:
        data: dict[str, Any] = json.loads(_strip_jsonc_comments(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    entries = data.get("skills") or []
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, str)]


def _catalog_names(directory: Path) -> set[str]:
    if not directory.is_dir():
        return set()
    return {path.name for path in directory.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}


def opencode_source_collision_check(root: Path, source_root: Path, expected_skills: set[str]) -> Check:
    """An explicit config source wins by precedence; duplicates must be reported, not hidden."""
    catalog = expected_skills or _catalog_names((source_root or root).resolve() / "skills")
    collisions: list[str] = []
    for config in _config_sources(root):
        try:
            entries = _registered_skills(config)
        except ValueError as exc:
            return Check("opencode-source-collision", "contract", "fail", str(exc))
        for entry in entries:
            raw = os.path.expanduser(entry)
            candidate = Path(raw) if os.path.isabs(raw) else (root / raw)
            overlap = sorted(catalog & _catalog_names(candidate.resolve()))
            if overlap:
                collisions.append(f"{entry}: {', '.join(overlap)}")
    if collisions:
        return Check(
            "opencode-source-collision",
            "contract",
            "fail",
            "duplicate skill ids from config sources: " + "; ".join(collisions),
        )
    return Check("opencode-source-collision", "contract", "pass", "no duplicate registered catalog")


def _version_parts(binary: str) -> tuple[int | None, str]:
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"cannot read OpenCode version: {exc}"
    text = (proc.stdout or proc.stderr).strip()
    if proc.returncode != 0:
        return None, f"opencode --version failed: {text}"
    match = _VERSION_RE.search(text)
    return (int(match.group(1)) if match else None), text


def opencode_discovery_check(root: Path, expected_skills: set[str]) -> Check:
    """Native level B: the real CLI must list every catalog id, opt-in only."""
    if os.environ.get(NATIVE_OPT_IN) != "1":
        return Check("opencode-native-discovery", "B", "not_run", f"{NATIVE_OPT_IN}=1 required")
    binary = shutil.which("opencode")
    if binary is None:
        return Check("opencode-native-discovery", "B", "not_run", "opencode binary not on PATH")
    major, version_text = _version_parts(binary)
    if major != 2:
        return Check(
            "opencode-native-discovery",
            "B",
            "blocked",
            f"OpenCode V2 required (V1 config differs); version={version_text!r}",
        )
    try:
        proc = subprocess.run(
            [binary, "api", "get", SKILL_API],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return Check("opencode-native-discovery", "B", "fail", f"skill API call failed: {exc}")
    if proc.returncode != 0:
        return Check("opencode-native-discovery", "B", "fail", f"skill API failed: {(proc.stderr or '').strip()}")
    try:
        payload: dict[str, Any] = json.loads(proc.stdout)
        discovered = {str(item["id"]) for item in payload.get("data", []) if isinstance(item, dict) and "id" in item}
    except (json.JSONDecodeError, TypeError, KeyError) as exc:
        return Check("opencode-native-discovery", "B", "fail", f"invalid skill API response: {exc}")
    missing = sorted(expected_skills - discovered)
    if missing:
        return Check(
            "opencode-native-discovery",
            "B",
            "fail",
            f"missing catalog ids: {', '.join(missing)}",
        )
    return Check(
        "opencode-native-discovery",
        "B",
        "pass",
        f"OpenCode {version_text}: {len(discovered)} skills, {len(expected_skills)} catalog ids present",
    )
