#!/usr/bin/env bash
# Native OpenCode level B on a temporary project. Level A is the static
# symlink gate; B requires a real OpenCode V2 binary and an explicit opt-in.
# Exit 3 means blocked/not_run, never PASS.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v opencode >/dev/null 2>&1; then
  echo "blocked: opencode binary not on PATH" >&2
  exit 3
fi

VERSION=$(opencode --version)
echo "opencode --version → ${VERSION}"
if ! printf '%s' "$VERSION" | grep -Eq 'v?2\.[0-9]+'; then
  echo "blocked: OpenCode V2 required (V1 config differs): ${VERSION}" >&2
  exit 3
fi
if [ "${MR_OPENCODE_NATIVE_OPT_IN:-0}" != "1" ]; then
  echo "not_run: MR_OPENCODE_NATIVE_OPT_IN=1 required" >&2
  exit 3
fi

TMP=$(mktemp -d /tmp/machineroom-opencode-native-XXXXXX)
cleanup() {
  rm -rf "$TMP"
}
trap cleanup EXIT
mkdir -p "$TMP/project" "$TMP/home" "$TMP/xdg"
export HOME="$TMP/home"
export XDG_CONFIG_HOME="$TMP/xdg"

bash "$ROOT/scripts/install.sh" --harness opencode \
  --target "$TMP/project" --yes --json >"$TMP/install.json"
python3 - "$TMP/install.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["harness"] == "opencode", data
assert data["installed"] == 14, data
assert data["status"] == "ok", data
print("OpenCode A install:", data["installed"], "skills")
PY

DOCTOR="uv run --project $ROOT/tools --frozen python $ROOT/tools/harness/doctor.py --source $ROOT"

$DOCTOR --harness opencode --target "$TMP/project" --json >"$TMP/static.json"
python3 - "$TMP/static.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
by_id = {check["id"]: check for check in report["checks"]}
assert by_id["opencode-skill-links"]["outcome"] == "pass", by_id
assert by_id["opencode-source-collision"]["outcome"] == "pass", by_id
assert report["outcome"] == "pass", report
print("OpenCode A static:", by_id["opencode-skill-links"]["detail"])
PY

set +e
$DOCTOR --harness opencode --target "$TMP/project" --native --json >"$TMP/native.json"
native_rc=$?
set -e
echo "doctor --native exit=${native_rc}"
python3 - "$TMP/native.json" "$native_rc" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
by_id = {check["id"]: check for check in report["checks"]}
assert by_id["opencode-skill-links"]["outcome"] == "pass", by_id
assert by_id["opencode-native-discovery"]["outcome"] == "pass", by_id
assert report["capabilities"].get("B") == "pass", report
assert int(sys.argv[2]) == 0, sys.argv[2]
print("OpenCode B native:", by_id["opencode-native-discovery"]["detail"])
PY

# The ids must resolve to the links we installed, not to a foreign catalog.
(
  cd "$TMP/project"
  opencode api get /api/skill >"$TMP/skills-api.json"
)
python3 - "$TMP/skills-api.json" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
data = payload.get("data") or []
by_id = {entry["id"]: entry for entry in data if isinstance(entry, dict) and "id" in entry}
expected = {
    "local-maintenance", "local-security", "plan-specification", "plan-testing",
    "project-architecture", "project-machineroom", "project-status", "role-back",
    "role-clean-code", "role-front", "role-linux", "web-compliance", "web-owasp",
    "web-performance",
}
missing = sorted(expected - set(by_id))
assert not missing, missing
# The CLI talks to the operator's running service; its context may be another
# project, so paths are reported but source provenance is proven by level A.
for skill_id in ("local-maintenance", "role-linux", "web-owasp"):
    print(f"  {skill_id} → {by_id[skill_id].get('path', '')}")
print("OpenCode skill API lists the 14 catalog ids")
PY

# Without opt-in B is not_run (exit 3), never PASS.
set +e
env -u MR_OPENCODE_NATIVE_OPT_IN $DOCTOR --harness opencode \
  --target "$TMP/project" --native --json >"$TMP/native-no-optin.json"
no_optin_rc=$?
set -e
python3 - "$TMP/native-no-optin.json" "$no_optin_rc" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
by_id = {check["id"]: check for check in report["checks"]}
assert by_id["opencode-native-discovery"]["outcome"] == "not_run", by_id
assert int(sys.argv[2]) == 3, sys.argv[2]
print("OpenCode B without opt-in: not_run")
PY

# A broken link must fail level A even when --native is requested.
rm -f "$TMP/project/.opencode/skills/role-linux"
set +e
$DOCTOR --harness opencode --target "$TMP/project" --json >"$TMP/static-broken.json"
broken_rc=$?
set -e
python3 - "$TMP/static-broken.json" "$broken_rc" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
by_id = {check["id"]: check for check in report["checks"]}
assert by_id["opencode-skill-links"]["outcome"] == "fail", by_id
assert int(sys.argv[2]) == 1, sys.argv[2]
print("OpenCode A broken link: fail")
PY

set +e
MR_OPENCODE_NATIVE_OPT_IN=1 $DOCTOR --harness opencode --target "$TMP/project" --native --json \
  >"$TMP/native-broken.json"
native_broken_rc=$?
set -e
python3 - "$TMP/native-broken.json" "$native_broken_rc" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
by_id = {check["id"]: check for check in report["checks"]}
assert by_id["opencode-skill-links"]["outcome"] == "fail", by_id
assert int(sys.argv[2]) == 1, sys.argv[2]
print("OpenCode A+B with broken link: fail (links not skipped)")
PY

echo "OpenCode native A/B tests OK"
