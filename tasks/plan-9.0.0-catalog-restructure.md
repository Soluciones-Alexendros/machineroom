# Plan 9.0.0 — Reestructuración del catálogo de skills

> Incremento: encajar 5 propuestas de restructuración del catálogo de machineroom.
> Plan canónico de este incremento (fuente de verdad). No crear trackers paralelos.
> Spec previa: análisis entregado al operador; decisiones cerradas y revisión de mejora incorporadas.

## Objetivo

Reorganizar el catálogo de **17 skills** en **14 skills** en 5 dominios, con tres renames, tres bajas y absorción de responsabilidades, manteniendo la paridad entre `skills/`, `skill-index.json`, router, registry, plantillas, docs y tests. Versión del repo: **9.0.0** (cambio rompedor del catálogo). La reestructuración se blinda con validadores nuevos (flechas en cuerpo, conteo de skills, coherencia de roles, handoffs) y se registra en un ADR.

## Decisiones cerradas (operador)

| #   | Decisión                | Valor                                                                                                                    |
| --- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| D1  | Frontera release        | `project-status` **absorbe** release completo (empaquetar + lanzar). Implica absorber `project-publish` y darlo de baja. |
| D2  | Dominio de `role-linux` | `role` (prefijo `role-` normativo). `project` queda con 3 skills.                                                        |
| D3  | Tipo de `plan-testing`  | `orchestrator` (planifica + ejecuta el plan de tests).                                                                   |
| D4  | Referencia a Impeccable | Prosa textual «external Impeccable skill (`impeccable-design-polish`)», sin flecha `→` (no es skill del catálogo).       |
| D5  | Versión                 | **9.0.0**.                                                                                                               |

## Mejoras incorporadas (revisión de implementación)

| Id  | Mejora                                                                                 | Dónde queda reflejada             |
| --- | -------------------------------------------------------------------------------------- | --------------------------------- |
| F1  | `project-status` sin `disable-model-invocation`; privilegios por operación en registry | § Diseño `project-status` + T3/T6 |
| F2  | Validación y migración de handoffs de `project.yaml` en la flota                       | § Capa mecánica + T11             |
| F3  | Contrato de frontera `role-linux` vs `project-status` vs `local-*`                     | § Diseño `role-linux`             |
| F4  | Validación de flechas `→` en el cuerpo de `SKILL.md`                                   | § Capa mecánica + T10             |
| F5  | Contrato de versionado de tres señales (producto / índice / skill)                     | § Versionado + T7/T9              |
| F6  | SSOT de la lista de roles + check de coherencia                                        | § Capa mecánica + T10             |
| F7  | ADR-0019 con la racionalidad del cambio                                                | T1                                |
| F8  | `git mv` para renames; renombrar antes de borrar                                       | § Proceso + T2–T5                 |
| F9  | Matiz de verificación: gate canónico vs `readiness` (exit 3)                           | § Verificación + T14              |

## Estado actual → estado destino

Estado actual (17): `plan` (plan-continue, plan-specification, plan-validators) · `local` (local-maintenance, local-security) · `project` (project-architecture, project-audit, project-libraries, project-machineroom, project-publish) · `role` (role-back, role-clean-code, role-design, role-front) · `web` (web-compliance, web-owasp, web-performance).

Estado destino (**14**):

| Dominio | Skills                                                          |
| ------- | --------------------------------------------------------------- |
| plan    | `plan-specification`, `plan-testing`                            |
| local   | `local-maintenance`, `local-security`                           |
| project | `project-architecture`, `project-status`, `project-machineroom` |
| role    | `role-back`, `role-clean-code`, `role-front`, `role-linux`      |
| web     | `web-compliance`, `web-owasp`, `web-performance`                |

Cambios:

| Operación        | De                  | A                | Motivo                                                                                                  |
| ---------------- | ------------------- | ---------------- | ------------------------------------------------------------------------------------------------------- |
| Rename + expand  | `project-libraries` | `role-linux`     | Rol de ingeniería Linux (arquitectura, compatibilidad, librerías, empaquetado, despliegue, instalación) |
| Rename + refocus | `plan-continue`     | `project-status` | Informe de estado + higienización + release                                                             |
| Rename + refocus | `plan-validators`   | `plan-testing`   | Plan completo de tests integrados, no solo TDD puntual                                                  |
| Baja             | `role-design`       | —                | Cubierto por Impeccable (externo)                                                                       |
| Baja             | `project-audit`     | —                | Absorbido por `project-status` (+ `web-*` y `role-linux` ya existentes)                                 |
| Baja             | `project-publish`   | —                | Absorbido por `project-status` (D1)                                                                     |

