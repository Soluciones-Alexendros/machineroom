#!/usr/bin/env bash
# End-to-end bootstrap tests with a local release fixture; no network or real release.
# Fixture is built with `git archive HEAD` so it matches a published tarball layout.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
VERSION=$(python3 -c 'import json; print(json.load(open("package.json"))["version"])' "$ROOT")
TMP=$(mktemp -d /tmp/machineroom-bootstrap-test-XXXXXX)
trap 'rm -rf "$TMP"' EXIT
RELEASE="$TMP/release"
PACKAGE_ROOT="$TMP/package"
PACKAGE="$PACKAGE_ROOT/machineroom-${VERSION}"
mkdir -p "$PACKAGE_ROOT" "$RELEASE" "$TMP/bin"
git -C "$ROOT" archive --format=tar --prefix="machineroom-${VERSION}/" HEAD | tar -x -C "$PACKAGE_ROOT"
# Overlay working-tree harness so uncommitted doctor/runtime fixes are in the fixture.
cp -a "$ROOT/tools/harness/." "$PACKAGE/tools/harness/"
cp -a "$ROOT/tools/structured_failure.py" "$PACKAGE/tools/structured_failure.py"
mkdir -p "$PACKAGE/scripts"
cp -a "$ROOT/scripts/runtime-sync.sh" "$PACKAGE/scripts/runtime-sync.sh"
tar -czf "$RELEASE/machineroom-${VERSION}.tar.gz" -C "$PACKAGE_ROOT" "machineroom-${VERSION}"
(
  cd "$RELEASE"
  sha256sum "machineroom-${VERSION}.tar.gz" > SHA256SUMS
)

cat >"$TMP/bin/gh" <<'PY'
#!/usr/bin/env python3
import os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
if args[0] == "release" and args[1] == "download":
    destination = Path(args[args.index("--dir") + 1])
    for name in os.environ["AW_BOOTSTRAP_RELEASE_DIR"].split(os.pathsep):
        source = Path(name)
        for item in source.iterdir():
            if item.is_file():
                shutil.copyfile(item, destination / item.name)
    raise SystemExit(0)
if args[0] == "attestation" and args[1] == "verify":
    raise SystemExit(1 if os.environ.get("AW_FIXTURE_ATTESTATION_FAIL") == "1" else 0)
raise SystemExit(2)
PY
chmod +x "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MR_BOOTSTRAP_REPOSITORY="fixture/machineroom"
export AW_BOOTSTRAP_RELEASE_DIR="$RELEASE"

DRY_TARGET="$TMP/dry-target"
DRY=$(bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor --target "$DRY_TARGET" --dry-run --json)
echo "$DRY" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="simulated" and d["dry_run"] is True'
test ! -e "$DRY_TARGET"

if command -v pi >/dev/null 2>&1; then
  HOME="$TMP/home-pi" bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness pi \
    --target "$TMP/project-pi" --json >"$TMP/pi.json"
  python3 - "$TMP/pi.json" <<'PY'
import json,sys
result=json.load(open(sys.argv[1]))
assert result["status"]=="installed" and result["doctor"]=="pass", result
print("bootstrap Pi + native doctor: PASS")
PY
else
  echo "not_run: Pi binary not found — skipping Pi bootstrap lane (Cursor lane still required)"
fi

bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/project-cursor" --json >"$TMP/cursor.json"
python3 - "$TMP/cursor.json" <<'PY'
import json,sys
result=json.load(open(sys.argv[1]))
assert result["status"]=="installed" and result["doctor"]=="pass", result
print("bootstrap Cursor full + doctor: PASS")
PY

# Checksum mismatch must stop before target installation.
BAD_SUM="$TMP/bad-sum"
cp -a "$RELEASE" "$BAD_SUM"
printf 'tampered' >> "$BAD_SUM/machineroom-${VERSION}.tar.gz"
if AW_BOOTSTRAP_RELEASE_DIR="$BAD_SUM" bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/bad-sum-target" --json >/dev/null 2>&1; then
  echo "FAIL: checksum mismatch accepted"; exit 1
fi
test ! -e "$TMP/bad-sum-target/.cursor"

# Attestation denial must stop before target installation.
if AW_FIXTURE_ATTESTATION_FAIL=1 bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/denied-target" --json >/dev/null 2>&1; then
  echo "FAIL: attestation denial accepted"; exit 1
fi
test ! -e "$TMP/denied-target/.cursor"

# Hostile archive with valid checksum must be rejected by the confined extractor.
HOSTILE="$TMP/hostile"
cp -a "$RELEASE" "$HOSTILE"
python3 - "$HOSTILE/machineroom-${VERSION}.tar.gz" <<'PY'
import io, sys, tarfile
path=sys.argv[1]
with tarfile.open(path, "w:gz") as archive:
    info=tarfile.TarInfo("../escape.txt")
    payload=b"escape"
    info.size=len(payload)
    archive.addfile(info, io.BytesIO(payload))
PY
(
  cd "$HOSTILE"
  sha256sum "machineroom-${VERSION}.tar.gz" > SHA256SUMS
)
if AW_BOOTSTRAP_RELEASE_DIR="$HOSTILE" bash "$ROOT/scripts/bootstrap.sh" --version "$VERSION" --harness cursor \
  --target "$TMP/hostile-target" --json >/dev/null 2>&1; then
  echo "FAIL: hostile archive accepted"; exit 1
fi
test ! -e "$TMP/hostile-target/.cursor"

# Incomplete payload: drop a PAYLOAD_FILES member and expect install_verified-style failure
# when syncing via the current harness (controlled failure, not a traceback).
INCOMPLETE="$TMP/incomplete-package/machineroom-${VERSION}"
mkdir -p "$TMP/incomplete-package"
git -C "$ROOT" archive --format=tar --prefix="machineroom-${VERSION}/" HEAD | tar -x -C "$TMP/incomplete-package"
rm -f "$INCOMPLETE/tools/structured_failure.py"
set +e
INCOMPLETE_ERR=$(
  PYTHONPATH="$ROOT/tools" python3 - <<PY
from pathlib import Path
from harness.runtime import InstallFailure, require_payload_present
try:
    require_payload_present(Path("$INCOMPLETE"), origin="release:$VERSION")
except InstallFailure as exc:
    print(exc.detail)
    raise SystemExit(1)
raise SystemExit(0)
PY
)
INCOMPLETE_RC=$?
set -e
test "$INCOMPLETE_RC" -ne 0
echo "$INCOMPLETE_ERR" | grep -q "tools/structured_failure.py"
echo "$INCOMPLETE_ERR" | grep -q "release $VERSION"
echo "incomplete payload detection: PASS"

echo "bootstrap tests OK"
