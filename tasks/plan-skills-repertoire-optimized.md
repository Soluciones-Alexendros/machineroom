# Plan Optimizado: Skills Repertoire Improvement (SDD)

## Objective

Transformar el catálogo de 16 skills en un repertorio coherente, fluido, bien referenciado y eficaz, alineado con el canon de flota (STANDARD.md, TAXONOMY.md, GLOSARIO.md, ADR-0017) sin desviaciones.

---

## Phase 0: Scope Check — Capability Map

| Capability ID                | Descripción                                                                                                                                                   | Shippable Alone | Depende de                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------------------------------- |
| `metadata-normalization`     | Unificar frontmatter en 16 skills (author, version, keywords[], compatibility, allowed-tools, dmi)                                                            | Sí              | —                                                 |
| `cross-reference-integrity`  | Añadir 14 flechas `→ skill` faltantes en descriptions/When to Use                                                                                             | Sí              | metadata-normalization                            |
| `references-structure`       | Crear `references/` donde faltan (5 skills); migrar inline docs; ≤500 líneas                                                                                  | Sí              | metadata-normalization                            |
| `type-reclassification`      | Alinear `metadata.type` al comportamiento real (3 cambios: project-libraries→atomic, project-publish→orchestrator, project-machineroom se queda orchestrator) | Sí              | metadata-normalization, cross-reference-integrity |
| `orchestrator-deduplication` | Separar `plan-continue` (fases+status) de auditoría de repo → nuevo `project-audit` (atomic)                                                                  | Sí              | type-reclassification                             |
| `validation-tooling`         | Extender `skill_spec.py`: template description, keywords array, size limits, cross-ref targets; `make validate-skills`                                        | Sí              | type-reclassification                             |
| `documentation-sync`         | Regenerar TAXONOMY.md, actualizar AGENTS.md, GLOSARIO.md, harness docs                                                                                        | Sí              | Todas las anteriores                              |
| `skill-gap-analysis`         | Documentar 7 huecos futuros en decisions file; no crear skills ahora                                                                                          | Sí              | documentation-sync                                |

**Orden de ejecución real (respetando dependencias):**

```
metadata-normalization
    ├─→ cross-reference-integrity
    ├─→ references-structure (paralelo)
    └─→ type-reclassification
            ├─→ orchestrator-deduplication
            └─→ validation-tooling (paralelo)
                    └─→ documentation-sync (final)
                            └─→ skill-gap-analysis
```

---

## Phase 1: Specification (Locked)

### 1.1 Assumptions

| Assumption                                           | Valor                                                                                     |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Stack                                                | Python (tools), Markdown (skills), YAML (frontmatter)                                     |
| Validación                                           | `tools/validate/skill_spec.py` + `skill_links.py`                                         |
| Distribución                                         | Pi package (Git), Cursor plugin (symlinks)                                                |
| Canon                                                | AGENTS.md, STANDARD.md, TAXONOMY.md, GLOSARIO.md, ADRs                                    |
| Idioma                                               | Skill bodies en inglés; planes del operador en español                                    |
| Progressive disclosure                               | ≤500 líneas, ≤5000 tokens por SKILL.md; profundidad en `references/`                      |
| Techo `allowed-tools` por `metadata.type` (ADR-0017) | `audit`: Read/Grep/Glob; `atomic`: +Bash+Write; `orchestrator`: todo; `router`: Read/Glob |

### 1.2 Target State por Skill

