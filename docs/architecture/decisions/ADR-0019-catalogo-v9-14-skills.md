---
version: "1.0.0"
date: "2026-11-17"
status: "Accepted"
adr_id: "ADR-0019"
priority: "P0"
---

# ADR-0019: Catálogo v9 — reestructuración a 14 skills

**Fecha:** 2026-11-17
**Estado:** Accepted
**Prioridad:** P0

### Propósito de este documento

- **Objetivos:** Registrar la reestructuración del catálogo 8.x (17 skills) a 9.0.0 (14 skills): tres renames con reenfoque, tres bajas por absorción y el contrato de privilegios que la sostiene. Fija qué no se reabre.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** Es una decisión del _producto_ machineroom. Un repo de producto que consuma el catálogo debe enlazarla, no copiarla; sus `handoffs` se actualizan con la tabla de migración del plan.

## Contexto

El catálogo 8.1.1 arrastraba cinco desajustes que se reforzaban entre sí:

1. **Responsabilidad difusa.** `plan-continue`, `project-audit` y `project-publish`
   compartían tres cosas: scripts duplicados (`scan_repo.py`, `audit-repo.sh`,
   `inicio_plan.py` en dos carpetas), el tablero de estado y el cierre de
   release. Ninguna de las tres tenía una responsabilidad única.
2. **`project-libraries` anunciaba más de lo que era.** Se declaraba auditoría
   SCA de dependencias, mientras el operador necesitaba un rol de ingeniería
   Linux completo (arquitectura, compatibilidad, librerías, empaquetado
   Ubuntu/Debian y Omarchy/Arch, despliegue, instalación).
3. **`plan-validators` era TDD puntual, no plan de pruebas.** El operador pedía
   que la skill, al lanzarse, leyera el proyecto y produjera un plan completo de
   tests integrados, no una simplicidad.
4. **`role-design` estaba fuera de lugar.** La dirección visual vive en Impeccable
   (`impeccable-design-polish`), instalado fuera de este catálogo; mantener el rol
   duplicaba la superficie y arrastraba once referencias de diseño.
5. **Privilegios por skill, no por operación.** `project-publish` llevaba
   `disable-model-invocation: true` porque mutaba; al absorber su capacidad de
   release en una skill que también debe _leer_ estado, el flag dejaba de ser
   correcto en cualquier posición.

A esto se sumaban tres deudas de verificación: las flechas `→` solo se validaban
en `description` (no en el cuerpo), el conteo «N skills» de los intro ya divergía
del catálogo real, y los `handoffs` de `.machineroom/project.yaml` no se validaban
contra el catálogo, así que un rename rompía silenciosamente los repos de la flota.

## Decisión

1. **Catálogo de 14 skills en cinco dominios** (`plan` 2, `local` 2, `project` 3,
   `role` 4, `web` 3). El prefijo `name` sigue siendo el dominio, normativo.
2. **Tres renames con reenfoque**, sin altas nuevas:
   - `project-libraries` → **`role-linux`** (`project`→`role`): rol de ingeniería
     del artefacto Linux. Absorbe la faceta SCA/CVE como una de sus caras y añade
     compatibilidad/ABI, empaquetado `.deb`/apt/PPA, PKGBUILD/pacman/AUR,
     despliegue e instalación.
   - `plan-continue` → **`project-status`** (`plan`→`project`): orquestador
     _observar → higienizar → cerrar_. Absorbe el tablero de `project-audit` y el
     release de `project-publish`.
   - `plan-validators` → **`plan-testing`** (`plan`, `atomic`→`orchestrator`):
     lee el estado del proyecto y produce un plan completo de tests integrados,
     después ejecuta con red-green-refactor.
3. **Tres bajas por absorción**: `role-design` (a Impeccable, externo),
   `project-audit` (tablero → `project-status`; dependencias → `role-linux`;
   superficie web → `web-*`) y `project-publish` (release → `project-status`).
4. **Privilegios por operación, no por skill.** `project-status` no lleva
   `disable-model-invocation`: la lectura de estado debe poder invocarla el
   modelo. La mutación se gana en `tools/execution/registry.yaml`:
   `hygiene` y `publish` con `approval_required: true`; `route`, `status` y
   `status_board` sin aprobación. `disable-model-invocation` queda reservado a
   `local-*`, que mutan el host.
