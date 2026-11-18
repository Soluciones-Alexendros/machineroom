---
name: Cohesión plano control
overview: "Spec y tareas ejecutables (plan-specification) para cohesionar el plano de control de machineroom 9.1.0 en Python 3.12: cargador único de índice, corte del fallback .autoworkspace, partición de status_bump y un solo bootstrap de imports. Sin Notion y sin cambio de lenguaje."
todos:
  - id: canon-architecture
    content: "T1 ARCHITECTURE.md: typo de directorio, roles vivos y los tres routers"
    status: in_progress
  - id: canon-adr-plan9
    content: T2 Cerrar checklist ADR-0019 y la confirmación obsoleta de project-publish en el plan 9.0.0
    status: pending
  - id: canon-history-changelog
    content: T3 Marcar tasks/plan.md y tasks/todo.md como histórico y retarget de pies CHANGELOG 9.x
    status: pending
  - id: index-loader
    content: T4 load_skill_index compartido por workspace-router y skill-router
    status: pending
  - id: index-shim
    content: T5 build_index.py delega en el cargador único sin un segundo importlib
    status: pending
  - id: outcome-alias
    content: T6 evidence.py usa PHASE_BLOCKING_OUTCOMES; se retira el alias NON_TERMINAL de ops.py
    status: pending
  - id: structured-failure
    content: T7 StructuredFailure como base de los cinco errores component/function/detail
    status: pending
  - id: legacy-fallback
    content: T8 state_dir falla si solo existe .autoworkspace y señala migrate_state
    status: pending
  - id: legacy-naming-ssot
    content: T9 state_paths importa los dirname desde harness/naming.py
    status: pending
  - id: legacy-doctor-home
    content: T10 doctor falla si solo existe ~/.autoworkspace y nombra migrate_legacy_runtime
    status: pending
  - id: split-task-lifecycle
    content: T11 Extraer el ciclo plan/tarea de status_bump.py con reexport
    status: pending
  - id: split-phase-advance
    content: T12 Extraer advance_status y resolve_awaiting_agent con reexport
    status: pending
  - id: bootstrap-module
    content: T13 Crear tools/_bootstrap.py
    status: pending
  - id: bootstrap-routers
    content: T14 Entry points de workspace-router, orchestrator y skill-router usan el bootstrap
    status: pending
  - id: bootstrap-harness
    content: T15 Entry points de harness usan el bootstrap
    status: pending
  - id: bootstrap-contracts
    content: T16 Entry points de validate y contracts usan el bootstrap
    status: pending
  - id: validate-close
    content: "Checkpoint final: make validate y npm run typecheck, sin promover skip a PASS"
    status: pending
isProject: false
---

# Spec: cohesión del plano de control

Documento único de este incremento. Al ejecutarlo se copia a `tasks/plan-9.2.0-control-plane-cohesion.md`. [tasks/plan.md](plan.md) y [tasks/todo.md](todo.md) siguen siendo el archivo histórico v5: no se sobrescriben. La lista de tareas vive en ese archivo nuevo, no en un `tasks/todo.md` paralelo.

Aprobar este documento no autoriza commit, push, PR ni release.

## Capability map

Ids estables. La flecha es dependencia de construcción, en un solo sentido.

- `canon-literals` — textos vivos del repo. Depende de: nada.
- `skill-index-loader` — un cargador del índice de skills. Depende de: `canon-literals` (el texto de los tres routers ya está escrito).
- `outcome-and-errors` — outcomes de execution y base de error estructurado. Depende de: nada.
- `legacy-state-cut` — fin del fallback `.autoworkspace`. Depende de: `outcome-and-errors` (`StateDirError` ya hereda la base).
- `status-bump-split` — partir [tools/workspace-router/status_bump.py](../tools/workspace-router/status_bump.py). Depende de: `legacy-state-cut` (commits separados; el YAML de estado no se toca en el mismo diff que el corte legacy).
- `import-bootstrap` — un solo `sys.path` de producción. Depende de: `skill-index-loader`, `status-bump-split`.