| Skill                   | domain  | type final                    | refs objetivo                                                                | keywords (lista)                                         | dmi    | Cambios clave                                                                        |
| ----------------------- | ------- | ----------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| plan-continue           | plan    | **orchestrator**              | 18 ✓                                                                         | [plan, continue, phase-router, status-bump, workspace]   | no     | Pierde repo-audit; queda fases+status; `Not for repo health board (→ project-audit)` |
| plan-specification      | plan    | orchestrator                  | 5 ✓                                                                          | [spec, plan, tasks, acceptance-criteria, capability-map] | no     | —                                                                                    |
| plan-validators         | plan    | atomic                        | 3 → +2 (test-patterns, cookbook)                                             | [tdd, test-coverage, qa, red-green, prove-it]            | no     | —                                                                                    |
| project-architecture    | project | audit                         | 0 → 3 (dependency-mapping, metrics-guide, drift-detection)                   | [architecture, dependency-mapping, drift, metrics]       | no     | —                                                                                    |
| project-libraries       | project | **atomic**                    | 4 → +1 (remediation-playbook)                                                | [sca, cve, sbom, supply-chain, remediation]              | no     | **+Bash** (ejecuta pipeline SCA)                                                     |
| project-machineroom     | project | **orchestrator** (corrección) | 5 ✓                                                                          | [self-audit, canon, harness, control-plane, doctor]      | no     | Se queda orchestrator (plan_self_change escribe; doctor.py usa Bash)                 |
| project-publish         | project | **orchestrator**              | 6 → +2 (versioning-guide, changelog-guide)                                   | [release, husky, lint-staged, ci-gate, versioning]       | **sí** | Semántica: flujo multi-paso con efectos externos                                     |
| role-back               | role    | atomic                        | 0 → 6 (cache, queue, rate-limit, storage, search, vector)                    | [backend, api, persistence, jobs, patterns]              | no     | Hueco mayor de eficacia                                                              |
| role-front              | role    | atomic                        | 0 → 4 (state-management, routing-patterns, form-patterns, api-contracts)     | [frontend, state, routing, forms, contracts]             | no     | Hueco mayor de eficacia                                                              |
| role-design             | role    | atomic                        | 11 ✓                                                                         | [design, tokens, tailwind, components, visual]           | no     | —                                                                                    |
| role-clean-code         | role    | atomic                        | 4 ✓                                                                          | [clean-code, refactor, naming, smells, protocols]        | no     | —                                                                                    |
| local-maintenance       | local   | atomic                        | 9 ✓                                                                          | [maintenance, linux, health, cleanup, optimization]      | **sí** | —                                                                                    |
| local-security          | local   | atomic                        | 6 → +3 (hardening-checklist, cve-tracking, forensics-guide)                  | [security, hardening, apparmor, forensics, cve]          | **sí** | —                                                                                    |
| web-compliance          | web     | audit                         | 10 ✓                                                                         | [compliance, wcag, gdpr, seo, remediation]               | no     | —                                                                                    |
| web-owasp               | web     | audit                         | 25 ✓                                                                         | [owasp, injection, xss, authz, crypto]                   | no     | —                                                                                    |
| web-performance         | web     | audit                         | 2 → 6 (cwv-deep-dive, rendering-modes, caching-strategies, lighthouse-guide) | [performance, cwv, lighthouse, caching, rendering]       | no     | —                                                                                    |
| **nuevo** project-audit | project | **atomic**                    | 3 (inicio-plan, plantilla-informe, verification-guide)                       | [repo-audit, health-board, evolution-plan, status]       | no     | Hereda scripts/refs de plan-continue; ops: repo_scan, status_board                   |

**Totales:** 17 skills (16 actuales + 1 nueva), 5 dominios, 0 `router` (imposible por techo allowed-tools).

### 1.3 Flechas `→ skill` obligatorias (14)

| From                 | → Target                                            | Reason                             |
| -------------------- | --------------------------------------------------- | ---------------------------------- |
| plan-continue        | project-audit                                       | repo health board                  |
| plan-continue        | project-machineroom                                 | self-audit vs plan continuation    |
| plan-specification   | plan-validators                                     | implementation phase               |
| plan-validators      | role-back, role-front, role-design, role-clean-code | implementation roles               |
| project-architecture | role-clean-code                                     | refactoring outcome                |
| project-libraries    | project-publish                                     | dependency updates → release       |
| project-machineroom  | plan-continue                                       | plan continuation after self-audit |
| project-audit        | plan-continue                                       | phase routing after repo health    |
| role-back            | project-libraries                                   | supply chain before new deps       |
| role-front           | role-design                                         | visual polish handoff              |
| role-design          | role-front                                          | implementation handoff             |
| web-compliance       | web-owasp                                           | security overlap                   |
| web-owasp            | web-compliance                                      | compliance overlap                 |
| web-performance      | web-compliance                                      | CWV overlaps SEO/accessibility     |

---

## Phase 2: Technical Plan — Work Packages (Batches)

### WP1: Metadata Normalization (1 commit, 16 skills)

