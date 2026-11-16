# Decisiones abiertas — repertorio de skills

> Incremento: mejora del repertorio (coherencia, fluidez, referencias, eficacia).
> Plan canónico: [`tasks/plan-skills-repertoire-improvement.md`](plan-skills-repertoire-improvement.md).
> Cada decisión: contexto verificado en el repo, opciones, recomendación y coste.
> Estado de partida: catálogo en **16 skills** tras retirar `local-email`.

## Resumen ejecutivo

| #   | Decisión                                         | Recomendación                                                  | Esfuerzo             |
| --- | ------------------------------------------------ | -------------------------------------------------------------- | -------------------- |
| D1  | Frontera `plan-continue` / `project-machineroom` | Partir en `plan-router` + `project-audit`                      | 1 tarea              |
| D2  | Tipo de `project-libraries` y `project-publish`  | `project-libraries`→`atomic`; `project-publish`→`orchestrator` | Trivial              |
| D3  | Estrictez del validador                          | Tres niveles: error / warn / info                              | 1 tarea              |
| D4  | Tamaño del catálogo                              | Congelar en 16 hasta cerrar la normalización                   | Decisión de política |
| D5  | `metadata.keywords` y `triggers`                 | Keywords = lista corta; triggers viven en `intent-map.yaml`    | 1 tarea              |
| D6  | Nombres y prefijos de dominio                    | Mantener prefijo = dominio, sin excepciones                    | Sin coste            |
| D7  | `disable-model-invocation`                       | Sólo en skills que mutan o publican                            | Trivial              |
| D8  | Versionado tras el recorte                       | `8.1.0` con bump por skill tocada                              | Trivial              |

---

## D1 — Frontera `plan-continue` vs `project-machineroom`

**Contexto verificado.** `plan-continue` declara hoy: «continue from roadmap or
`.machineroom` status; when missing, audit the repo, scaffold project.yaml/status.yaml,
and route DEFINE→…→STATUS». `project-machineroom` declara: «audit and improve the
machineroom system itself». Ambos se declaran `type: orchestrator`. El solape real es
la auditoría del repo: `plan-continue` la hace para arrancar un plan y
`project-machineroom` la hace para auditarse a sí mismo.

**Opciones**

| Opción                             | Qué hace                                                                                                             | Ventaja                                                       | Inconveniente                                                                          |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **A. Sólo documentar la frontera** | Reescribir ambas descripciones y añadir `→` cruzados; ningún cambio estructural                                      | Coste mínimo; no toca router ni tests                         | El nombre `plan-continue` sigue prometiendo auditoría de repo que su cuerpo no detalla |
| **B. Partir en tres**              | `plan-router` (fase pura), `project-audit` (auditoría de repo + status board), `project-machineroom` (autoauditoría) | Cada skill = una capacidad; `type` honesto; router más simple | Nuevo skill = bump de taxonomía, `intent-map.yaml`, instaladores y tests de catálogo   |
| **C. Fusionar**                    | Un solo `plan-continue` que absorbe `project-machineroom`                                                            | Menos skills                                                  | Mezcla autoauditoría con trabajo de producto; el self-change protocol queda escondido  |

**Recomendación: B, en una sola tarea.** La auditoría de repo ya existe en
`scripts/scan_repo.py`, `scripts/audit-repo.sh` e `inicio_plan.py`; separarla da un
`plan-router` con `type: router` real (no ejecuta lógica de dominio) y un
`project-audit` con `type: audit`. Si el coste de mantener tres skills molesta,
**A es el siguiente mejor**, porque no rompe el runtime del workspace.

Coste de B: `intent-map.yaml` (2 entradas), `registry.yaml` (tool_id nuevo),
`test_catalog_16.py` (constantes), `docs/TAXONOMY.md` + `AGENTS.md`.

---

## D2 — Tipo declarado que no coincide con el comportamiento

**Contexto verificado.** `project-libraries` está marcado `audit` pero ejecuta un
pipeline multi-lenguaje que instala y corre escáneres: no es lectura pura.
`project-publish` está marcado `atomic` pero orquesta gates locales, CI, versión, PR
y merge-watch. `project-machineroom` está marcado `orchestrator` pero sólo audita.

**Opciones**