Orden: `canon-literals` → `skill-index-loader` en paralelo lógico con `outcome-and-errors` → `legacy-state-cut` → `status-bump-split` → `import-bootstrap`. En una sola sesión van en ese orden, secuencial.

Fuera del mapa: reescritura de `tools/validate/`, skills nuevas, ampliar el registry (14 skills / 10 tools es intencional), el bloque OpenCode ya anotado en `CHANGELOG` `[Unreleased]`, y cualquier migración a Rust, Go u otro lenguaje.

## Assumptions

1. El producto sigue en Python 3.12 (`requires-python` en [tools/pyproject.toml](../tools/pyproject.toml)) con mypy estricto. El cuello de botella es subprocess, YAML y git, así que el lenguaje no cambia.
2. [extensions/machineroom/](../extensions/machineroom/) sigue siendo el borde Pi sobre los JSON de política. Node no gana un segundo pipeline.
3. `package = false` se mantiene. El arreglo de imports es un bootstrap, no un paquete instalable.
4. [tools/harness/naming.py](../tools/harness/naming.py) es la SSOT de los dirname. [tools/state_paths.py](../tools/state_paths.py) importa desde ahí.
5. [tools/skill-router/build_index.py](../tools/skill-router/build_index.py) sigue existiendo: [.machineroom/SPEC.md](../.machineroom/SPEC.md) lo invoca. Deja de copiar el `importlib`.
6. `migrate_state` (repo) y `migrate_legacy_runtime` (hogar, [tools/harness/runtime.py](../tools/harness/runtime.py)) siguen siendo las únicas mudanzas. Este incremento no mueve `~/.autoworkspace` del operador.
7. Los `sys.path.insert` de `tools/**/tests/` se quedan. El bootstrap cubre solo entry points de producción.
8. Los compare del `CHANGELOG` anteriores a 9.0.0 siguen en `Soluciones-Alexendros/autoworkspace` si GitHub redirige. Se retargetean `[Unreleased]` y las anclas 9.x.

## Objective

Un agente puede ejecutar cada tarea en una sesión, con un pytest concreto y sin redescubrir el diseño. Al terminar, el plano de control tiene un solo cargador de índice, un solo vocabulario de fallo no terminal en execution, errores `component`/`function`/`detail` con la misma base, el fallback silencioso de `.autoworkspace` sustituido por un error que nombra la migración, `status_bump.py` reducido a I/O más reexports, y un solo bootstrap de `sys.path` en producción.

## Tech stack

Python 3.12, PyYAML, pytest 9.0.3, ruff, mypy 2.4.0, jsonschema 4.26.0. Sin dependencias nuevas. TypeScript solo en la extensión Pi, que este incremento no edita.

## Commands

Desde la raíz del repo:

```bash
uv run --project tools --frozen pytest tools/<paquete>/tests/<fichero>.py -q
make validate
npm run typecheck
```

`make test` es la suite ancha (`pytest tools/` más tests de skills). El cierre de fase usa `make validate` y `npm run typecheck`. Un `skip`, una dependencia ausente o un `not_run` no es PASS.

## Project structure

- `tools/skill-index/` — generador del índice y, tras T4, `load.py`
- `tools/skill-router/` — router de intención; `build_index.py` es el CLI documentado
- `tools/workspace-router/` — router de fase y estado (`.machineroom/`)
- `tools/orchestrator/` — DAG del plan activo
- `tools/execution/` — `run_registered`, approval, evidence
- `tools/contracts/` — esquema de resultado
- `tools/harness/` — Cursor, Pi, OpenCode, doctor, naming
- `tools/state_paths.py` — directorio de estado del repo
- `tasks/plan-9.2.0-control-plane-cohesion.md` — copia de este documento cuando se ejecute

## Code style

Python 3.12 con `from __future__ import annotations`. Errores de frontera con `component`, `function`, `detail` y `to_dict()`. La API pública que hoy importan orchestrator y tests se reexporta desde `status_bump.py`: `status_path`, `load_status`, `migrate_status`, `activate_plan`, `load_active_plan`, `ready_tasks`, `start_task`, `await_task`, `complete_task`, `fail_task`, `block_task`, `cancel_task`, `retry_task`, `bump_kind_for_phase`, `advance_status`, `resolve_awaiting_agent`. Mypy estricto sigue verde. Ruff no añade noqa nuevos para tapar tamaño: el split existe para quitarlos de las funciones que se mueven, no para silenciarlos en el sitio viejo.