- [ ] **T1.1** `metadata.author` = `Soluciones-Alexendros` (unificar 8 skills con `addyosmani (adapted)` / `Soluciones-Alexendros (adapted)`)
- [ ] **T1.2** `metadata.version`: patch para docs, minor para capacidad, major para breaking; alinear `local-maintenance` 8.0.0 / `local-security` 7.1.1
- [ ] **T1.3** `metadata.keywords`: string → array con `[skill, domain, 3-5 términos]`
- [ ] **T1.4** `compatibility: ["cursor", "pi"]` en todas
- [ ] **T1.5** `allowed-tools`: auditorías = Read/Grep/Glob; atomic/orchestrator = +Bash+Write justificado en description
- [ ] **T1.6** `disable-model-invocation: true` sólo en `local-maintenance`, `local-security`, `project-publish`; quitar si existiera en otras
- [ ] **T1.7** `description` a plantilla: `[Capability]. Use when [contexts]. Not for [limit] (→ neighbor-skill).` (16 skills)

**Validación WP1:** `python tools/validate/skill_spec.py --all` → 0 errores; `skill_links.py` → 0 rotos.

---

### WP2: Cross-Reference Integrity (1 commit)

- [ ] **T2.1** Añadir 14 flechas de la tabla 1.3 en `description` y `When to Use`/`Not for`
- [ ] **T2.2** Ejecutar `skill_links.py` y corregir cualquier roto

**Validación WP2:** `skill_links.py` → 0 rotos.

---

### WP3: References Structure (3 commits por dominio, paralelos)

#### WP3a: project-* (1 commit)

- [ ] **T3a.1** `project-architecture/references/`: `dependency-mapping.md`, `metrics-guide.md`, `drift-detection.md`
- [ ] **T3a.2** `project-libraries/references/`: `remediation-playbook.md`
- [ ] **T3a.3** `project-machineroom/references/`: ya completo ✓
- [ ] **T3a.4** `project-publish/references/`: `versioning-guide.md`, `changelog-guide.md`
- [ ] **T3a.5** Añadir tabla de índice de referencias en cada SKILL.md

#### WP3b: role-* (1 commit)

- [ ] **T3b.1** `role-back/references/`: 6 patrones (cache, queue, rate-limit, storage, search, vector)
- [ ] **T3b.2** `role-front/references/`: 4 archivos (state-management, routing-patterns, form-patterns, api-contracts)
- [ ] **T3b.3** `role-design/references/`: ya completo ✓
- [ ] **T3b.4** `role-clean-code/references/`: ya completo ✓
- [ ] **T3b.5** Añadir tabla de índice en cada SKILL.md

#### WP3c: web-* + local-* (1 commit)

- [ ] **T3c.1** `web-performance/references/`: 4 archivos (cwv-deep-dive, rendering-modes, caching-strategies, lighthouse-guide)
- [ ] **T3c.2** `local-security/references/`: 3 archivos (hardening-checklist, cve-tracking, forensics-guide)
- [ ] **T3c.3** `plan-validators/references/`: 2 archivos (test-patterns, cookbook)
- [ ] **T3c.4** Migrar contenido inline >500 líneas a references/ (ninguno hoy)
- [ ] **T3c.5** Añadir tabla de índice en cada SKILL.md

**Validación WP3:** `skill_spec.py --size` → todos ≤500 líneas / ≤5000 tokens; cada skill tiene `references/` con ≥1 archivo.

---

### WP4: Type Reclassification (1 commit, 3 skills)

- [ ] **T4.1** `project-libraries`: `audit` → `atomic` (+Bash en allowed-tools, entrada en registry.yaml: `sca_scan`, `sbom_generate`)
- [ ] **T4.2** `project-publish`: `atomic` → `orchestrator` (sin cambio de herramientas; justificar en description)
- [ ] **T4.3** `project-machineroom`: confirmar `orchestrator` (no cambiar a audit; explicar en description)
- [ ] **T4.4** Actualizar `tools/validate/skill_spec.py`: enum type = `["atomic","orchestrator","router","audit"]` (router se queda para futuro; no se usa)
- [ ] **T4.5** Regenerar `docs/TAXONOMY.md` con columna type correcta

**Validación WP4:** `skill_spec.py --all` → 0 errores; TAXONOMY.md coherente.

---