## Diseño por skill

### `role-linux` (nuevo, desde `project-libraries`)

- **Frontmatter:** `name: role-linux`, `metadata.domain: role`, `type: atomic`, `allowed-tools: Read, Grep, Glob, Bash, Write`, `language: en`. `metadata.execution: role-linux`.
- **Alcance (contrato de frontera, F3):** rol de **ingeniería del artefacto Linux**, no de operación de host ni de proceso de release. Cubre: arquitectura de apps Linux, compatibilidad/ABI, librerías y dependencias (hereda la faceta SCA/CVE de `project-libraries`), empaquetado Ubuntu/Debian (`.deb`, apt, PPA, Debian packaging) y Omarchy/Arch (PKGBUILD, pacman, AUR), build y despliegue/instalación del producto.
  - **vs `project-status`:** `role-linux` construye el artefacto y sus specs de paquete; `project-status` cierra y entrega (versionado, gates, CI/CD, publicación). Flecha `→ project-status`.
  - **vs `local-maintenance`/`local-security`:** `role-linux` opera sobre el artefacto del producto; `local-*` opera sobre el host. Flechas `→ local-maintenance`, `→ local-security`.
  - **vs `project-architecture`:** `project-architecture` es análisis de arquitectura genérico (cualquier stack); `role-linux` es la arquitectura/empaquetado específico de Linux. Flecha `→ project-architecture`.
- **Referencias:** conserva las 5 de `project-libraries` (dependency-audit-ecosystems, dependency-audit-pipeline, modern-threats, remediation-playbook, supply-chain) y añade nuevas para empaquetado/despliegue/instalación (deb, arch, deploy, install).
- **Registry:** `tool_id: role-linux`, `entrypoint: tools/execution`, `execution_kind: script`, `distribution: workspace-required`, `network: true`. Ops: `sca_scan` (read), `sbom_generate` (write-workspace) heredados; añadir `compat_check` (read) y `package`/`install` (mutación con `approval_required: true`; effect enum exacto se fija contra `registry.py` en TASKS).

### `project-status` (nuevo, desde `plan-continue` + `project-audit` + `project-publish`)

- **Frontmatter:** `name: project-status`, `metadata.domain: project`, `type: orchestrator`, `allowed-tools: Read, Grep, Glob, Bash, Write`. `metadata.execution: project-status`. **Sin `disable-model-invocation`** (F1): la lectura de estado debe ser invocable por el modelo.
- **Alcance:** orquestador **status → higiene → release** con tres etapas y referencias propias (no un cuerpo monolítico; progressive disclosure ≤200 líneas):
  1. **Observar:** leer estado de desarrollo (`.machineroom/status.yaml`, planes, ramas, cambios sin commitear) y emitir informe (status board P0/P1/P2, salud, Renovate/CI).
  2. **Higienizar:** limpiar ramas fusionadas, integrar trabajo no commiteado.
  3. **Cerrar:** gates locales, versionado, changelog, CI/CD, PR/merge-watch, empaquetado + publicación.
- **Privilegios por operación, no por skill (F1):** la lectura es libre; toda mutación pasa por el registry con aprobación. El conocimiento de release se conserva como `references/releasing.md` (sin diluirlo en el cuerpo).
- **Scripts consolidados (una sola copia):** `scan_repo.py`, `audit-repo.sh`, `check-product-structure.sh`, `inicio_plan.py` (hoy duplicados en `plan-continue/scripts` y `project-audit/scripts`) + `gate-husky.sh`, `review-vs-plan.py` (de `project-publish/scripts`).
- **Referencias:** hereda de `plan-continue` (inicio-plan, plantilla-informe, source-guide, citation-guide, verification-guide, etc.), de `project-audit` (inicio-plan, plantilla-informe, verification-guide) y de `project-publish` (cierre-trabajo, changelog-guide, versioning-guide); consolidar solapes y añadir `releasing.md`.
- **Registry:** `tool_id: project-status`, `entrypoint: tools/workspace-router`, `execution_kind: orchestrator`, `distribution: workspace-required`. Ops: `route` (read), `init` (write-workspace), `schema_write` (write-workspace), `integrate` (write-workspace), `status` (read), `status_board` (write-workspace) sin aprobación; `hygiene` (mutación git, `approval_required: true` para borrado de ramas); `local_gates` (write-workspace, sin aprobación, heredado de project-publish); `publish` (`communicate-external`, `approval_required: true`).
- **El pipeline DEFINE→…→STATUS sigue vivo** en `tools/workspace-router`; `project-status` envuelve observación, higienización, integración y release. Mapeo: DEFINE→`plan-specification`, SCHEMAS→`project-status`, IMPLEMENT→`role-*`, VALIDATE→`plan-testing`, INTEGRATE→`project-status`, STATUS→`project-status`.

