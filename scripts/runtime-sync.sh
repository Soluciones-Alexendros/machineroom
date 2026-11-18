#!/usr/bin/env bash
# Materialize the machine runtime at $HOME/.machineroom from a verified release.
# `sync` refuses that path: the development checkout stays in the working tree.
# Migrates a legacy $HOME/.autoworkspace once (D2/H2: no two runtimes).
#
# Install/update always run the extracted release's harness.runtime (PYTHONPATH
# under the package tree), so a newer checkout can install an older release.
# Extraction uses the checkout bootstrap when present; otherwise a stdlib
# safe-extract so ~/.machineroom/scripts/runtime-sync.sh can self-update.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CMD="${1:-}"
shift || true
FROM="$ROOT"
VERSION=""
LATEST=false
DRY_RUN=false
JSON_OUT=false
HOME_DIR="${HOME}"
REPOSITORY="${MR_BOOTSTRAP_REPOSITORY:-${AW_BOOTSTRAP_REPOSITORY:-Soluciones-Alexendros/machineroom}}"
RUNTIME_NAME=".machineroom"
LEGACY_RUNTIME_NAME=".autoworkspace"

usage() {
  cat <<EOF
Usage:
  bash scripts/runtime-sync.sh install --version X.Y.Z [--dry-run] [--json]
  bash scripts/runtime-sync.sh update --latest [--dry-run] [--json]
  bash scripts/runtime-sync.sh update --version X.Y.Z [--dry-run] [--json]
  bash scripts/runtime-sync.sh sync [--from CHECKOUT] [--dry-run] [--json]
    Refused for \$HOME/.machineroom. That directory is a verified release,
    not a copy of the development checkout.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --latest) LATEST=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --json) JSON_OUT=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

RUNTIME="${HOME_DIR}/${RUNTIME_NAME}"
LEGACY_RUNTIME="${HOME_DIR}/${LEGACY_RUNTIME_NAME}"

if [[ "$CMD" != "sync" && "$CMD" != "install" && "$CMD" != "update" ]]; then
  usage
  exit 2
fi

if [[ -L "$RUNTIME" ]]; then
  echo "ERROR: runtime must be a real directory, not a symlink: $RUNTIME" >&2
  exit 1
fi

migrate_legacy() {
  if [[ -e "$LEGACY_RUNTIME" || -L "$LEGACY_RUNTIME" ]]; then
    if [[ -e "$RUNTIME" || -L "$RUNTIME" ]]; then
      echo "ERROR: two runtimes present: $LEGACY_RUNTIME and $RUNTIME; remove one" >&2
      exit 1
    fi
    if [[ -L "$LEGACY_RUNTIME" ]]; then
      echo "ERROR: legacy runtime must be a real directory, not a symlink: $LEGACY_RUNTIME" >&2
      exit 1
    fi
    if [[ "$DRY_RUN" == true ]]; then
      echo "dry-run: would move $LEGACY_RUNTIME -> $RUNTIME" >&2
      return 0
    fi
    mv -- "$LEGACY_RUNTIME" "$RUNTIME"
    echo "Migrated legacy runtime: $LEGACY_RUNTIME -> $RUNTIME" >&2
  fi
}

migrate_legacy

if [[ "$CMD" == "sync" ]]; then
  FROM=$(cd "$FROM" && pwd)
  if [[ "$DRY_RUN" == true ]]; then
    echo "ERROR: home runtime only accepts a verified release (bash scripts/runtime-sync.sh install --version X.Y.Z); the development checkout stays in the working tree" >&2
    if [[ "$JSON_OUT" == true ]]; then
      printf '{"status":"failed","action":"sync","runtime":"%s"}\n' "$RUNTIME"
    fi
    exit 1
  fi
  export MR_SYNC_FROM="$FROM"
  export MR_SYNC_RUNTIME="$RUNTIME"
  set +e
  RESULT=$(PYTHONPATH="$ROOT/tools" JSON_OUT="$JSON_OUT" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path
from harness.runtime import InstallFailure, format_failure, sync_payload

from_path = Path(os.environ["MR_SYNC_FROM"])
runtime = Path(os.environ["MR_SYNC_RUNTIME"])
json_out = os.environ.get("JSON_OUT") == "true"
try:
    manifest = sync_payload(from_path, runtime, origin="sync")
except InstallFailure as exc:
    print(format_failure(exc.component, exc.function, exc.detail), file=sys.stderr)
    if json_out:
        print(json.dumps({"status": "failed", "action": "sync", "runtime": str(runtime), "failures": [exc.to_dict()]}))
    raise SystemExit(1) from None
print(json.dumps({"status": "ok", "action": "sync", "runtime": str(runtime), **manifest}))
PY
)
  RC=$?
  set -e
  if [[ "$RC" -ne 0 ]]; then
    if [[ "$JSON_OUT" == true && -n "$RESULT" ]]; then
      echo "$RESULT"
    fi
    exit "$RC"
  fi
  if [[ "$JSON_OUT" == true ]]; then
    echo "$RESULT"
  else
    echo "Synced runtime at $RUNTIME"
    printf '%s\n' "$RESULT" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("version=%s digest=%s…" % (d["version"], d["digest"][:12]))'
  fi
  exit 0