## Testing strategy

Pytest ya vive en `tools/<area>/tests/`. Cada tarea nombra el fichero que debe seguir verde y el que cambia de expectativa. No se añade cobertura de módulos que esta spec no toca. Niveles: unidad del módulo movido y el test de integración ya existente (`test_scheduler.py`, `test_task_lifecycle.py`). No hay UI que abrir en navegador.

## Boundaries

- Always: reevaluar `role-back` antes de T4–T10 y T13–T16, y `role-clean-code` junto con `role-back` antes de T11–T12. Correr el pytest de la tarea antes de darla por hecha. Editar el código del repo con las herramientas del agente.
- Ask first: dependencia nueva, editar workflows de CI, borrar `build_index.py`, ejecutar `migrate_legacy_runtime` sobre el hogar real del operador.
- Never: página o base de Notion; sobrescribir [tasks/plan.md](plan.md) o [tasks/todo.md](todo.md); reescribir el plano de control en otro lenguaje; ampliar el registry; commit, push, PR o release sin pedido explícito; invocar scripts mutadores de skill o `run_registered` para aplicar este refactor.

## Success criteria

- `load_catalog` y `load_index` llaman a la misma función en `tools/skill-index/load.py`.
- `execution.ops.NON_TERMINAL` no existe. `evidence.py` importa `PHASE_BLOCKING_OUTCOMES`. `contracts.result.NON_TERMINAL` sigue siendo solo `awaiting_agent` y `awaiting_approval`.
- `StateDirError`, `DenyListError`, `ModelScopeError`, `ContractError` e `InstallFailure` heredan una base común con `to_dict()`.
- Con solo `.autoworkspace` en un repo temporal, `state_dir` lanza `StateDirError` y el detalle nombra `migrate_state`. `migrate_state` en dry-run sigue sin borrar nada.
- `PROJECT_DIRNAME` y `LEGACY_PROJECT_DIRNAME` se definen una vez, en `harness/naming.py`.
- Doctor, con home temporal que solo tiene `.autoworkspace`, reporta fallo y nombra `migrate_legacy_runtime`. No mueve ese directorio.
- `status_bump.py` reexporta la lista de Code style y baja de 804 líneas a I/O, lock y reexports. `advance_status` y `complete_task` conservan firma y YAML.
- Los entry points de producción listados en T14–T16 no contienen `sys.path.insert`. Los tests sí pueden contenerlo.
- `make validate` y `npm run typecheck` salen 0 en la misma sesión.

## Open questions

Ninguna. Las decisiones están en Assumptions.

## Architecture decisions

- Python 3.12 permanece. Rust o Go no acortan un plano de control limitado por procesos externos.
- El fallback `.autoworkspace` deja de resolver en silencio. `REMOVAL_VERSION` en `state_paths.py` pasa a la versión de este incremento; el texto del error dice que el anuncio fue 9.0.0.
- `status_bump.py` conserva el nombre de módulo importable. Los módulos nuevos son `task_lifecycle.py` y `phase_advance.py` en el mismo paquete. La I/O (`load_status`, lock, escritura atómica) se queda en `status_bump.py` para no abrir un tercer corte.
- `import-bootstrap` no toca tests. Convertir `tools` en paquete instalable queda fuera.

## Risks and mitigations

- Corte legacy: un checkout de la flota con solo `.autoworkspace` deja de rutear hasta `migrate_state`. Mitigación: el `detail` del error nombra la función; T8 incluye un test de ese texto; no se mezcla con T11.
- Split de `status_bump.py`: un cambio de forma del YAML colaría en el refactor. Mitigación: T11 y T12 no editan las cadenas escritas; la puerta es `test_task_lifecycle.py`, `test_status_bump.py` y `test_scheduler.py` antes y después.
- Bootstrap: un entry point olvidado vuelve a insertar la ruta. Mitigación: T16 termina con una búsqueda `sys.path.insert` limitada a los ficheros de producción listados, que debe dar cero.