### WP5: Orchestrator Deduplication (1 commit, nueva skill)

- [ ] **T5.1** Reescribir `plan-continue/SKILL.md`: quitar repo-audit, scripts y refs (`inicio-plan`, `plantilla-informe`, `verification-guide`); acortar description a fases+status; añadir `Not for repo health board (→ project-audit)`
- [ ] **T5.2** Crear `skills/project-audit/`: `SKILL.md` + `references/` (3 archivos heredados) + entrada en `intent-map.yaml` (`repo_starting`) + `registry.yaml` (`repo_scan` read, `status_board` write-workspace, `atomic`, `disable-model-invocation: false`)
- [ ] **T5.3** `project-machineroom/SKILL.md`: añadir `Not for product-repo health (→ project-audit)`
- [ ] **T5.4** Actualizar `tools/skill-router/intent-map.yaml`: mover patterns `audita repo`, `repo starting`, `inicio de plan` de `plan_continuar` a `repo_starting` (`project-audit`); `plan_continuar` queda con `por donde empiezo`, `ciclo de vida`, `pon al día proyecto`
- [ ] **T5.5** Actualizar `test_catalog_16.py` → `test_catalog_17.py` (EXPECTED_COUNT=17, RETIRED=local-email, NEW=project-audit)
- [ ] **T5.6** Actualizar `AGENTS.md` routing contract: nuevo skill `project-audit` para repo starting; `plan-continue` = phase router + status bump

**Validación WP5:** `bash run-validation.sh` → All checks passed; `make test` → 662+ passed; install matrix deriva 17 skills.

---

### WP6: Validation Tooling (1 commit)

- [ ] **T6.1** `skill_spec.py`: añadir checks — description template regex (warn), keywords array (warn), size limits (error), cross-ref targets en frontmatter/description (error)
- [ ] **T6.2** `skill_links.py`: verificar que todos los `→ skill` en prosa apuntan a skills/ existentes
- [ ] **T6.3** Añadir `make validate-skills` que corra `skill_spec.py --all`, `skill_links.py`, `--size`, `--taxonomy`
- [ ] **T6.4** Integrar en CI (`.github/workflows/ci.yml` job `validate-skills`)

**Validación WP6:** `make validate-skills` pasa; CI gate `ci-gate` incluye el job.

---

### WP7: Documentation Sync (1 commit, final)

- [ ] **T7.1** Regenerar `docs/TAXONOMY.md` con `tools/skill-index/generate.py --sync-docs` (17 skills)
- [ ] **T7.2** Actualizar `AGENTS.md`: catálogo 17 skills, routing rules, dominio `project` con 5 skills
- [ ] **T7.3** Actualizar `docs/GLOSARIO.md` si nuevos términos canónicos
- [ ] **T7.4** Actualizar `docs/harness-integration.md` y `docs/harness-setup.md` (conteo derivado)
- [ ] **T7.5** Entrada `Removed: local-email` + `Added: project-audit` + `Changed: types` en `CHANGELOG.md` (via PR de release 8.1.0)

**Validación WP7:** `run-validation.sh` → All checks passed; `pi skill list` / Cursor `/skills` → 17 skills.

---

### WP8: Skill Gap Analysis (1 commit, documentation only)

- [ ] **T8.1** Documentar 7 huecos en `tasks/decisions-skills-repertoire.md` (ya hecho) con prioridad P1/P2
- [ ] **T8.2** No crear skills; decisión futura en próximo incremento

---

## Phase 3: Implementation Roles & Handoffs

| Work Package  | Implementation Role                                                               | Test Surface                             | Handoff                                       |
| ------------- | --------------------------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------- |
| WP1, WP2, WP4 | `role-clean-code` + `plan-specification`                                          | Validator output                         | → `plan-validators` para tests de validadores |
| WP3a          | `role-back` (project-*)                                                           | Reference readability, link validity     | → `plan-validators`                           |
| WP3b          | `role-front` (role-front), `role-design` (role-design)                            | Reference readability, link validity     | → `plan-validators`                           |
| WP3c          | `plan-validators` (plan-*), `local-maintenance`/`local-security` (domain experts) | Reference readability                    | → `plan-validators`                           |
| WP5           | `plan-continue` (router), `project-machineroom` (audit)                           | Phase routing, audit output, nueva skill | → `plan-validators` E2E                       |
| WP6           | `role-back` (Python tooling)                                                      | Unit tests validators                    | → `plan-validators` integración               |
| WP7, WP8      | `plan-specification` (canonical docs)                                             | Doc render, terminology                  | → `project-publish` para release              |