fi

require_deps() {
  for dependency in gh python3; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
      echo "not_run: required dependency not found: $dependency" >&2
      if [[ "$JSON_OUT" == true ]]; then
        printf '{"status":"not_run","action":"%s","detail":"required dependency not found: %s"}\n' "$CMD" "$dependency"
      fi
      exit 3
    fi
  done
}

resolve_latest_version() {
  local tag
  tag=$(gh release list --repo "$REPOSITORY" --limit 50 --json tagName,isPrerelease,isDraft \
    --jq '[.[] | select(.isPrerelease|not) | select(.isDraft|not) | .tagName | select(test("^v[0-9]+\\.[0-9]+\\.[0-9]+$"))] | first')
  if [[ -z "$tag" ]]; then
    echo "ERROR: no exact SemVer release found for $REPOSITORY" >&2
    exit 1
  fi
  VERSION="${tag#v}"
}

if [[ "$CMD" == "update" ]]; then
  if [[ "$LATEST" == true && -n "$VERSION" ]]; then
    echo "ERROR: use either --latest or --version, not both" >&2
    exit 2
  fi
  if [[ "$LATEST" != true && -z "$VERSION" ]]; then
    echo "ERROR: update requires --latest or --version X.Y.Z" >&2
    usage
    exit 2
  fi
  require_deps
  if [[ "$LATEST" == true ]]; then
    resolve_latest_version
  fi
elif [[ -z "$VERSION" ]]; then
  echo "ERROR: --version must be an exact SemVer release" >&2
  exit 2
fi

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
  echo "ERROR: --version must be an exact SemVer release" >&2
  exit 2
fi

require_deps

WORK=$(mktemp -d /tmp/machineroom-runtime-XXXXXX)
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT
ARCHIVE="$WORK/machineroom-${VERSION}.tar.gz"
gh release download "v${VERSION}" --repo "$REPOSITORY" \
  --pattern "machineroom-${VERSION}.tar.gz" --pattern "SHA256SUMS" --dir "$WORK"
(
  cd "$WORK"
  if [[ "$JSON_OUT" == true ]]; then
    sha256sum -c SHA256SUMS >/dev/null
  else
    sha256sum -c SHA256SUMS
  fi
)
ASSET_SHA256=$(sha256sum "$ARCHIVE" | awk '{print $1}')
if [[ "$JSON_OUT" == true ]]; then
  gh attestation verify "$ARCHIVE" -R "$REPOSITORY" >/dev/null
else
  gh attestation verify "$ARCHIVE" -R "$REPOSITORY"
fi

extract_release() {
  local archive="$1"
  local destination="$2"
  if [[ -f "$ROOT/tools/harness/bootstrap.py" ]]; then
    if [[ "$JSON_OUT" == true ]]; then
      PYTHONPATH="$ROOT/tools" python3 -m harness.bootstrap "$archive" "$destination" >/dev/null
    else
      PYTHONPATH="$ROOT/tools" python3 -m harness.bootstrap "$archive" "$destination"
    fi
    return
  fi
  ARCHIVE_PATH="$archive" EXTRACT_DEST="$destination" python3 - <<'PY'
import os
import shutil
import tarfile
from pathlib import Path, PurePosixPath

archive_path = Path(os.environ["ARCHIVE_PATH"]).resolve()
destination = Path(os.environ["EXTRACT_DEST"]).resolve()
if destination.exists():
    raise SystemExit(f"ERROR: extraction destination must be new: {destination}")
max_files = 10_000
max_total_bytes = 100 * 1024 * 1024
with tarfile.open(archive_path, "r:gz") as archive:
    members = archive.getmembers()
    if len(members) > max_files:
        raise SystemExit("ERROR: archive file quota exceeded")
    total = sum(member.size for member in members if member.isfile())
    if total > max_total_bytes:
        raise SystemExit("ERROR: archive total byte quota exceeded")
    seen: set[str] = set()
    for member in members:
        name = member.name
        if not name or "\\" in name:
            raise SystemExit(f"ERROR: invalid archive path: {name!r}")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"ERROR: archive path escape rejected: {name!r}")
        key = str(path)
        if key in seen:
            raise SystemExit(f"ERROR: duplicate archive member: {path}")
        seen.add(key)
        if member.issym() or member.islnk():
            raise SystemExit(f"ERROR: archive link rejected: {name}")
        if not (member.isfile() or member.isdir()):
            raise SystemExit(f"ERROR: special archive member rejected: {name}")
    destination.mkdir(mode=0o700)
    for member in members:
        output_path = destination / str(PurePosixPath(member.name))
        if member.isdir():
            output_path.mkdir(parents=True, exist_ok=True)
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            raise SystemExit(f"ERROR: unreadable archive member: {member.name}")
        with source, output_path.open("xb") as output:
            shutil.copyfileobj(source, output)
        output_path.chmod(member.mode & 0o777)
