# Plan canónico: integridad y seguridad

Plan vivo del incremento de integridad/seguridad del canon. Resume los módulos de la spec aprobada (`plan-specification` Fase 1). **No** hay tracker paralelo (`SPEC-*.md`, `tasks/todo.md` nuevo). No se toca `tasks/plan-9.2.0-control-plane-cohesion.md`.

Rama de trabajo: `plan/security-integrity` (desde `origin/main`). Implementación autorizada; cierre de PR/ruleset/`mutation-pilot` con evidencia de esta sesión.

No marcar **PASS** sin evidencia de esta sesión (comando del repo o job CI verde). Skip, binario ausente o `not_run` no son PASS.

## Módulos (10)

Orden de construcción: `secret-content-scan` → `sast-gate` → `distro-smoke` → `release-sign` → `release-sbom` → `reproducible-builds` → `asvs-statement` → `governance-repo` → `perf-budget` → `mutation-pilot`.

| id                    | Ownership                                      | Estado local (esta sesión)                                      |
| --------------------- | ---------------------------------------------- | --------------------------------------------------------------- |
| `secret-content-scan` | `ci.yml` + action gitleaks                     | Árbol: job `secret-scan` en `ci-gate` needs                     |
| `sast-gate`           | `ci.yml`                                       | Árbol: `codeql` / `semgrep` / `shellcheck -S warning` en needs  |
| `distro-smoke`        | `ci.yml`                                       | Árbol: matriz ubuntu/debian/arch                                |
| `release-sign`        | `release.yml` + `release_coherence.py`         | Tests `test_release_assets` + `release_coherence` OK            |
| `release-sbom`        | `release.yml`                                  | Mismo gate + asset `*.cdx.json`                                 |
| `reproducible-builds` | `docs/reproducible-builds.md`                  | Árbol + enlace `SECURITY.md` (alineado a `*.sigstore.json`)     |
| `asvs-statement`      | `docs/security/asvs-applicability.md`          | Árbol; sin claim L2                                             |
| `governance-repo`     | `CODEOWNERS` + `CONTRIBUTING.md`               | Árbol; ruleset GitHub = acto operador                           |
| `perf-budget`         | `tools/skill-router/tests/test_perf_budget.py` | pytest PASS (techo 5.0s)                                        |
| `mutation-pilot`      | `security.yml`                                 | Árbol; runtime **`not_run`** hasta `workflow_dispatch`/schedule |

## Evidencia local (sesión)

```text
shellcheck -S warning (scripts/ skills/ tools/) → rc=0
pytest test_release_assets + test_perf_budget + test_ci_gate → 20 passed
release_coherence.py → RELEASE: OK
hygiene.py → HYGIENE: OK
skill_spec.py → SPEC: OK
bump.py --check --auto --base origin/main → CHECK: todo versionado
cut_tag.py --check-repo → CHECK-REPO: OK
```

CI verde del PR y `mutation-pilot` ejecutado son evidencia aparte (no se inventan aquí).

## Límites

- No inventar ruleset JSON; documentar clics del operador.
- No promover skip / dependencia ausente a PASS.
- DAST, Scorecard badge, SARIF de gitleaks, clave privada de firma: fuera de alcance.

## Referencias

- [`SECURITY.md`](../SECURITY.md)
- [`docs/reproducible-builds.md`](../docs/reproducible-builds.md)
- [`docs/security/asvs-applicability.md`](../docs/security/asvs-applicability.md)
- [`.github/CODEOWNERS`](../.github/CODEOWNERS)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
