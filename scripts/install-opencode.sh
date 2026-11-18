#!/bin/bash
# Symlink skills/ into OpenCode's project (.opencode/skills) or user
# (${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills) skills directory.
# User installs read the catalog from $HOME/.machineroom, like the other harnesses.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
OPCODE_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"

ARGS=()
for arg in "$@"; do
  ARGS+=("$arg")
done

# An explicit `skills` config entry has higher precedence than linked skills dirs.
# If it already registers a machineroom catalog, installing symlinks would create
# duplicate ids with the config source winning. Refuse instead of shadowing silently.
# Runs for both project and --user installs (fail closed).
check_config_conflict() {
  python3 - "$ROOT" "$OPCODE_CONFIG_HOME" <<'PY' || exit 1
import json
import os
import sys
from pathlib import Path

root, config_home = (Path(arg) for arg in sys.argv[1:3])
source = root / "skills"


def strip_jsonc(text: str) -> str:
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    escaped = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
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
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    stripped = "".join(out)
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


def skill_names(directory: Path) -> set[str]:
    if not directory.is_dir():
        return set()
    return {p.name for p in directory.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}


def config_sources() -> list[Path]:
    names = ("opencode.json", "opencode.jsonc")
    candidates = [config_home / name for name in names]
    candidates.extend(root / name for name in names)
    candidates.extend(root / ".opencode" / name for name in names)
    return [path for path in candidates if path.is_file()]


expected = skill_names(source)
if not expected:
    sys.exit(0)

for path in config_sources():
    try:
        data = json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot parse OpenCode config {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    entries = data.get("skills") or []
    if not isinstance(entries, list):
        continue
    for entry in entries:
        if not isinstance(entry, str):
            continue
        raw = os.path.expanduser(entry)
        # Resolve relatives against the project/repo root (parity with harness.opencode).
        candidate = Path(raw) if os.path.isabs(raw) else (root / raw)
        overlap = expected & skill_names(candidate.resolve())
        if overlap:
            print(
                "ERROR: OpenCode config registers catalog with duplicate skill ids "
                f"({', '.join(sorted(overlap))}) from {entry}; remove that 'skills' entry "
                "before installing symlinks",
                file=sys.stderr,
            )
            sys.exit(1)
PY
}
check_config_conflict

exec bash "$HERE/lib/link-skills.sh" \
  --installer "scripts/install-opencode.sh" \
  --default-target "$ROOT/.opencode/skills" \
  --user-target "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills" \
  --harness opencode \
  "${ARGS[@]}"