PY
}

extract_release "$ARCHIVE" "$WORK/extracted"
PACKAGE="$WORK/extracted/machineroom-${VERSION}"
[[ -d "$PACKAGE" && ! -L "$PACKAGE" ]]
[[ -d "$PACKAGE/tools" ]]
PACKAGE_TOOLS="$PACKAGE/tools"

if [[ "$DRY_RUN" == true ]]; then
  set +e
  RESULT=$(PYTHONPATH="$PACKAGE_TOOLS" \
    MR_INSTALL_PACKAGE="$PACKAGE" MR_INSTALL_VERSION="$VERSION" \
    MR_ASSET_SHA256="$ASSET_SHA256" MR_ACTION="$CMD" python3 - <<'PY'
import hashlib
import json
import os
import shutil
from pathlib import Path

from harness.runtime import PAYLOAD_CURSOR, PAYLOAD_DIRS, PAYLOAD_FILES, InstallFailure

package = Path(os.environ["MR_INSTALL_PACKAGE"])
version = os.environ["MR_INSTALL_VERSION"]
asset_sha256 = os.environ["MR_ASSET_SHA256"]
action = os.environ.get("MR_ACTION", "install")


def _digest_tree(root: Path) -> str:
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


try:
    for relative in (*PAYLOAD_DIRS, *PAYLOAD_CURSOR):
        if not (package / relative).is_dir():
            raise InstallFailure(
                relative, "dry_run", f"payload missing directory: {relative} (release {version})"
            )
    for relative in PAYLOAD_FILES:
        if not (package / relative).is_file():
            raise InstallFailure(
                relative, "dry_run", f"payload missing file: {relative} (release {version})"
            )
    staging = package.parent / f"dry-run-digest-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    for relative in (*PAYLOAD_DIRS, *PAYLOAD_CURSOR):
        shutil.copytree(package / relative, staging / relative, symlinks=False)
    for relative in PAYLOAD_FILES:
        dest = staging / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package / relative, dest)
    digest = _digest_tree(staging)
    shutil.rmtree(staging)
except InstallFailure as exc:
    print(json.dumps({"status": "failed", "action": action, "version": version, "failures": [exc.to_dict()]}))
    raise SystemExit(1) from None
print(
    json.dumps(
        {
            "status": "simulated",
            "action": action,
            "version": version,
            "asset_sha256": asset_sha256,
            "digest": digest,
        }
    )
)
PY
)
  RC=$?
  set -e
  if [[ "$RC" -ne 0 ]]; then
    echo "$RESULT" >&2
    if [[ "$JSON_OUT" == true ]]; then
      echo "$RESULT"
    fi
    exit "$RC"
  fi
  if [[ "$JSON_OUT" == true ]]; then
    echo "$RESULT"
  else
    DIGEST=$(printf '%s\n' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["digest"])')
    echo "dry-run: would install v$VERSION digest=${DIGEST:0:12}… into $RUNTIME"
  fi
  exit 0
fi

set +e
RESULT=$(PYTHONPATH="$PACKAGE_TOOLS" JSON_OUT="$JSON_OUT" \
  MR_INSTALL_PACKAGE="$PACKAGE" MR_INSTALL_RUNTIME="$RUNTIME" MR_INSTALL_VERSION="$VERSION" \
  MR_ACTION="$CMD" MR_ASSET_SHA256="$ASSET_SHA256" \
  python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

from harness.runtime import InstallFailure, format_failure, install_verified_runtime

package = Path(os.environ["MR_INSTALL_PACKAGE"])
runtime = Path(os.environ["MR_INSTALL_RUNTIME"])
version = os.environ["MR_INSTALL_VERSION"]
json_out = os.environ.get("JSON_OUT") == "true"
action = os.environ.get("MR_ACTION", "install")
asset_sha256 = os.environ.get("MR_ASSET_SHA256", "")
try:
    manifest = install_verified_runtime(package, runtime, version)
except InstallFailure as exc:
    print(format_failure(exc.component, exc.function, exc.detail), file=sys.stderr)
    if json_out:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "action": action,
                    "runtime": str(runtime),
                    "failures": [exc.to_dict()],
                }
            )
        )
    raise SystemExit(1) from None
payload = {"status": "ok", "action": action, "runtime": str(runtime), **manifest}
if asset_sha256:
    payload["asset_sha256"] = asset_sha256
print(json.dumps(payload))
PY
)
RC=$?
set -e
if [[ "$RC" -ne 0 ]]; then
  if [[ "$JSON_OUT" == true && -n "$RESULT" ]]; then
    echo "$RESULT"
  fi
  exit "$RC"
fi
if [[ "$JSON_OUT" == true ]]; then
  echo "$RESULT"
else
  echo "Installed runtime $VERSION at $RUNTIME"
fi
