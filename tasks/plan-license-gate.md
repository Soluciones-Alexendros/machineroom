# Implementation Plan: license-gate

Plan canónico del incremento `license-gate` (spec + correcciones ejecutables). **No** hay tracker paralelo (`SPEC-*.md`, `tasks/todo.md`). No se reescribe [`tasks/plan-security-integrity.md`](plan-security-integrity.md).

Implementación autorizada por el operador (plan ejecutable confirmado). Sin push, PR ni ruleset hasta una orden aparte.

No marcar **PASS** sin evidencia de la sesión (comando del repo o job CI verde). Skip, binario ausente o `not_run` no son PASS.

## Overview

El proyecto es MIT y publica un SBOM CycloneDX (`machineroom-${VERSION}.cdx.json`) generado por Syft sobre el `git archive` de release. Este incremento añade `tools/validate/license_gate.py` (stdlib) contra `tools/validate/license_allowlist.txt`, un job `license-gate` en `ci-gate`, y el mismo checker en `release.yml` entre Syft y `gh release upload`. Bump de versión a **9.2.1** al tocar workflows.

## Architecture Decisions (corrected)

- **Artefacto de verdad = CycloneDX de Syft**, no `pip-licenses`.
- **Syft pin único** v1.57.2 / SHA-256 `ad92bd3ec1b94a3df01d4d0aec199afa9c42b72e86da436ff5f837914d32706b` en `ci.yml` y `release.yml`; pytest falla si divergen.
- **Solo licencias declaradas.** Vacío, `NONE` y `NOASSERTION` no son error. Un SPDX declarado fuera de la allowlist, o en la denylist, sí lo es. Cualquier `type` con licencia declarada entra.
- **Denylist en código:** `GPL` / `AGPL` / `SSPL` / `CPAL` (variantes `-only`, `-or-later`, con versión) fallan aunque estén en la allowlist. Excepción `OR`: `MIT OR GPL-3.0-only` pasa si algún disjunto está en allowlist y no es denylist.
- **Expresiones SPDX v1:** id/name suelto → allowlist (y no denylist); solo `OR` → algún disjunto ok; `AND`/`WITH` → todos ok; `OR` mezclado con `AND`/`WITH` → fail.
- **Contrato release atómico:** docs solos; `release_coherence` + tests + workflow en el mismo paso (Task 4). Paso `license` detectado por `license_gate.py` en step distinto del de Syft.
- **Orden release:** `archive → checksum → attestation → sign → sbom → license → upload`.
- **CI:** `git archive` → Syft → `license_gate.py` → `ci-gate` needs. Sin `continue-on-error`.
- **Bump 9.2.1:** `package.json`, `package-lock.json`, `tools/pyproject.toml`, `tools/uv.lock`, `README.md`. Notas en `## [Unreleased]`.

```text
git_archive → syft_cdx → license_gate.py → ci_gate
                                      ↘ gh_release_upload
```

## Task List

### Task 1: Checker + tests

- [x] `license_gate.py` + allowlist stub `MIT` + pytest matriz corregida + `syntax-check`
- Roles: `role-back`, `role-clean-code`

### Task 2: Docs (sin release_coherence)

- [x] `docs/licensing.md`, frase en `reproducible-builds.md`, bullet Unreleased
- Roles: `role-clean-code`

### Task 3: Seed allowlist

- [x] Scan Syft 1.57.2 pinneado del archive; 70 components / 0 declared licenses; allowlist = `MIT`; gate OK
- Roles: `role-linux`, `role-back`

### Task 4: Wire CI/release + bump

- [x] Job `license-gate`, step release, coherence/tests, SHA compartido, versión 9.2.1
- Roles: `role-back`, `role-linux`, `role-clean-code`

## Evidencia local (sesión)

```text
pytest test_license_gate + test_release_assets → 26 passed
release_coherence.py → RELEASE: OK
cut_tag.py --check-repo → CHECK-REPO: OK package=9.2.1 latest_tag=9.2.0
npm run syntax-check → OK
Syft 1.57.2 scan: 70 components, 0 with licenses, DENY_HITS=[]
```

## Boundaries

- **Always:** fail closed ante SPDX declarado no permitido; pin Syft idéntico; versión alineada.
- **Ask first:** meter id denylist; dependencia nueva; push/PR/ruleset.
- **Never:** `pip-licenses`; skill `project-licenses`; reescribir `plan-security-integrity.md`; Scorecard; GUI; packaging.

## References

- Plan ejecutable Cursor: `license-gate_execute`
- [`.github/workflows/release.yml`](../.github/workflows/release.yml)
- [`tools/validate/release_coherence.py`](../tools/validate/release_coherence.py)
- [`docs/reproducible-builds.md`](../docs/reproducible-builds.md)
