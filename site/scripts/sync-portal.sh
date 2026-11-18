#!/usr/bin/env bash
# Checkout the pinned alexendros.dev commit and copy its theme script.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PIN="$ROOT/site/portal.pin"
DEST="$ROOT/site/.portal"
CACHE="${PORTAL_CHECKOUT:-$HOME/Work/web/alexendros.dev}"

SHA="$(
  uv run --project "$ROOT/tools" python3 - "$PIN" <<'PY'
import sys
from pathlib import Path
import yaml

data = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
sha = data.get("sha") if isinstance(data, dict) else None
if not isinstance(sha, str) or len(sha) != 40:
    raise SystemExit("site/portal.pin sha must be 40 hex")
print(sha)
PY
)"

if [[ -d "$DEST/.git" ]] && [[ "$(git -C "$DEST" rev-parse HEAD)" == "$SHA" ]]; then
  echo "portal cache: $SHA"
else
  rm -rf "$DEST"
  mkdir -p "$DEST"
  git -C "$DEST" init
  if [[ -d "$CACHE/.git" ]] && git -C "$CACHE" cat-file -e "${SHA}^{commit}" 2>/dev/null; then
    git -C "$DEST" remote add origin "$CACHE"
  else
    git -C "$DEST" remote add origin https://github.com/Alexendros/alexendros.dev.git
  fi
  git -C "$DEST" fetch --depth 1 origin "$SHA"
  git -C "$DEST" checkout --detach FETCH_HEAD
fi

test "$(git -C "$DEST" rev-parse HEAD)" = "$SHA"

uv run --project "$ROOT/tools" python3 - "$PIN" "$DEST/package.json" "$ROOT/site/package.json" "$DEST" <<'PY'
import json
import sys
from pathlib import Path
import yaml

pin_path, portal_pkg, site_pkg, dest = sys.argv[1:]
pin = yaml.safe_load(Path(pin_path).read_text(encoding="utf-8"))
paths = pin.get("paths") if isinstance(pin, dict) else None
versions = pin.get("versions") if isinstance(pin, dict) else None
if not isinstance(paths, list) or not isinstance(versions, dict):
    raise SystemExit("portal.pin needs paths and versions")
root = Path(dest)
for rel in paths:
    if not isinstance(rel, str) or not (root / rel).is_file():
        raise SystemExit(f"pinned path missing: {rel}")

def spec(path: Path, name: str) -> str | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("dependencies", "devDependencies"):
        block = data.get(key) or {}
        if isinstance(block, dict) and name in block:
            return str(block[name])
    return None

for name, expected in versions.items():
    for label, path in (("portal", Path(portal_pkg)), ("site", Path(site_pkg))):
        found = spec(path, name)
        if found != expected:
            raise SystemExit(f"{label} {name}: expected {expected}, found {found}")
print("portal pin ok")
PY

mkdir -p "$ROOT/site/public"
cp "$DEST/src/scripts/theme-init.js" "$ROOT/site/public/theme-init.js"