### `plan-testing` (nuevo, desde `plan-validators`)

- **Frontmatter:** `name: plan-testing`, `metadata.domain: plan`, `type: orchestrator`, `allowed-tools: Read, Grep, Glob, Bash, Write`. `metadata.execution: plan-testing`.
- **Alcance:** al lanzarla, leer el estado actual del proyecto y producir un **plan completo de tests integrados** (rutas, funcionalidades, componentes, jobs, flujos e2e) apoyado en referencias profesionales y guías estándar; después ejecutar con red-green-refactor. «Auténticos e integrales», no trivialidades.
- **Frontera con `plan-specification`:** `plan-specification` define QUÉ construir y sus criterios de aceptación; `plan-testing` define CÓMO probarlo con tests integrados y ejecuta ese plan. Flecha `→ plan-specification`.
- **Referencias:** conserva las 5 de `plan-validators` (test-pyramid-and-sizes, writing-good-tests, rationalizations-and-flags, cookbook, test-patterns).
- **Registry:** `tool_id: plan-testing`, `entrypoint: tools/execution`, `execution_kind: agent`. Ops: `discover_stack` (read), `test_plan` (write-workspace), `implement_tests` (write-workspace, `completion_phases: [VALIDATE]`).

### Bajas

- **`role-design`:** eliminar `skills/role-design/` (SKILL.md + 11 referencias). Diseño → Impeccable externo.
- **`project-audit`:** eliminar `skills/project-audit/` (SKILL.md + 3 referencias + scripts, ya consolidados en `project-status`). Reparto: tablero/salud → `project-status`; dependencias → `role-linux`; auditorías web → `web-*` (ya existentes).
- **`project-publish`:** eliminar `skills/project-publish/` (SKILL.md + referencias + scripts, ya consolidados en `project-status`).

## Capa mecánica compartida

Tocar (paridad obligatoria entre catálogo, router, registry y docs):

- `skills/*/SKILL.md` — frontmatter y descripciones con `→` actualizados; **quitar toda flecha `→ role-design` / `→ project-audit` / `→ project-libraries` / `→ project-publish` / `→ plan-continue` / `→ plan-validators`** y sustituir por `→ role-linux` / `→ project-status` / `→ plan-testing`, o por prosa para Impeccable. Aplicar también en el **cuerpo** (F4).
- `tools/execution/registry.yaml` — tool_ids renames + bajas + ops nuevas con `approval_required` según § Diseño.
- `tools/skill-router/intent-map.yaml` — intents: `plan_continuar`/`release`/`hooks`/`repo_starting` → `project-status`; `libraries` → `role-linux` (+ patrones de empaquetado/despliegue/compatibilidad); `validar_tdd` → `testing`/`plan-testing`; **eliminar** intent `design`; `arquitectura` sin `plan-continue`.
- `tools/workspace-router/project_load.py` — `handoff_for_phase`: SCHEMAS/STATUS → `project-status`, VALIDATE → `plan-testing`, INTEGRATE → `project-status`. **Añadir validación de handoffs contra el catálogo con pista de migración** (F2).
- `tools/contracts/schemas/plan.schema.json` — enum `roles`: quitar `role-design`, añadir `role-linux`; pasa a ser el **SSOT** de la lista de roles (F6).
- `tools/contracts/validate_contracts.py` — `REQUIRED_REGISTRY_TOOLS`: `plan-continue`→`project-status`, quitar `project-publish`.
- `templates/harness/project.yaml`, `templates/product/.machineroom/project.yaml`, `.machineroom/project.yaml` — handoffs: `continue: project-status`, `validate: plan-testing`, `libraries: role-linux`, `integrate_publish`→`integrate_release: project-status`; quitar `implement_design`.
- `skill-index.json` (regenerado) + `docs/architecture/skill-index-9.0.0.json` (snapshot nuevo) + `tools/skill-index/generate.py` (`INDEX_VERSION` → `9.0.0`) + `run-validation.sh` (paso 5b apunta al snapshot 9.0.0).
- `README.md`, `docs/TAXONOMY.md`, `AGENTS.md`, `ARCHITECTURE.md`, `docs/routing.md`, `docs/harness-integration.md` — «14 skills», nombres nuevos, rutado de roles sin `role-design` y con `role-linux`, pipeline con `plan-testing`/`project-status`, semántica de dominios (F3/F5).
- `.cursor/agents/mr-verifier.md`, `extensions/machineroom/agents/worker.md` — lista de roles sin `role-design`, con `role-linux`.
- Tests: `tools/skill-router/tests/test_catalog_17.py`→`test_catalog_14.py` (EXPECTED_COUNT 14), `test_route.py`, `tools/execution/tests/*` (registry/ops counts), `tools/harness/tests/test_cursor_install.py`, `test_runtime.py`, `test_pi_catalog_discovery.py`, `scripts/tests/*` (nombres de skill).
- `mypy.ini`/`ruff.toml` — quitar exclusiones específicas de `project-audit` (módulos duplicados desaparecen).
- `CHANGELOG.md` — entrada `[Unreleased]`→`[9.0.0]` (Keep a Changelog): Added/Changed/Removed.