## Task list

Cada tarea es S o M. Al empezarla, reevaluar el rol declarado. Parar si el diff necesita un fichero que no está en Files.

### Fase 1 — Canon

**T1: Alinear ARCHITECTURE.md.** Tamaño S.

Descripción: Corregir el párrafo que llama legacy a `.machineroom/` y destino a la misma ruta: el directorio vivo es `.machineroom/` y el legacy es `.autoworkspace/`. La frase de selección por tarea nombra `role-back`, `role-front`, `role-clean-code`, `role-linux` e Impeccable. Añadir tres frases: `workspace-router` elige la skill de fase, `skill-router` elige por intención, `orchestrator` ejecuta el DAG del plan activo.

Acceptance:

- Las líneas 7 y 11 ya no dicen que `.machineroom/` migra hacia `.machineroom/`.
- La línea 53 no presenta `design` como rol del catálogo.
- El árbol de routers distingue fase, intención y DAG.

Verify: lectura del diff de [ARCHITECTURE.md](../ARCHITECTURE.md). `make validate` en el checkpoint.

Roles: ninguno de implementación. Test surfaces: gate de terminología dentro de `make validate`. Files: [ARCHITECTURE.md](../ARCHITECTURE.md). Dependencies: ninguna.

**T2: Cerrar ADR-0019 y el pendiente del plan 9.0.0.** Tamaño S.

Descripción: Marcar hechas en el checklist de implementación de [docs/architecture/decisions/ADR-0019-catalogo-v9-14-skills.md](../docs/architecture/decisions/ADR-0019-catalogo-v9-14-skills.md) las casillas que el árbol ya cumple (bajas de `role-design`, `project-audit`, `project-publish`, catálogo de 14). En [tasks/plan-9.0.0-catalog-restructure.md](plan-9.0.0-catalog-restructure.md), la sección «Confirmación pendiente» pasa a una línea de cierre: `project-publish` quedó absorbido por `project-status`.

Acceptance:

- El checklist de implementación no deja en `[ ]` una baja que ya no tiene carpeta en `skills/`.
- El plan 9.0.0 no pide confirmar esa baja.

Verify: `rg -n "^- \\[ \\]" docs/architecture/decisions/ADR-0019-catalogo-v9-14-skills.md` no muestra las bajas ya hechas. Lectura de la sección de confirmación.

Roles: ninguno. Test surfaces: ninguna de runtime. Files: los dos markdown citados. Dependencies: ninguna.

**T3: Histórico y pies de CHANGELOG.** Tamaño S.

Descripción: Primera línea de [tasks/plan.md](plan.md) y [tasks/todo.md](todo.md): son el plan v5 archivado, no el incremento vivo. En [CHANGELOG.md](../CHANGELOG.md), retarget de `[Unreleased]` y de las anclas cuya versión es 9.x hacia `Soluciones-Alexendros/machineroom`, después de comprobar con `gh repo view Soluciones-Alexendros/machineroom --json name,url` que el rename redirige. Las anclas anteriores a 9.0.0 se quedan.

Acceptance:

- Los dos archivos históricos se identifican como archivo en la primera línea, y el resto de su contenido no cambia.
- `[Unreleased]` y las anclas 9.x apuntan a `machineroom`.

Verify: `gh repo view` (solo lectura) y diff de las tres cabeceras/pies. Checkpoint de fase: `make validate`.

Roles: ninguno. Test surfaces: higiene de `make validate`. Files: [tasks/plan.md](plan.md), [tasks/todo.md](todo.md), [CHANGELOG.md](../CHANGELOG.md). Dependencies: ninguna.

### Checkpoint: Canon

- `make validate` sale 0.
- T1–T3 no han tocado Python.

### Fase 2 — Índice

**T4: Cargador único del índice.** Tamaño M. Rol: `role-back`.

Descripción: Crear `tools/skill-index/load.py` con `load_skill_index(repo) -> dict`. [tools/workspace-router/run.py](../tools/workspace-router/run.py) `load_catalog` y [tools/skill-router/route.py](../tools/skill-router/route.py) `load_index` la llaman. La generación sigue en [tools/skill-index/generate.py](../tools/skill-index/generate.py).