5. **Frontera explícita `role-linux` / `project-status` / `local-*`.**
   `role-linux` construye el artefacto y sus specs de paquete;
   `project-status` cierra y entrega (versionado, gates, CI/CD, publicación);
   `local-*` opera el host. Las tres se enlazan con flechas cruzadas.
6. **Referencias externas sin flecha.** Impeccable se cita en prosa como
   «external Impeccable skill (`impeccable-design-polish`)»: no es una skill del
   catálogo y una flecha `→` rompería la validación de referencias.
7. **Verificación acoplada al cambio.** En el mismo incremento se cierran las
   tres deudas: flechas `→` validadas también en el cuerpo, conteo de skills
   derivado del generador y `handoffs` validados contra el catálogo con tabla de
   migración.
8. **Versión `9.0.0`** (BREAKING: renames y bajas) y contrato de **tres señales**
   de versión documentado (producto, índice de catálogo, skill).

## Consecuencias

- Un repo de la flota con `handoffs` viejos (`continue: plan-continue`,
  `validate: plan-validators`, `libraries: project-libraries`,
  `integrate_publish: project-publish`) deja de resolver en silencio: el router
  avisa y el `doctor` lo marca, con tabla de migración explícita.
- `project-status` es la skill más grande del catálogo por responsabilidad; se
  contrarresta con tres etapas documentadas en `references/` y cuerpo corto, no
  con un `SKILL.md` monolítico.
- La ejecución mutadora sigue pasando por `run_registered`; el release conserva
  `approval_required: true` aunque la skill ya no lo bloquee por frontmatter.
- Los scripts de estado quedan en una sola copia (`project-status/scripts`), lo
  que elimina las exclusiones de `mypy`/`ruff` que existían por el módulo
  duplicado.
- Adoptar Impeccable como dependencia externa implica que el diseño visual deja
  de ser verificable por `make validate` de este repo.

## Prioridad

**P0**: el catálogo es el contrato de ruteo de toda la flota. Mantener 17 skills
con responsabilidades solapadas degrada cada plan que arranca con el router.

## Checklist de implementación

- [x] ADR-0019 publicado e indexado en `docs/architecture/decisions/README.md`.
- [x] `git mv` de las tres skills y reescritura de `SKILL.md` + referencias.
- [x] Bajas de `role-design`, `project-audit` y `project-publish`.
- [x] `registry.yaml`, `intent-map.yaml`, `project_load.py`, `plan.schema.json`,
      plantillas `project.yaml` y docs sincronizados a 14 skills.
- [x] `skill-index.json` regenerado y snapshot `skill-index-9.0.0.json`.
- [x] `skill_spec.py` valida flechas de cuerpo, conteo de skills y lista de roles.
- [x] `project_load.py` valida `handoffs` contra el catálogo.
- [x] `CHANGELOG.md` `[9.0.0]` y bump de `package.json`.
- [x] `make validate && make test && make smoke` en verde.

## Alternativas

- **Mantener 17 skills y sólo documentar fronteras.** Descartada: no elimina la
  duplicación de scripts ni el solape de release, y el operador ya había pedido
  la absorción.
- **Crear `project-release` como cuarta skill separada de `project-status`.**
  Descartada: el operador decidió la absorción total; además el release sin
  lectura previa de estado era precisamente el fallo de `project-publish`.
- **Reclasificar `project-libraries` a `audit` y añadir `role-linux` aparte.**
  Descartada: dos skills para una sola superficie (ingeniería Linux) y una de
  ellas mentiría sobre su privilegio real.
- **Mantener `role-design` como rol del catálogo y usar Impeccable como
  referencia.** Descartada: duplica la dirección visual y arrastra once
  referencias mantenidas a mano.

## Relacionados

- [ADR-0010](ADR-0010-semver-contrato-estandar.md): SemVer del contrato.
- [ADR-0017](ADR-0017-centralizacion-execution-min-priv.md): execution central y
  mínimo privilegio.
- [ADR-0018](ADR-0018-rename-a-machineroom.md): rename a machineroom; este ADR es
  el primer incremento que aprovecha el 9.0.0 para retirar el fallback legacy.
- Plan canónico del incremento: `tasks/plan-9.0.0-catalog-restructure.md`.
