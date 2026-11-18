# ASVS applicability (machineroom)

### Propósito de este documento

- **Objetivos:** Declarar qué capítulos OWASP ASVS aplican a este canon CLI/harness, sin fingir certificación.
- **Estructura:** Alcance → `not_applicable` → controles presentes o en aterrizaje → referencias.
- **Contenido a integrar según contexto:** Canal de reporte en [`SECURITY.md`](../../SECURITY.md). Verificación de artefactos en [`docs/reproducible-builds.md`](../reproducible-builds.md).

## Statement

This repository tracks **applicability** of [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) controls to a fleet canon and agent harness (skills, validators, installers, execution registry). It does **not** claim ASVS Level 2 certification, product certification, or a scored L1/L2 audit badge.

## `not_applicable` (no HTTP surface)

**Rule:** this repository does not serve HTTP (no browser app, no session cookie surface, no public web API).

Under that rule the following ASVS chapter families are `not_applicable`:

| Area                    | Typical ASVS chapters                            | Status           | Rule                          |
| ----------------------- | ------------------------------------------------ | ---------------- | ----------------------------- |
| Session management      | Session Management                               | `not_applicable` | this repo does not serve HTTP |
| Browser / client web UI | Client-side / browser controls aimed at web apps | `not_applicable` | this repo does not serve HTTP |
| Web API                 | API / web-API verification chapters              | `not_applicable` | this repo does not serve HTTP |

DAST against a live web origin is likewise `not_applicable` by the same rule — not an open finding.

## Controls that exist or are landing

These are real tree/CI/release controls. “Landing” means specified in the integrity increment and wired when that module ships; absence of a green job is `not_run` / `blocked`, never a silent PASS.

| Control                        | Where                                                                           | Notes                                                                                                   |
| ------------------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Vulnerability disclosure       | [`SECURITY.md`](../../SECURITY.md)                                              | Private advisories + ops mailbox                                                                        |
| Least privilege (execution)    | [`tools/execution/registry.yaml`](../../tools/execution/registry.yaml)          | Operations declare `effect`, approval, and recovery; mutators go through `run_registered`               |
| Secret content scan (gitleaks) | `skills/project-status/actions/secret-scan` → `ci-gate` (`secret-content-scan`) | Fixed binary checksum; no SARIF upload of secrets                                                       |
| CodeQL                         | `ci.yml` (`sast-gate`)                                                          | Languages `python` + `actions`                                                                          |
| Semgrep                        | `ci.yml` (`sast-gate`)                                                          | Configs `p/python` + `p/bash`; ERROR fails the job                                                      |
| shellcheck                     | `ci.yml` (`sast-gate`)                                                          | Shell under `scripts/`, `skills/`, `tools/`                                                             |
| Cosign signing                 | `release.yml` job `provenance`                                                  | Keyless `sign-blob` / `verify-blob` of archive and `SHA256SUMS` via `*.sigstore.json` bundles           |
| SBOM                           | `release.yml` job `provenance`                                                  | CycloneDX from the `git archive` tree (Syft)                                                            |
| Checksums + attestation        | `release.yml` jobs `provenance` + `post-release-smoke`                          | `SHA256SUMS` + `gh attestation verify` — see [`docs/reproducible-builds.md`](../reproducible-builds.md) |

## Related

- [`SECURITY.md`](../../SECURITY.md)
- [`docs/reproducible-builds.md`](../reproducible-builds.md)
- Living plan: [`tasks/plan-security-integrity.md`](../../tasks/plan-security-integrity.md)