Acceptance:

- Una sola función carga el índice para los dos routers.
- El JSON devuelto coincide con el que hoy construye `generate.build_index` en los tests de catálogo.

Verify:

```bash
uv run --project tools --frozen pytest tools/skill-router/tests/test_route.py tools/skill-router/tests/test_catalog_14.py tools/workspace-router/tests/test_project_load.py -q
```

Test surfaces: `load_catalog`, `load_index`, catálogo de 14 skills. Files: `tools/skill-index/load.py`, [tools/workspace-router/run.py](../tools/workspace-router/run.py), [tools/skill-router/route.py](../tools/skill-router/route.py). Dependencies: T1.

**T5: Shim sin segundo importlib.** Tamaño S. Rol: `role-back`.

Descripción: [tools/skill-router/build_index.py](../tools/skill-router/build_index.py) importa `build_index` y `main` desde el módulo cargado por `load.py` (o desde `generate` vía ese cargador). El fichero sigue siendo el CLI de [.machineroom/SPEC.md](../.machineroom/SPEC.md). No aparece un segundo `spec_from_file_location` hacia `generate.py`.

Acceptance:

- `python3 tools/skill-router/build_index.py` sigue delegando en `generate.main`.
- El fichero no abre `generate.py` por su cuenta con `importlib`.

Verify: el mismo pytest de T4, más `python3 tools/skill-router/build_index.py --help` (o la invocación sin argumentos que ya usa el módulo, si `--help` no existe: leer `main` y usar el flag de comprobación que `generate.py` ya acepte). `rg -n "spec_from_file_location" tools/skill-router/build_index.py` vacío.

Test surfaces: CLI del shim y `build_index` del generador. Files: [tools/skill-router/build_index.py](../tools/skill-router/build_index.py), `tools/skill-index/load.py` si el shim necesita una función pública. Dependencies: T4.

### Checkpoint: Índice

- Pytest de T4 sale 0.
- Los dos routers comparten cargador.

### Fase 3 — Errores

**T6: Quitar el alias NON_TERMINAL de execution.** Tamaño S. Rol: `role-back`.

Descripción: [tools/execution/evidence.py](../tools/execution/evidence.py) importa `PHASE_BLOCKING_OUTCOMES` y sustituye los dos usos de `NON_TERMINAL` (aprox. líneas 390 y 540). Se borra el alias en [tools/execution/ops.py](../tools/execution/ops.py) líneas 53–56. [tools/contracts/result.py](../tools/contracts/result.py) no se toca: su `NON_TERMINAL` sigue siendo `awaiting_agent` y `awaiting_approval`.

Acceptance:

- `rg -n "NON_TERMINAL" tools/execution` no devuelve coincidencias.
- Un outcome `blocked` o `simulated` sigue sin poder completar fase, igual que antes del alias.

Verify:

```bash
uv run --project tools --frozen pytest tools/execution/tests/test_product_closure_evidence.py tools/execution/tests/test_verifiable_closure.py tools/contracts/tests/test_plan.py -q
```

Test surfaces: `evidence` frente a outcomes de fase; esquema D03 intacto. Files: [tools/execution/ops.py](../tools/execution/ops.py), [tools/execution/evidence.py](../tools/execution/evidence.py). Dependencies: ninguna.

**T7: Base StructuredFailure.** Tamaño M. Rol: `role-back`.

Descripción: Nuevo `tools/structured_failure.py` con `StructuredFailure(ValueError)` (`component`, `function`, `detail`, `to_dict()`). Heredan sin cambiar el texto de `str()`: `StateDirError`, `DenyListError`, `ModelScopeError`, `ContractError`, `InstallFailure`.

Acceptance:

- Las cinco clases exponen `to_dict()` con esas tres claves.
- El mensaje `FAIL {component} {function}: {detail}` de `StateDirError` se conserva.

Verify:

```bash
uv run --project tools --frozen pytest tools/execution/tests/test_deny_list.py tools/harness/tests/test_model_scope.py tools/harness/tests/test_install_failures.py tools/contracts/tests/test_loader.py tools/workspace-router/tests/test_legacy_state_migration.py -q
```