| Opción                           | Qué hace                                                                                      |
| -------------------------------- | --------------------------------------------------------------------------------------------- |
| **A. Reclasificar al tipo real** | `project-libraries`→`atomic`; `project-publish`→`orchestrator`; `project-machineroom`→`audit` |
| **B. Mantener y añadir matiz**   | Dejar el tipo y explicar en `## Overview` que el skill «audita ejecutando»                    |
| **C. Ampliar el enum**           | Añadir `pipeline` al conjunto cerrado de `docs/TAXONOMY.md`                                   |

**Recomendación: A, con una corrección.** El tipo es contrato normativo
(`docs/TAXONOMY.md`, «closed set») y gobierna el techo de `allowed-tools` por ADR-0017,
así que el cambio arrastra `allowed-tools`:

- `project-libraries` → `atomic` **y `+Bash`**: como `audit` no puede ejecutar el
  pipeline SCA que anuncia.
- `project-publish` → `orchestrator` (sin cambio de herramientas).
- `project-machineroom` → **se queda `orchestrator`**: `plan_self_change` escribe un
  spec y `self_audit` corre `doctor.py` con Bash; `audit` (Read/Grep/Glob) se lo
  impediría.

Detalle por skill en [`decisions-d1-d2-table.md`](decisions-d1-d2-table.md).

---

## D3 — Estrictez del validador

**Contexto verificado.** `tools/validate/skill_spec.py` hoy valida frontmatter, dominio
y presencia de `## Overview` / `## When to Use`. No valida plantilla de `description`,
ni arreglos de `keywords`, ni que los `→ skill` existan (eso lo hace `skill_links.py`
para enlaces Markdown, no para flechas en prosa ni en frontmatter).

**Opciones**

| Opción              | Regla                                                                                                                             | Riesgo                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **A. Todo error**   | Cualquier desviación rompe CI                                                                                                     | Frena PRs legítimos; falso positivo en descripciones con matices |
| **B. Tres niveles** | `error` (name/domain/type/links/size), `warn` (plantilla de description, keywords como lista), `info` (metadata opcional ausente) | Ninguno relevante                                                |
| **C. Sólo informe** | El validador imprime y nunca falla                                                                                                | No protege nada a medio plazo                                    |

**Recomendación: B, empezando por `error` sólo en lo ya violado.** Concretamente:
flecha `→` a skill inexistente = error; `description` sin `Use when` = warn (ya lo es);
`keywords` no-lista = warn; `≤500` líneas / `≤5000` tokens = error. Los `warn` se
listan en el resumen del gate sin bloquear, y se suben a `error` en un segundo
incremento cuando el catálogo esté limpio.

---

## D4 — Tamaño objetivo del catálogo

**Contexto verificado.** El histórico osciló entre 16 y 17 skills; el plan propone
huecos (`local-network`, `project-dependencies`, `role-api`, `role-data`,
`web-api-security`, `project-licenses`, `local-containers`). Cada skill nueva cuesta:
`SKILL.md` + `references/` + entrada en `intent-map.yaml` + tool en `registry.yaml` +
una línea en la matriz de instalación + tests de catálogo.

**Opciones**

| Opción                                                         | Qué implica                                                   |
| -------------------------------------------------------------- | ------------------------------------------------------------- |
| **A. Congelar en 16** hasta cerrar normalización y referencias | El `type` y la frontera de D1 quedan estables antes de crecer |
| **B. Crecer a 23 ya** con los huecos propuestos                | Cobertura inmediata                                           |
| **C. Sin objetivo**                                            | Crecer por demanda puntual                                    |

**Recomendación: A.** El cuello de botella hoy no es cobertura, es coherencia: cinco
skills sin `references/`, `metadata.author` inconsistente y flechas `→` incompletas.
Añadir skills antes de arreglar eso multiplica la deuda. Tras cerrar el incremento,
`local-network` y `project-dependencies` son los dos huecos con más valor.

---

## D5 — `metadata.keywords` y `triggers`

**Contexto verificado.** `keywords` es hoy una cadena con el propio nombre
(`keywords: local-maintenance`), es decir, información nula. Los disparadores reales
están en `tools/skill-router/intent-map.yaml` (`patterns:`), y
`tools/skill-index/generate.py` los inyecta en el índice como `triggers`. Hay por
tanto dos fuentes para lo mismo.

**Opciones**

