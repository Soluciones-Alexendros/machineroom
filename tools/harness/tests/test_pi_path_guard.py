"""Pi path-guard (TypeScript): the fail-closed decision must be provable.

``path-guard.ts`` protects writes outside ``~/Work``: hard lists block, config
files confirm, and any unlisted path is fail-closed. The decision lives inside
the extension, so this test drives the module through Node's type stripping and
asserts the full matrix. It skips (``not_run``) when Node cannot run it.

RED target: ``decidePath`` does not exist yet, so the first run must fail.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

PATH_GUARD = ROOT / "extensions" / "machineroom" / "path-guard.ts"


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not on PATH: path-guard decision is not_run here")
    probe = subprocess.run(
        [node, "--experimental-strip-types", "-e", "process.exit(0)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip(
            "node without --experimental-strip-types: path-guard decision is not_run here"
        )
    return node


def _decisions(tmp_path: Path, home: Path, has_ui: bool) -> list[str]:
    node = _node()
    work = home / "Work"
    matrix = [
        str(work / "notes.txt"),
        "/tmp/machineroom-x/foo",
        str(home),
        str(home / ".ssh" / "id_rsa"),
        str(home / ".machineroom" / "runtime"),
        str(home / ".pi" / "agent" / "auth.json"),
        str(home / "proj" / ".env"),
        str(home / ".pi" / "agent" / "settings.json"),
        str(home / "random" / "file.txt"),
    ]
    script = tmp_path / "matrix.mjs"
    script.write_text(
        "import { decidePath } from "
        f'"{PATH_GUARD.as_posix()}";\n'
        f"const home = {json.dumps(str(home))};\n"
        f"const work = {json.dumps(str(work))};\n"
        f"const hasUI = {'true' if has_ui else 'false'};\n"
        f"const paths = {json.dumps(matrix)};\n"
        "console.log(JSON.stringify(paths.map((p) => decidePath(p, { home, work, hasUI }).verdict)));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=True,
    )
    verdicts: list[str] = json.loads(proc.stdout.strip().splitlines()[-1])
    return verdicts


def test_path_guard_matrix_is_fail_closed_without_ui(tmp_path: Path) -> None:
    home = tmp_path / "home"
    verdicts = _decisions(tmp_path, home, has_ui=False)
    assert verdicts == [
        "allow",  # inside ~/Work
        "allow",  # explicit /tmp allowlist prefix
        "block",  # home root
        "block",  # hard dir
        "block",  # machineroom runtime
        "block",  # hard file
        "block",  # hard segment (.env)
        "block",  # config file without UI -> fail-closed
        "block",  # unlisted path without UI -> fail-closed
    ]


def test_path_guard_confirm_files_with_ui(tmp_path: Path) -> None:
    home = tmp_path / "home"
    verdicts = _decisions(tmp_path, home, has_ui=True)
    assert verdicts[7] == "confirm"  # settings.json
    assert verdicts[8] == "confirm"  # unlisted path, UI available


def test_path_guard_missing_export_is_not_silently_accepted() -> None:
    # Guard against the extension losing its pure decision entry point.
    text = PATH_GUARD.read_text(encoding="utf-8")
    assert "export function decidePath" in text


def _verdicts(
    tmp_path: Path, home: Path, paths: list[str], *, cwd: str, has_ui: bool = False
) -> list[str]:
    node = _node()
    work = home / "Work"
    script = tmp_path / "cwd-matrix.mjs"
    script.write_text(
        "import { decidePath } from "
        f'"{PATH_GUARD.as_posix()}";\n'
        f"const home = {json.dumps(str(home))};\n"
        f"const work = {json.dumps(str(work))};\n"
        f"const cwd = {json.dumps(cwd)};\n"
        f"const hasUI = {'true' if has_ui else 'false'};\n"
        f"const paths = {json.dumps(paths)};\n"
        "console.log(JSON.stringify(paths.map((p) => decidePath(p, { home, work, cwd, hasUI }).verdict)));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [node, "--experimental-strip-types", str(script)],
        capture_output=True,
        text=True,
        check=True,
    )
    verdicts: list[str] = json.loads(proc.stdout.strip().splitlines()[-1])
    return verdicts


def test_launch_directory_is_open_and_credentials_stay_blocked(tmp_path: Path) -> None:
    """A session launched in a directory may write that tree, including children."""
    home = tmp_path / "home"
    launch = home / "Projects" / "app"
    paths = [
        str(launch / "src" / "main.ts"),
        str(launch / "node_modules" / "pkg" / "index.js"),
        str(launch / ".env"),
        str(home / "Work" / "notes.txt"),
        str(home / ".machineroom" / "extensions" / "machineroom" / "path-guard.ts"),
        str(home / ".ssh" / "id_rsa"),
        str(home / ".pi" / "agent" / "auth.json"),
        str(home / "other" / "file.txt"),
    ]
    verdicts = _verdicts(tmp_path, home, paths, cwd=str(launch))
    assert verdicts == [
        "allow",  # file inside the launch directory
        "allow",  # subdirectory, even a normally protected segment
        "allow",  # project .env inside the launch directory
        "allow",  # ~/Work stays open from any launch directory
        "block",  # runtime is outside the launch directory
        "block",  # credential store, even if someone launches in $HOME
        "block",  # credential file
        "block",  # sibling of the launch directory, no UI
    ]


def test_home_launch_opens_its_tree_except_credentials(tmp_path: Path) -> None:
    home = tmp_path / "home"
    paths = [
        str(home / ".machineroom" / "extensions" / "machineroom" / "path-guard.ts"),
        str(home / ".config" / "hypr" / "bindings.lua"),
        str(home / ".pi" / "agent" / "extensions" / "path-guard.ts"),
        str(home),
        str(home / ".ssh" / "id_rsa"),
        str(home / ".pi" / "agent" / "mcp-auth.json"),
    ]
    verdicts = _verdicts(tmp_path, home, paths, cwd=str(home))
    assert verdicts == [
        "allow",
        "allow",
        "allow",
        "block",  # the home directory inode itself
        "block",
        "block",
    ]


def test_symlink_into_credentials_stays_blocked(tmp_path: Path) -> None:
    home = tmp_path / "home"
    work = home / "Work"
    secret = home / ".ssh"
    secret.mkdir(parents=True)
    (secret / "id_rsa").write_text("secret", encoding="utf-8")
    work.mkdir()
    link = work / "id_rsa"
    link.symlink_to(secret / "id_rsa")
    verdicts = _verdicts(tmp_path, home, [str(link)], cwd=str(work))
    assert verdicts == ["block"]