Test surfaces: construcción y `to_dict` de cada error; migración legacy aún en su comportamiento actual (el corte es T8). Files: `tools/structured_failure.py`, [tools/state_paths.py](../tools/state_paths.py), [tools/execution/deny_list.py](../tools/execution/deny_list.py), [tools/harness/model_scope.py](../tools/harness/model_scope.py), [tools/contracts/loader.py](../tools/contracts/loader.py), [tools/harness/runtime.py](../tools/harness/runtime.py). Dependencies: T6.

### Checkpoint: Errores

- Pytest de T6 y T7 salen 0.
- `contracts.result.NON_TERMINAL` sigue en su módulo.

### Fase 4 — Estado legacy

**T8: state_dir deja de resolver el fallback.** Tamaño M. Rol: `role-back`.

Descripción: Si el repo solo tiene `.autoworkspace`, `state_dir` lanza `StateDirError` cuyo `detail` contiene `migrate_state`. `migrate_state` (incluido `dry_run=True`) sigue moviendo o informando sin borrar en el fallo. Actualizar el docstring de [tools/workspace-router/project_load.py](../tools/workspace-router/project_load.py), que hoy habla de un fallback `.machineroom`. `REMOVAL_VERSION` pasa a `9.2.0` y el mensaje cita el anuncio 9.0.0. Reescribir [tools/workspace-router/tests/test_legacy_state_migration.py](../tools/workspace-router/tests/test_legacy_state_migration.py) a la expectativa nueva.

Acceptance:

- Un tmp solo con `.autoworkspace` no obtiene esa ruta como estado.
- `migrate_state(..., dry_run=True)` no borra el directorio legacy.
- Dos directorios a la vez siguen siendo error, como ahora.

Verify:

```bash
uv run --project tools --frozen pytest tools/workspace-router/tests/test_legacy_state_migration.py tools/workspace-router/tests/test_project_load.py -q
```

Test surfaces: `state_dir`, `migrate_state`, carga de `project.yaml`. Files: [tools/state_paths.py](../tools/state_paths.py), [tools/workspace-router/project_load.py](../tools/workspace-router/project_load.py), [tools/workspace-router/tests/test_legacy_state_migration.py](../tools/workspace-router/tests/test_legacy_state_migration.py). Dependencies: T7.

**T9: Dirname solo en naming.py.** Tamaño S. Rol: `role-back`.

Descripción: [tools/state_paths.py](../tools/state_paths.py) importa `PROJECT_DIRNAME` y `LEGACY_PROJECT_DIRNAME` desde `harness.naming` y no los reasigna. [tools/harness/tests/test_naming.py](../tools/harness/tests/test_naming.py) sigue exigiendo que `autoworkspace` en `naming.py` viva solo en líneas `LEGACY_*`.

Acceptance:

- Una búsqueda de `PROJECT_DIRNAME =` en `tools/` encuentra la asignación en `naming.py` y no en `state_paths.py`.
- El test de literales legacy de naming sigue en verde.

Verify:

```bash
uv run --project tools --frozen pytest tools/harness/tests/test_naming.py tools/workspace-router/tests/test_legacy_state_migration.py -q
```

Test surfaces: constantes de naming y `state_dir`. Files: [tools/state_paths.py](../tools/state_paths.py), [tools/harness/naming.py](../tools/harness/naming.py) solo si hace falta un reexport mínimo. Dependencies: T8.

**T10: Doctor avisa el runtime de hogar.** Tamaño M. Rol: `role-back`.

Descripción: Si el home bajo prueba tiene `~/.autoworkspace` y no tiene `~/.machineroom`, la salida JSON de [tools/harness/doctor.py](../tools/harness/doctor.py) incluye un fallo cuyo detalle nombra `migrate_legacy_runtime`. Doctor no llama a esa función. El test usa `tmp_path`, nunca el hogar real.

Acceptance:

- Home temporal solo legacy → estado `fail` y el nombre de la función en el detalle.
- Home temporal ya migrado → esa comprobación no falla.
- El directorio legacy del tmp sigue en su sitio tras el doctor.

Verify:

```bash
uv run --project tools --frozen pytest tools/harness/tests/test_doctor.py tools/harness/tests/test_runtime_migration.py -q
```

Checkpoint de fase: `make validate`.

Test surfaces: doctor JSON y `migrate_legacy_runtime` existente, sin invocarlo desde doctor. Files: [tools/harness/doctor.py](../tools/harness/doctor.py), [tools/harness/tests/test_doctor.py](../tools/harness/tests/test_doctor.py). Dependencies: T9.

### Checkpoint: Estado legacy

- Pytest de T8–T10 salen 0.
- `make validate` sale 0.
- Ningún test usa el `HOME` real del operador.

### Fase 5 — Partir status_bump

**T11: Extraer el ciclo plan/tarea.** Tamaño M. Roles: `role-clean-code` y `role-back` (el YAML es persistencia del pipeline).

Descripción: Mover a `tools/workspace-router/task_lifecycle.py` las funciones públicas `activate_plan`, `load_active_plan`, `ready_tasks`, `start_task`, `await_task`, `complete_task`, `fail_task`, `block_task`, `cancel_task`, `retry_task` y los helpers privados que solo ellas usan. Importan I/O desde `status_bump` (`load_status`, lock, escritura). `status_bump.py` las reexporta. No cambia el texto YAML ni las firmas.

Acceptance:

- `from status_bump import complete_task, activate_plan` sigue funcionando en los tests actuales.
- Un complete de tarea de prueba escribe las mismas claves que antes del movimiento.

Verify:

```bash
uv run --project tools --frozen pytest tools/workspace-router/tests/test_task_lifecycle.py tools/workspace-router/tests/test_plan_state.py tools/orchestrator/tests/test_scheduler.py -q
```

Test surfaces: `complete_task`, `start_task`, `activate_plan`, scheduler. Files: `tools/workspace-router/task_lifecycle.py`, [tools/workspace-router/status_bump.py](../tools/workspace-router/status_bump.py). Dependencies: T10.

**T12: Extraer el avance de fase.** Tamaño M. Roles: `role-clean-code` y `role-back`.

Descripción: Mover a `tools/workspace-router/phase_advance.py` `advance_status`, `resolve_awaiting_agent`, `bump_kind_for_phase` y los helpers privados que solo sirven al avance (`_AdvanceContext` y la cadena `_advance_*` / `_validated_evidence`). Reexport desde `status_bump.py`. El rechazo de `--bump` en [tools/workspace-router/run.py](../tools/workspace-router/run.py) no se toca. Tras el corte, `status_bump.py` conserva carga, lock, escritura atómica y reexports.

Acceptance:

- La firma keyword-only de `advance_status` y `resolve_awaiting_agent` es la misma.
- `rg -n "^def advance_status|^def complete_task" tools/workspace-router/status_bump.py` no encuentra definición local (sí puede haber import de reexport).
- `status_bump.py` queda por debajo de 400 líneas.

Verify:

```bash
uv run --project tools --frozen pytest tools/workspace-router/tests/test_status_bump.py tools/workspace-router/tests/test_task_lifecycle.py tools/orchestrator/tests/test_scheduler.py tools/workspace-router/tests/test_plan_state.py -q
```

Test surfaces: `advance_status`, `resolve_awaiting_agent`, ciclo de tarea ya extraído. Files: `tools/workspace-router/phase_advance.py`, [tools/workspace-router/status_bump.py](../tools/workspace-router/status_bump.py). Dependencies: T11.

### Checkpoint: status_bump

- Pytest de T12 sale 0.
- El diff de T11 y T12 no incluye `state_paths.py` ni `doctor.py`.

### Fase 6 — Bootstrap de imports

**T13: Módulo tools/\_bootstrap.py.** Tamaño XS. Rol: `role-back`.

Descripción: `ensure_tools_on_path()` inserta la raíz `tools/` una vez. Idempotente si la ruta ya está. Sin dependencia nueva.