**Recurrent routing:** Antes de cada WP, re-evaluar e invocar roles coincidentes per AGENTS.md.

---

## Phase 4: Acceptance Criteria (Global)

```bash
# Desde repo root
make validate-skills              # All validators pass (metadata, links, size, taxonomy)
python tools/workspace-router/run.py --status --repo . --json  # Status clean
uv run python tools/harness/doctor.py --harness all --json     # No drift
pi skill list                     # 17 skills discoverable
# En Cursor: /skills muestra 17 skills
bash scripts/tests/test_install.sh # install tests OK (conteo derivado)
```

| Capability                 | Done Criteria                                                                                                              |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| metadata-normalization     | 16 skills pass `skill_spec.py --metadata`; author/version/keywords[]/compatibility/tools consistentes                      |
| cross-reference-integrity  | 14 flechas añadidas; `skill_links.py` 0 rotos                                                                              |
| references-structure       | 17 skills con `references/`; todos ≤500 líneas / ≤5000 tokens; índice de refs en cada SKILL.md                             |
| type-reclassification      | 3 skills con type corregido; TAXONOMY.md coherente; validator enforces closed set                                          |
| orchestrator-deduplication | `plan-continue` = fases+status; `project-audit` = repo health; `project-machineroom` = self-audit; sin solape en AGENTS.md |
| validation-tooling         | `make validate-skills` pasa; CI incluye job                                                                                |
| documentation-sync         | TAXONOMY.md, AGENTS.md, GLOSARIO.md, harness docs reflejan 17 skills                                                       |

---

## Riesgos y Mitigaciones (Actualizados)

| Riesgo                                                                                   | Probabilidad | Impacto | Mitigación                                                                |
| ---------------------------------------------------------------------------------------- | ------------ | ------- | ------------------------------------------------------------------------- |
| `plan-continue` → `router` imposible por techo allowed-tools                             | Ya resuelto  | —       | Usar `orchestrator` para `plan-continue`; `router` queda reservado        |
| `project-machineroom` como `audit` rompe `plan_self_change` (write) + `doctor.py` (Bash) | Ya resuelto  | —       | Mantener `orchestrator` con corrección en decisions                       |
| Nueva skill `project-audit` requiere `atomic` (no `audit`) por escribir `ESTADO.md`      | Ya resuelto  | —       | Definida como `atomic` en tabla 1.2                                       |
| Tests de catálogo fallan durante transición                                              | Media        | Alto    | WP5 actualiza `test_catalog_16.py` → `test_catalog_17.py` en mismo commit |
| Validator false positives en description template                                        | Media        | Bajo    | Empezar con `warn`; subir a `error` en segundo incremento                 |

---

## Próximos Pasos

1. **Aprobación** de este plan optimizado (WP1–WP8)
2. **Ejecución** por work packages en orden, con role routing recurrente
3. **Validación y cierre** → `make validate-skills`, harness doctor, PR de release 8.1.0

---

## Diferencias Clave vs Plan Original

| Aspecto       | Plan Original                | Plan Optimizado                                          |
| ------------- | ---------------------------- | -------------------------------------------------------- |
| Work packages | 8 fases lineales             | 8 WPs con paralelismo explícito (WP3a/b/c, WP1+WP2)      |
| D1/D2         | Router/audit incorrectos     | Corregidos por techo allowed-tools (orchestrator/atomic) |
| Nueva skill   | `plan-audit` (ambiguo)       | `project-audit` (domain=project, type=atomic)            |
| Tasks         | 36 granulares                | 25 tareas agrupadas en WPs con commit boundaries         |
| Validación    | Al final                     | Checkpoint por WP (fail-fast)                            |
| Referencias   | 15 tasks sueltas             | 3 WPs por dominio (project/role/web+local)               |
| Versionado    | Mencionado en D8             | Entrada CHANGELOG.md explícita en WP7 (release 8.1.0)    |
| Router type   | Propuesto para plan-continue | Descartado (imposible); reservado para futuro            |