**Validadores nuevos (lock-in, se añaden cuando el árbol ya está limpio):**

- `tools/validate/skill_spec.py` — (a) validar flechas `→` en el **cuerpo** de `SKILL.md` (F4); (b) derivar el conteo «N skills» de los intro de `README.md`/`docs/TAXONOMY.md` y rechazar divergencia (hoy dicen «16» con 17 reales); (c) check de coherencia de la lista de roles en `AGENTS.md`/`README.md`/`plan-specification` contra el enum de `plan.schema.json` (F6).
- `tools/workspace-router/project_load.py` — validar `handoffs.*` contra el catálogo con tabla de migración `plan-continue→project-status`, `plan-validators→plan-testing`, `project-libraries→role-linux`, `project-publish→project-status` (F2). `doctor.py` marca handoffs obsoletos.

**Fuera de alcance (historia):** `docs/plans/*`, `tasks/*` anteriores, `.machineroom/SPEC.md` (marcada OBSOLETA), `.github/policy-exceptions.md` — se dejan como historia.

## Versionado (contrato de tres señales, F5)

| Señal                                                                                        | Significado                                     | Valor en 9.0.0                                  |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| `package.json` `version`                                                                     | Versión de producto/repo                        | `9.0.0`                                         |
| `skill-index.json` `version` (top-level) + snapshot `docs/architecture/skill-index-<v>.json` | Versión del índice de catálogo                  | `7.0.0` → `9.0.0`                               |
| `metadata.version` por skill                                                                 | SemVer independiente por skill; bump al tocarla | policy final en TASKS; `check-bump` lo verifica |

Documentar este contrato en `docs/TAXONOMY.md` (o `GLOSARIO.md`) para que no vuelva a descuadrarse.

## Proceso

- Usar **`git mv`** para renames (`project-libraries`, `plan-continue`, `plan-validators`) y `git rm` para bajas, de modo que Git detecte renames y los diffs queden limpios (F8).
- **Renombrar primero, borrar al final** dentro de la rama, para minimizar el radio de cada commit y que la revisión sea legible (F8).
- Una rama de trabajo `plan/9.0.0-catalog-restructure`; commits atómicos por fase.

## Lista de tareas (índice ordenado)

### Fase 0 — Preparación

- T0. Baseline verde en `main` (`make validate && make test && make smoke`) + rama `plan/9.0.0-catalog-restructure`.

### Fase 1 — ADR y renames

- T1. `ADR-0019` (racionalidad del catálogo v9: role-linux, project-status absorbe release, plan-testing, bajas, privilegios por operación).
- T2. `git mv skills/project-libraries skills/role-linux`; reescribir `SKILL.md` (frontmatter + Overview + When to Use con contrato de frontera F3); conservar 5 referencias SCA; añadir referencias de empaquetado/despliegue/instalación.
- T3. `git mv skills/plan-continue skills/project-status`; `SKILL.md` como orquestador status→higiene→release (F1); consolidar scripts de `project-audit/scripts` y `project-publish/scripts` en `project-status/scripts`; añadir `references/releasing.md`.
- T4. `git mv skills/plan-validators skills/plan-testing`; `SKILL.md` re-enfocado + referencias.

### Fase 2 — Bajas y cross-refs

- T5. `git rm` de `skills/role-design`, `skills/project-audit`, `skills/project-publish` (tras consolidar scripts en T3).
- T6. Cross-refs de todas las skills restantes + `registry.yaml` + `intent-map.yaml` + `project_load.py` handoffs + `plan.schema.json` roles + plantillas `project.yaml`.