Acceptance: llamarla dos veces no duplica la entrada. Verify: test nuevo `tools/tests/test_bootstrap.py` o, si no hay paquete `tools/tests`, `tools/harness/tests/test_bootstrap.py` con un nombre que no choque con el bootstrap de harness ya existente; el fichero de test se elige para no pisar [tools/harness/tests/test_bootstrap.py](../tools/harness/tests/test_bootstrap.py). Preferir `tools/skill-index/tests/test_load.py` solo si T4 ya creó ese directorio; si no, `tools/workspace-router/tests/test_import_bootstrap.py`.

Test surfaces: `ensure_tools_on_path`. Files: `tools/_bootstrap.py`, el test nuevo. Dependencies: T12.

**T14: Routers y orchestrator.** Tamaño M. Rol: `role-back`.

Descripción: Sustituir los `sys.path.insert` de producción en [tools/workspace-router/run.py](../tools/workspace-router/run.py), [tools/workspace-router/project_load.py](../tools/workspace-router/project_load.py), [tools/workspace-router/status_bump.py](../tools/workspace-router/status_bump.py) (incluidas las inserciones internas hacia `tools/`), [tools/orchestrator/run.py](../tools/orchestrator/run.py), [tools/orchestrator/scheduler.py](../tools/orchestrator/scheduler.py) y el shim [tools/skill-router/build_index.py](../tools/skill-router/build_index.py) si aún inserta ruta. Los tests de esos paquetes no se editan.

Acceptance: `rg -n "sys\\.path\\.insert" ` sobre esos seis ficheros no devuelve coincidencias. Los pytest de routers y scheduler siguen en 0.

Verify:

```bash
uv run --project tools --frozen pytest tools/workspace-router/tests tools/orchestrator/tests tools/skill-router/tests -q
```

Test surfaces: CLI de fase, scheduler, ruta de intención. Files: los seis citados y `tools/_bootstrap.py`. Dependencies: T13.

**T15: Harness.** Tamaño M. Rol: `role-back`.

Descripción: Igual en [tools/harness/doctor.py](../tools/harness/doctor.py), [tools/harness/cursor.py](../tools/harness/cursor.py), [tools/harness/pi.py](../tools/harness/pi.py), [tools/harness/cursor_install.py](../tools/harness/cursor_install.py). No cambiar la cadena que `cursor.py` escribe dentro de un fichero generado para otra sesión (el `sys.path.insert` que aparece en una f-string de plantilla no es el import del proceso actual: se queda).

Acceptance: los cuatro módulos no insertan `sys.path` para importar el repo. La plantilla emitida por `cursor.py` conserva su insert. Verify:

```bash
uv run --project tools --frozen pytest tools/harness/tests/test_doctor.py tools/harness/tests/test_cursor_install.py tools/harness/tests/test_pi.py tools/harness/tests/test_runtime.py -q
```

Test surfaces: doctor, install de Cursor, adaptador Pi. Files: los cuatro módulos. Dependencies: T14.

**T16: Validate y contracts.** Tamaño M. Rol: `role-back`.

Descripción: Igual en [tools/validate/skill_spec.py](../tools/validate/skill_spec.py), [tools/contracts/validate_contracts.py](../tools/contracts/validate_contracts.py) y el insert de [tools/contracts/loader.py](../tools/contracts/loader.py). Después, `rg -n "sys\\.path\\.insert" tools --glob '!**/tests/**'` solo puede coincidir con la f-string de plantilla en `cursor.py` y con `tools/_bootstrap.py`.

Acceptance: esa búsqueda no muestra otro entry point de producción. Checkpoint final debajo.

Verify:

```bash
uv run --project tools --frozen pytest tools/validate/tests/test_skill_spec.py tools/contracts/tests/test_loader.py -q
```

Test surfaces: `skill_spec` y carga del registry. Files: los tres módulos. Dependencies: T15.

### Checkpoint: Cierre

- `make validate` sale 0.
- `npm run typecheck` sale 0.
- La búsqueda de T16 cumple su acceptance.
- No hay PASS declarado sobre un paso `skip`, `not_run` o con dependencia ausente.

## Qué no entra en la ejecución de este documento

La copia a `tasks/plan-9.2.0-control-plane-cohesion.md` es el primer gesto de la ejecución, después de un pedido explícito de implementar. Hasta entonces este archivo es la spec.
