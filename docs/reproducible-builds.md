# Reproducible source archive

### Propósito de este documento

- **Objetivos:** Cómo se construye el tarball de release y cómo verificarlo (checksum, attestation, firma cosign).
- **Estructura:** Comando canónico → límites → verificación.
- **Contenido a integrar según contexto:** El job `provenance` de [`.github/workflows/release.yml`](../.github/workflows/release.yml) es la fuente de verdad del comando. Política de vulnerabilidades: [`SECURITY.md`](../SECURITY.md).

## Canonical archive command

The release provenance job builds the public source archive with `git archive` against the release commit (`HEAD` after checkout of that tag/commit):

```bash
git archive --format=tar.gz --prefix="machineroom-${VERSION}/" -o "machineroom-${VERSION}.tar.gz" HEAD
```

`${VERSION}` is the release version without the leading `v` (for example `9.1.0`). The same job writes `SHA256SUMS` with `sha256sum` over that archive, signs both the archive and `SHA256SUMS` with cosign keyless `sign-blob` into `*.sigstore.json` bundles, then attaches GitHub build provenance before upload.

## Reproducibility limit

The tarball is reproducible for the **same commit** and the **same git version** that produced the release asset.

Do **not** promise byte-identical archives across different git versions: `git archive` output can vary with the git binary. Matching checksums after rebuilding on another git version is a bonus, not a contract.

## Verification

Download the release assets for `v${VERSION}` (the same set `post-release-smoke` checks):

- `machineroom-${VERSION}.tar.gz`
- `SHA256SUMS`
- `machineroom-${VERSION}.tar.gz.sigstore.json`
- `SHA256SUMS.sigstore.json`
- `machineroom-${VERSION}.cdx.json` (SBOM; presence check only below). The
  provenance job publishes this asset only after
  [`tools/validate/license_gate.py`](../tools/validate/license_gate.py) accepts
  declared SPDX ids against
  [`tools/validate/license_allowlist.txt`](../tools/validate/license_allowlist.txt);
  policy: [`docs/licensing.md`](licensing.md).

Then:

```bash
REPO=Soluciones-Alexendros/machineroom
ARCHIVE="machineroom-${VERSION}.tar.gz"

# 1) Integrity of the published bytes
sha256sum -c SHA256SUMS

# 2) Build provenance (GitHub Attestations / SLSA)
gh attestation verify "${ARCHIVE}" --repo "${REPO}"

# 3) Cosign keyless blob signatures (Sigstore JSON bundles from provenance)
cosign verify-blob \
  --bundle "${ARCHIVE}.sigstore.json" \
  --certificate-identity-regexp "https://github.com/${REPO}/\\.github/workflows/release\\.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "${ARCHIVE}"

cosign verify-blob \
  --bundle "SHA256SUMS.sigstore.json" \
  --certificate-identity-regexp "https://github.com/${REPO}/\\.github/workflows/release\\.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  SHA256SUMS
```

These flags match `.github/workflows/release.yml` job `post-release-smoke` (`Download and verify release assets`). Cosign keyless signing already runs in the `provenance` job (`sign-blob --bundle … .sigstore.json`).

If a binary (`gh`, `cosign`) is missing locally, treat that check as `not_run` with that reason — never as PASS.

## Related

- Vulnerability disclosure: [`SECURITY.md`](../SECURITY.md)
- ASVS applicability (no L2 claim): [`docs/security/asvs-applicability.md`](security/asvs-applicability.md)
