#!/usr/bin/env bash
# Hermetic cross-version install: current checkout installs a release whose
# PAYLOAD_FILES matches v9.0.2 (no tools/structured_failure.py in the list).
# Fails if the installer still applies the checkout's PAYLOAD_FILES to the extract.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
VERSION=$(python3 -c 'import json; print(json.load(open("package.json"))["version"])')
TMP=$(mktemp -d /tmp/machineroom-cross-version-XXXXXX)
trap 'rm -rf "$TMP"' EXIT

PACKAGE="$TMP/package/machineroom-${VERSION}"
RELEASE="$TMP/release"
mkdir -p "$PACKAGE" "$RELEASE" "$TMP/bin"

git -C "$ROOT" archive --format=tar HEAD | tar -x -C "$PACKAGE"
# Swap in the published v9.0.2 installer contract (standalone InstallFailure + older PAYLOAD_FILES).
git -C "$ROOT" show v9.0.2:tools/harness/runtime.py >"$PACKAGE/tools/harness/runtime.py"
# package.json must declare the version we install; keep HEAD's version for the tag name.
# Remove files the v9.0.2 contract never shipped in PAYLOAD_FILES so a checkout-PYTHONPATH
# install against this extract fails the same way as a real older release.
rm -f "$PACKAGE/tools/structured_failure.py" "$PACKAGE/scripts/runtime-sync.sh"

tar -czf "$RELEASE/machineroom-${VERSION}.tar.gz" -C "$TMP/package" "machineroom-${VERSION}"
(
  cd "$RELEASE"
  sha256sum "machineroom-${VERSION}.tar.gz" > SHA256SUMS
)

cat >"$TMP/bin/gh" <<'PY'
#!/usr/bin/env python3
import os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
if args[:2] == ["release", "download"]:
    destination = Path(args[args.index("--dir") + 1])
    for name in os.environ["MR_CROSS_VERSION_RELEASE_DIR"].split(os.pathsep):
        source = Path(name)
        for item in source.iterdir():
            if item.is_file():
                shutil.copyfile(item, destination / item.name)
    raise SystemExit(0)
if args[:2] == ["attestation", "verify"]:
    raise SystemExit(0)
if args[:2] == ["release", "list"]:
    version = os.environ.get("MR_CROSS_VERSION_VERSION", "0.0.0")
    tag = f"v{version}"
    # Honour --jq used by runtime-sync.sh resolve_latest_version.
    if "--jq" in args:
        print(tag)
    else:
        print(f'[{{"tagName":"{tag}","isPrerelease":false,"isDraft":false}}]')
    raise SystemExit(0)
raise SystemExit(2)
PY
chmod +x "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MR_BOOTSTRAP_REPOSITORY="fixture/machineroom"
export MR_CROSS_VERSION_RELEASE_DIR="$RELEASE"
export MR_CROSS_VERSION_VERSION="$VERSION"

HOME="$TMP/home-ok"
mkdir -p "$HOME"
OUT=$(HOME="$HOME" bash "$ROOT/scripts/runtime-sync.sh" install --version "$VERSION" --json)
echo "$OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok", d; print("cross-version install OK:", d["version"], d["digest"][:12])'
test -f "$HOME/.machineroom/tools/execution/deny_list.py"
test ! -e "$HOME/.machineroom/tools/structured_failure.py"
test ! -e "$HOME/.machineroom/scripts/runtime-sync.sh"
echo "payload shape OK for 9.0.2-like contract"

# Negative: remove a stable required file from the fixture archive.
BAD="$TMP/bad-release"
mkdir -p "$BAD"
BAD_PKG="$TMP/bad-package/machineroom-${VERSION}"
mkdir -p "$BAD_PKG"
git -C "$ROOT" archive --format=tar HEAD | tar -x -C "$BAD_PKG"
git -C "$ROOT" show v9.0.2:tools/harness/runtime.py >"$BAD_PKG/tools/harness/runtime.py"
rm -f "$BAD_PKG/tools/structured_failure.py" "$BAD_PKG/scripts/runtime-sync.sh"
rm -f "$BAD_PKG/tools/execution/deny_list.py"
tar -czf "$BAD/machineroom-${VERSION}.tar.gz" -C "$TMP/bad-package" "machineroom-${VERSION}"
(
  cd "$BAD"
  sha256sum "machineroom-${VERSION}.tar.gz" > SHA256SUMS
)
HOME_BAD="$TMP/home-bad"
mkdir -p "$HOME_BAD"
set +e
BAD_OUT=$(MR_CROSS_VERSION_RELEASE_DIR="$BAD" HOME="$HOME_BAD" bash "$ROOT/scripts/runtime-sync.sh" install --version "$VERSION" --json 2>"$TMP/bad.err")
BAD_RC=$?
set -e
test "$BAD_RC" -ne 0
echo "$BAD_OUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["status"]=="failed", d
detail=d["failures"][0]["detail"]
assert "tools/execution/deny_list.py" in detail, detail
assert "traceback" not in detail.lower()
print("cross-version negative OK:", detail)
'
test ! -e "$HOME_BAD/.machineroom"

