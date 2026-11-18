"""Release assets must be uploaded with checksum, provenance, sign and SBOM evidence."""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from validate.release_coherence import release_asset_errors  # noqa: E402


def _write_workflow(tmp_path: Path, data: object) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def test_release_workflow_uploads_attested_archive_and_checksums() -> None:
    assert release_asset_errors(ROOT) == []


def test_missing_upload_or_wrong_order_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    steps = data["jobs"]["provenance"]["steps"]
    data["jobs"]["provenance"]["steps"] = [
        step for step in steps if "gh release upload" not in str(step.get("run", ""))
    ]
    _write_workflow(tmp_path, data)
    assert any("upload" in error for error in release_asset_errors(tmp_path))


def test_missing_sign_step_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    steps = data["jobs"]["provenance"]["steps"]
    data["jobs"]["provenance"]["steps"] = [
        step for step in steps if not ("cosign" in str(step.get("run", "")) and "sign-blob" in str(step.get("run", "")))
    ]
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("sign" in error for error in errors), errors


def test_missing_sbom_step_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    steps = data["jobs"]["provenance"]["steps"]
    data["jobs"]["provenance"]["steps"] = [step for step in steps if "syft" not in str(step.get("run", ""))]
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("sbom" in error.lower() for error in errors), errors


def test_sign_after_upload_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    steps = data["jobs"]["provenance"]["steps"]
    sign_idx = next(
        i
        for i, step in enumerate(steps)
        if "cosign" in str(step.get("run", "")) and "sign-blob" in str(step.get("run", ""))
    )
    upload_idx = next(i for i, step in enumerate(steps) if "gh release upload" in str(step.get("run", "")))
    steps.insert(upload_idx + 1, steps.pop(sign_idx))
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("ordered" in error for error in errors), errors


def test_upload_without_signature_or_sbom_assets_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    for step in data["jobs"]["provenance"]["steps"]:
        run = str(step.get("run", ""))
        if "gh release upload" in run:
            step["run"] = (
                "set -euo pipefail\n"
                'gh release view "v${VERSION}" >/dev/null\n'
                'gh release upload "v${VERSION}" "${ARCHIVE}" SHA256SUMS\n'
            )
            break
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("signature" in error for error in errors), errors
    assert any("SBOM" in error or "sbom" in error or "cdx" in error for error in errors), errors


def test_smoke_without_cosign_or_sbom_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    for step in data["jobs"]["post-release-smoke"]["steps"]:
        run = str(step.get("run", ""))
        if "gh release download" in run:
            step["run"] = (
                "set -euo pipefail\n"
                "TMP=$(mktemp -d)\n"
                'gh release download "v${VERSION}" --dir "$TMP" '
                '--pattern "machineroom-${VERSION}.tar.gz" --pattern SHA256SUMS\n'
                '( cd "$TMP" && sha256sum -c SHA256SUMS )\n'
                'gh attestation verify "$TMP/machineroom-${VERSION}.tar.gz" '
                '--repo "${GITHUB_REPOSITORY}"\n'
            )
            break
    # Drop the dedicated cosign install step so verify-blob cannot appear elsewhere.
    data["jobs"]["post-release-smoke"]["steps"] = [
        step for step in data["jobs"]["post-release-smoke"]["steps"] if "cosign" not in str(step.get("run", ""))
    ]
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("verify-blob" in error for error in errors), errors
    assert any("SBOM" in error or "sbom" in error for error in errors), errors


def test_archive_and_checksum_fixture_round_trip(tmp_path: Path) -> None:
    archive = tmp_path / "machineroom-fixture.tar.gz"
    subprocess.run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            "--prefix=machineroom-fixture/",
            "-o",
            str(archive),
            "HEAD",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    checksum = subprocess.run(
        ["sha256sum", archive.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    (tmp_path / "SHA256SUMS").write_text(checksum, encoding="utf-8")
    subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=tmp_path, check=True, capture_output=True)


def test_historical_vmain_version_fallback_is_rejected(tmp_path: Path) -> None:
    """v7.1.0 failed when upload resolved VERSION from branch name (vmain)."""
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    for step in data["jobs"]["provenance"]["steps"]:
        run = str(step.get("run", ""))
        if "gh release upload" in run:
            step["run"] = run.replace(
                'gh release upload "v${VERSION}"',
                'VERSION="${VERSION:-${GITHUB_REF_NAME#v}}"\ngh release upload "v${VERSION}"',
                1,
            )
            break
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("GITHUB_REF_NAME" in error for error in errors), errors


def test_missing_post_release_smoke_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    del data["jobs"]["post-release-smoke"]
    _write_workflow(tmp_path, data)
    errors = release_asset_errors(tmp_path)
    assert any("post-release-smoke" in error for error in errors), errors


def test_canonical_order_message_mentions_sign_and_sbom(tmp_path: Path) -> None:
    """Positive contract: live workflow is clean; flipping sign/sbom surfaces the order string."""
    assert release_asset_errors(ROOT) == []
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    mutated = copy.deepcopy(data)
    steps = mutated["jobs"]["provenance"]["steps"]
    sbom_idx = next(i for i, step in enumerate(steps) if "syft" in str(step.get("run", "")))
    sign_idx = next(
        i
        for i, step in enumerate(steps)
        if "cosign" in str(step.get("run", "")) and "sign-blob" in str(step.get("run", ""))
    )
    steps[sign_idx], steps[sbom_idx] = steps[sbom_idx], steps[sign_idx]
    _write_workflow(tmp_path, mutated)
    flipped = release_asset_errors(tmp_path)
    assert any("archive → checksum → attestation → sign → sbom → upload" in error for error in flipped), flipped
