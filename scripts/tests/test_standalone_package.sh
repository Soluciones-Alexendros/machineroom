#!/bin/bash
# V34–V35: standalone package runs without source PYTHONPATH
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

DEST="$TMP/pkg"
mkdir -p "$DEST"

# Reject relative dest
if bash "$ROOT/scripts/package-standalone-skill.sh" --skill local-maintenance --dest relative 2>/dev/null; then
  echo "FAIL: relative dest should be rejected"; exit 1
fi

# Reject escape skill name
if bash "$ROOT/scripts/package-standalone-skill.sh" --skill '../evil' --dest "$DEST/x" 2>/dev/null; then
  echo "FAIL: escape skill should be rejected"; exit 1
fi

bash "$ROOT/scripts/package-standalone-skill.sh" --skill local-maintenance --dest "$DEST"
test -f "$DEST/local-maintenance/SKILL.md"
test -f "$DEST/local-maintenance/vendor/execution/ops.py"

# P11 T3: skill that cites canon docs must vendor those files
DEST2="$TMP/pkg-plan"
mkdir -p "$DEST2"
bash "$ROOT/scripts/package-standalone-skill.sh" --skill project-status --dest "$DEST2"
test -f "$DEST2/project-status/SKILL.md"
# project-status references point at docs/architecture/decisions/ADR-0016…
if ! find "$DEST2/project-status/vendor/canon" -type f -name 'ADR-0016*.md' | grep -q .; then
  echo "FAIL: expected vendored ADR-0016 under vendor/canon"; find "$DEST2/project-status/vendor/canon" -type f | head
  exit 1
fi
echo "canon vendor OK"

# Move package and run with clean env (no ROOT/tools on PYTHONPATH)
MOVED="$TMP/moved"
mv "$DEST" "$MOVED"
# Make source tools unreadable via empty PYTHONPATH and cwd outside repo
cd "$MOVED"
python3 - <<'PY'
import sys, os
from pathlib import Path
# Only vendor on path — prove autonomy
vendor = Path("local-maintenance/vendor").resolve()
sys.path.insert(0, str(vendor))
# Ensure repo tools not accidentally present
checkout = os.environ.get("CHECKOUT_NAME", "machineroom")
# Drop the checkout's own tools/ package, but keep site-packages (the venv may
# live under <checkout>/tools/.venv and still provides third-party modules).
needle = f"{checkout}/tools"
sys.path = [
    p for p in sys.path
    if not p.replace("\\", "/").rstrip("/").endswith(needle)
]
from execution.ops import run_registered
from execution.approval import DenyProvider
import execution.ops as ops
ops.provider_from_env = lambda: DenyProvider()
r = run_registered("clean_journal", {"snapshot_id": "s"}, target="/")
assert r.outcome == "blocked", r
print("standalone deny OK", r.detail[:40])
PY

echo "standalone package tests PASS"
