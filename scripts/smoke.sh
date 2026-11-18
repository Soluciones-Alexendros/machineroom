#!/usr/bin/env bash
# Product smoke: verify the machine runtime (or a hermetic fixture) is usable.
#
# Default: inspect $HOME/.machineroom. Exit 1 when missing or incomplete.
# MR_SMOKE_FIXTURE=1: build a temporary runtime from this checkout (no network)
# and verify it — used by the CI canon job on runners without a home runtime.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

EXPECTED_SKILLS=14

smoke_check_runtime() {
  local runtime="$1"
  if [[ ! -d "$runtime" ]]; then
    echo "runtime not found: $runtime" >&2
    return 1
  fi
  local manifest="$runtime/.runtime-manifest.json"
  if [[ ! -f "$manifest" ]]; then
    echo "runtime manifest missing: $manifest" >&2
    return 1
  fi
  local version
  version=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$manifest")
  for relative in \
    skills \
    extensions/machineroom \
    .cursor/agents \
    .cursor/hooks \
    .cursor/rules \
    package.json \
    .cursor/hooks.json \
    tools/execution/__init__.py \
    tools/execution/deny_list.py
  do
    if [[ ! -e "$runtime/$relative" ]]; then
      echo "runtime payload incomplete: missing $relative" >&2
      return 1
    fi
  done
  local count
  count=$(find "$runtime/skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
  if [[ "$count" -ne "$EXPECTED_SKILLS" ]]; then
    echo "runtime catalog expected $EXPECTED_SKILLS skills, found $count" >&2
    return 1
  fi
  echo "smoke: runtime $version OK ($count skills)"
  return 0
}

if [[ "${MR_SMOKE_FIXTURE:-}" == "1" ]]; then
  WORK=$(mktemp -d /tmp/machineroom-smoke-XXXXXX)
  trap 'rm -rf "$WORK"' EXIT
  HOME="$WORK/home"
  mkdir -p "$HOME"
  PYTHONPATH="$ROOT/tools" HOME="$HOME" python3 - <<PY
import json
import shutil
from pathlib import Path

from harness.runtime import PAYLOAD_CURSOR, PAYLOAD_DIRS, PAYLOAD_FILES, install_verified_runtime

root = Path("$ROOT")
stage = Path("$WORK/stage")
for relative in (*PAYLOAD_DIRS, *PAYLOAD_CURSOR):
    shutil.copytree(root / relative, stage / relative, symlinks=False)
for relative in PAYLOAD_FILES:
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / relative, target)
version = json.loads((stage / "package.json").read_text(encoding="utf-8"))["version"]
install_verified_runtime(stage, Path("$HOME") / ".machineroom", version)
PY
  smoke_check_runtime "$HOME/.machineroom"
  exit 0
fi

RUNTIME="${HOME}/.machineroom"
if ! smoke_check_runtime "$RUNTIME"; then
  exit 1
fi
exit 0