### Fase 3 — Capa mecánica y docs

- T7. `README.md`, `docs/TAXONOMY.md`, `AGENTS.md`, `ARCHITECTURE.md`, `docs/routing.md`, `docs/harness-integration.md`, `mr-verifier.md`/`worker.md`; semántica de dominios y contrato de versionado (F3/F5).
- T8. `skill-index.json` + snapshot `skill-index-9.0.0.json` + `INDEX_VERSION` + `run-validation.sh` paso 5b.
- T9. Tests de catálogo/router/registry/install/harness + `mypy.ini`/`ruff.toml`.

### Fase 4 — Validación (lock-in)

- T10. `skill_spec.py`: flechas `→` en cuerpo (F4), conteo «N skills» derivado, coherencia de roles contra `plan.schema.json` (F6).
- T11. `project_load.py`: validación de handoffs contra catálogo + tabla de migración (F2); `doctor.py` marca handoffs obsoletos.

### Fase 5 — Cierre

- T12. `CHANGELOG.md` `[9.0.0]` + bump versiones (`package.json`, `metadata.version`).
- T13. Gate canónico: `make validate && make test && make smoke` (F9).

### Checkpoints

- **CP1 (tras Fase 1):** renames hechos con `git mv`; `role-linux`, `project-status`, `plan-testing` existen; cross-refs de renames resueltos.
- **CP2 (tras Fase 2):** catálogo en 14; registry/intent-map sin referencias a skills dadas de baja.
- **CP3 (tras Fase 3):** docs, snapshot e índice coherentes; `make validate` verde.
- **CP4 (tras Fase 4):** validadores nuevos en verde sobre el árbol limpio.
- **CP5 (final):** gate canónico verde; revisión del operador antes de publicar.

> Nota: por ser una restructuración acoplada, la paridad cross-ref solo queda verde al final de cada fase; el gate canónico es `make validate` verde en CP3/CP4. Commits intermedios pueden quedar rojos en validación de enlaces.

## Verificación (F9)

- Gate canónico local: `make validate && make test && make smoke`.
- `make readiness` incluye natives/e2e y trata el exit 3 (`blocked`/`not_run`) como bloqueo duro; para el cierre local no es requisito y puede omitirse o reportarse como `not_run`.
- `make validate-harnesses` y `make e2e-orchestration` pueden salir `blocked`/`not_run` sin ser fallo en local.

## Riesgos

| Riesgo                                                                              | Impacto | Mitigación                                                                        |
| ----------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------- |
| Rotura de cross-refs en `skill_spec.py`/`skill_links.py` a mitad de restructuración | Medio   | Ordenar por fases; validar en cada checkpoint; gate canónico al final             |
| Perder ops de registry al renombrar tool_ids                                        | Alto    | Migrar ops antes de borrar tool_ids; `registry --check` + `validate_contracts`    |
| `project-status` tiende a god skill                                                 | Alto    | F1: etapas con referencias propias, cuerpo ≤200 líneas, privilegios por operación |
| Handoffs obsoletos en repos de la flota (fuera de este repo)                        | Alto    | F2: validación con tabla de migración + `doctor.py`                               |
| Tests de catálogo con conteos hardcodeados (17/16)                                  | Medio   | Actualizar EXPECTED_COUNT y nombres en la misma fase que las bajas                |
| Duplicación de scripts `inicio_plan.py`/`scan_repo.py`                              | Bajo    | Consolidar en `project-status/scripts` y limpiar `mypy.ini`/`ruff.toml`           |
| Snapshot congelado `skill-index-8.0.0.json` desincronizado                          | Medio   | Regenerar a `skill-index-9.0.0.json` y actualizar `run-validation.sh`             |
| Ambigüedad de frontera `project-status` vs `project-publish`                        | Alto    | Resuelto por D1: absorción total, `project-publish` se elimina                    |
| Señales de versión descuadradas                                                     | Medio   | F5: contrato documentado y bump coherente en una fase                             |

## Preguntas resueltas

1. Frontera release → absorción total en `project-status` (D1).
2. Dominio `role-linux` = `role` (D2).
3. Tipo `plan-testing` = `orchestrator` (D3).
4. Impeccable referenciado en prosa, sin flecha (D4).
5. Versión 9.0.0 (D5).

## Confirmación pendiente única

- La absorción de release (D1) **implica dar de baja `project-publish`**. Si el operador prefería conservarlo con otro cometido, indicarlo antes de iniciar; el plan asume su eliminación.
