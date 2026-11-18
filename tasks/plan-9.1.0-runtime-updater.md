# Plan: runtime updater (9.1.0)

> Spec approved 2026-11-18. Canonical plan for this increment.
> Source: reports `20261118-actualizacion-ilutex-machineroom` + Cursor plan
> `runtime_updater_remediation_25d7b11c`. Branch: `plan/9.1.0-runtime-updater`
> from `origin/main` `652a8cd`.

## Objective

Cross-version `runtime-sync.sh install`, `update --latest` (including from the
runtime), doctor runtime checks, and gates that fail when the installer is broken.
Tag `v9.1.0` is out of scope until the operator authorizes publication.

## Capability map

| Module id             | Responsibility                                                 | Depends on            |
| --------------------- | -------------------------------------------------------------- | --------------------- |
| cross-version-install | Installer Python comes from the extracted release              | —                     |
| self-update           | `update --latest` + `scripts/runtime-sync.sh` in payload       | cross-version-install |
| runtime-doctor        | `runtime-version` + `runtime-payload`                          | —                     |
| install-gates         | Hermetic cross-version + bootstrap fixtures in `make validate` | cross-version-install |
| release-provenance    | `provenance` checks PAYLOAD_* on the archive                   | —                     |
| operator-docs         | README, harness-integration, Unreleased changelog              | self-update           |

## Tasks

1. cross-version-pythonpath — PYTHONPATH from extracted release
2. payload-precheck — named relative missing-file errors
3. cross-version-test — hermetic fixture + `run-validation.sh`
4. update-latest — `update --latest` / dry-run / `not_run`
5. runtime-entry — `scripts/runtime-sync.sh` in `PAYLOAD_FILES`
6. bootstrap-fixture — `git archive HEAD` + incomplete case
7. doctor-runtime — version + payload checks
8. smoke-real — real smoke + `MR_SMOKE_FIXTURE=1` for CI canon
9. provenance-payload — PAYLOAD_* check before upload
10. docs-unreleased — README, docs, CHANGELOG

## Out of scope

- Tag / release `v9.1.0`
- Branch hygiene (`plan/opencode-harness`, `feat/herdr-plugin-min`)
- Catalog / control-plane changes already on main (#89)