| Opción                                                            | Qué hace                                                                           |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **A. Keywords = lista corta; triggers sólo en `intent-map.yaml`** | `keywords: [maintenance, linux, cleanup, health-score]`; el ruteo sigue en el YAML |
| **B. Duplicar triggers en frontmatter**                           | `keywords` con todos los patrones                                                  |
| **C. Eliminar `keywords`**                                        | Sólo `intent-map.yaml`                                                             |

**Recomendación: A.** Una lista de 3–5 términos legibles describe el skill para un
humano; los patrones de ruteo son datos de máquina y se quedan en un solo sitio.
C dejaría el frontmatter sin señal semántica para lectores y para el índice.
B duplica y garantiza divergencia.

---

## D6 — Nombres y prefijos de dominio

**Contexto verificado.** `docs/TAXONOMY.md` es normativo: «the name prefix IS the
domain». Los 16 nombres actuales cumplen. `local-email` era el único con nombre de
proveedor disfrazado de dominio (`local` + `email`), y ya está retirado.

**Opciones**

| Opción                                   | Qué hace                                           |
| ---------------------------------------- | -------------------------------------------------- |
| **A. Mantener la regla sin excepciones** | Cualquier skill futura se llama `<dominio>-<slug>` |
| **B. Permitir alias por proveedor**      | `local-proton`, `local-gmail`                      |
| **C. Renombrar dominios**                | `host` en vez de `local`, etc.                     |

**Recomendación: A.** El prefijo es lo que hace el ruteo predecible y lo que el
validador puede comprobar. Los proveedores van dentro del cuerpo o de `references/`.

---

## D7 — `disable-model-invocation`

**Contexto verificado.** Lo tienen `local-maintenance`, `local-security` y
`project-publish`. Ninguna `role-*` ni `plan-*` lo tiene. La semántica es: el modelo no
invoca el skill por su cuenta; requiere orden explícita.

**Opciones**

| Opción                                            | Qué hace                                          |
| ------------------------------------------------- | ------------------------------------------------- |
| **A. Criterio: muta host, muta remoto o publica** | Sólo `local-*`, `project-publish` (estado actual) |
| **B. Añadirlo a `project-machineroom`**           | Autoauditoría tampoco se autodispara              |
| **C. Quitarlo de todas**                          | Todo invocable por modelo                         |

**Recomendación: A, más B.** Es barato y coherente: un skill que puede tocar el host,
el remoto o publicar no debe dispararse por coincidencia semántica. `plan-*` y `role-*`
son de lectura/edición de código y deben seguir siendo invocables por el modelo.

---

## D8 — Versionado tras el recorte

**Contexto verificado.** `package.json` está en `8.0.1`; `scopes` de skills en 7.1.x
salvo `local-maintenance` (8.0.0) y `project-publish` (8.0.0). `docs/STANDARD.md`
exige bump en PR que toque una skill (`tools/version/bump.py --check --auto`). Retirar
`local-email` no requiere bump de ninguna skill superviviente, pero sí entrada de
changelog.

**Opciones**

| Opción                                       | Qué hace                                                                        |
| -------------------------------------------- | ------------------------------------------------------------------------------- |
| **A. 8.1.0 con bump sólo de skills tocadas** | `minor` para las que ganan referencias/capacidad, `patch` para las de metadatos |
| **B. 9.0.0 por el recorte de catálogo**      | Trata la retirada como breaking                                                 |
| **C. Dejar versiones**                       | Sólo changelog                                                                  |

**Recomendación: A.** Una skill retirada no rompe a los consumidores del catálogo
(el índice se regenera), así que no hay breaking real. `8.1.0` con entradas `Added` /
`Changed` / `Removed` describe el incremento con precisión.

**Estado verificado del gate.** `tools/version/cut_tag.py` incluye `CHANGELOG.md` en
`RELEASE_PATHS`: cualquier PR que toque el changelog exige `package.json` por delante
del último tag (`check-bump`). Por eso la retirada se integró **sin** entrada de
changelog y la nota `Removed` viaja con el PR de release (TASK-028b). Publicar `8.1.0`
es una autorización aparte: mergear la retirada no corta tag.

---

## Siguiente paso

Si aceptas las recomendaciones (D1-B, D2-A, D3-B, D4-A, D5-A, D6-A, D7-A+B, D8-A),
el orden de ejecución es el de `tasks/plan-skills-repertoire-improvement.md`
§2.1, con D1 y D2 en la misma tanda por compartir tests de catálogo.