# Prove the gate bites: forcing checkout PYTHONPATH against the 9.0.2-like extract fails.
HOME_REGRESS="$TMP/home-regress"
mkdir -p "$HOME_REGRESS"
WORK=$(mktemp -d /tmp/machineroom-regress-XXXXXX)
trap 'rm -rf "$TMP" "$WORK"' EXIT
cp "$RELEASE/machineroom-${VERSION}.tar.gz" "$WORK/"
PYTHONPATH="$ROOT/tools" python3 -m harness.bootstrap "$WORK/machineroom-${VERSION}.tar.gz" "$WORK/extracted"
PACKAGE_EXTRACTED="$WORK/extracted/machineroom-${VERSION}"
set +e
REGRESS=$(
  HOME="$HOME_REGRESS" PYTHONPATH="$ROOT/tools" \
    MR_INSTALL_PACKAGE="$PACKAGE_EXTRACTED" MR_INSTALL_RUNTIME="$HOME_REGRESS/.machineroom" MR_INSTALL_VERSION="$VERSION" \
    python3 - <<'PY'
import json, os, sys
from pathlib import Path
from harness.runtime import InstallFailure, install_verified_runtime
try:
    install_verified_runtime(
        Path(os.environ["MR_INSTALL_PACKAGE"]),
        Path(os.environ["MR_INSTALL_RUNTIME"]),
        os.environ["MR_INSTALL_VERSION"],
    )
except InstallFailure as exc:
    print(json.dumps({"status": "failed", "failures": [exc.to_dict()]}))
    raise SystemExit(1) from None
print(json.dumps({"status": "ok"}))
PY
)
REGRESS_RC=$?
set -e
test "$REGRESS_RC" -ne 0
echo "$REGRESS" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["status"]=="failed"
detail=d["failures"][0]["detail"]
assert "structured_failure.py" in detail or "runtime-sync.sh" in detail, detail
print("checkout-PYTHONPATH regression OK:", detail)
'

# update --latest dry-run against the same fixture (no runtime write)
HOME_UPDATE="$TMP/home-update"
mkdir -p "$HOME_UPDATE"
DRY=$(HOME="$HOME_UPDATE" bash "$ROOT/scripts/runtime-sync.sh" update --latest --dry-run --json)
echo "$DRY" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["status"]=="simulated", d
assert d["action"]=="update", d
assert "digest" in d and "asset_sha256" in d
print("update --latest --dry-run OK:", d["version"], d["digest"][:12])
'
test ! -e "$HOME_UPDATE/.machineroom"

# Self-update entry: payload-only runtime can invoke update against the fixture.
# Build a current-contract runtime that includes scripts/runtime-sync.sh.
HOME_SELF="$TMP/home-self"
mkdir -p "$HOME_SELF"
PYTHONPATH="$ROOT/tools" HOME="$HOME_SELF" python3 - <<PY
import json
from pathlib import Path
from harness.runtime import PAYLOAD_CURSOR, PAYLOAD_DIRS, PAYLOAD_FILES, install_verified_runtime
import shutil
stage = Path("$TMP/self-stage")
root = Path("$ROOT")
for relative in (*PAYLOAD_DIRS, *PAYLOAD_CURSOR):
    shutil.copytree(root / relative, stage / relative, symlinks=False)
for relative in PAYLOAD_FILES:
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / relative, target)
version = json.loads((stage / "package.json").read_text())["version"]
install_verified_runtime(stage, Path("$HOME_SELF") / ".machineroom", version)
PY
# Point update at a same-version fixture built with the CURRENT contract so install succeeds.
CUR="$TMP/current-release"
CUR_PKG="$TMP/current-package/machineroom-${VERSION}"
mkdir -p "$CUR" "$CUR_PKG"
# Working-tree payload (not git archive): includes uncommitted PAYLOAD_FILES changes.
PYTHONPATH="$ROOT/tools" python3 - <<PY
import json
import shutil
from pathlib import Path
from harness.runtime import PAYLOAD_CURSOR, PAYLOAD_DIRS, PAYLOAD_FILES

root = Path("$ROOT")
stage = Path("$CUR_PKG")
# Minimal package tree for install_verified_runtime + bootstrap extract layout.
for relative in (*PAYLOAD_DIRS, *PAYLOAD_CURSOR):
    shutil.copytree(root / relative, stage / relative, symlinks=False)
for relative in PAYLOAD_FILES:
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / relative, target)
# Harness import path for the extracted installer.
shutil.copytree(root / "tools" / "harness", stage / "tools" / "harness", dirs_exist_ok=True)
shutil.copy2(root / "tools" / "structured_failure.py", stage / "tools" / "structured_failure.py")
(stage / "tools" / "harness" / "bootstrap.py").stat()  # ensure extract helper exists
PY
tar -czf "$CUR/machineroom-${VERSION}.tar.gz" -C "$TMP/current-package" "machineroom-${VERSION}"
(
  cd "$CUR"
  sha256sum "machineroom-${VERSION}.tar.gz" > SHA256SUMS
)
SELF_OUT=$(
  MR_CROSS_VERSION_RELEASE_DIR="$CUR" HOME="$HOME_SELF" \
    bash "$HOME_SELF/.machineroom/scripts/runtime-sync.sh" update --latest --json
)
echo "$SELF_OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok", d; print("runtime self-update OK:", d["version"])'
# Idempotent second run
SELF_OUT2=$(
  MR_CROSS_VERSION_RELEASE_DIR="$CUR" HOME="$HOME_SELF" \
    bash "$HOME_SELF/.machineroom/scripts/runtime-sync.sh" update --latest --json
)
echo "$SELF_OUT2" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok", d; print("runtime self-update idempotent OK")'

echo "test_runtime_cross_version: PASS"
