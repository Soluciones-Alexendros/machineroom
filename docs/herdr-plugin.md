# Plugin de Herdr — superficie opcional (no adoptada)

### Propósito de este documento

- **Objetivos:** Explicar qué es el plugin de [Herdr](https://herdr.dev) para machineroom, qué expone, qué aporta y dónde vive hoy. Es la referencia que se consulta antes de proponerlo de nuevo.
- **Estructura:** Esta meta-sección → qué es → superficie → estado → cómo probarlo → límites.
- **Contenido a integrar según contexto:** Si un producto quiere una superficie equivalente, usa el patrón (manifiesto + puente que invoca el CLI del repo) y su propio ADR; no copia este plugin.

## Qué es

Herdr es un workspace de terminal con plugins declarativos: un manifiesto con
**acciones** (se invocan desde menú, selección o atajo) y **paneles** (la
superficie donde se renderiza el resultado). El plugin de machineroom es un
envoltorio: **no reimplementa nada**, conduce las herramientas que ya existen.

## Superficie

| Acción      | Contexto  | Qué muestra                                             | Herramienta que invoca                |
| ----------- | --------- | ------------------------------------------------------- | ------------------------------------- |
| `dashboard` | workspace | git, fase declarada y accesos rápidos                   | `.machineroom/`                       |
| `skills`    | workspace | catálogo por dominio, con tipo y propósito              | `skill-index.json`                    |
| `route`     | selection | top-3 skills para el texto seleccionado                 | `tools/skill-router/route.py`         |
| `status`    | workspace | git, fase, contenido de `.machineroom/`                 | —                                     |
| `phase`     | workspace | menú DEFINE→SCHEMAS→IMPLEMENT→VALIDATE→INTEGRATE→STATUS | `tools/workspace-router/run.py`       |
| `validate`  | workspace | gate completo en panel dividido                         | `make validate` / `run-validation.sh` |
| `doctor`    | global    | doctores + enlaces de skills en Pi y Cursor             | `tools/harness/doctor.py`             |

Paneles: `dashboard`, `skills`, `route`, `status`, `phase`, `doctor` (overlay) y
`validate` (split). El puente es `herdr/bin/mmctl.py` (Python stdlib, sin
dependencias) y busca el checkout por `skill-index.json` + `skills/`, así que
sirve al árbol de desarrollo, no al runtime `~/.machineroom`.

## Estado

**No adoptado.** La decisión y su racionalidad están en
[ADR-0020](architecture/decisions/ADR-0020-plugin-herdr-opcional.md) (estado
`Proposed`):

- `main` no contiene `herdr/` ni el paso `[10]` de `run-validation.sh`.
- El trabajo se conserva actualizado al catálogo de 14 skills en la rama
  `feat/herdr-plugin-14` y en un PR draft.
- El PR #72 original quedó cerrado por estar construido sobre el catálogo
  anterior (17–18 skills, snapshot `skill-index-8.0.0.json`, pytest con
  `tools/email/`).

## Cómo probarlo sin mergear

```bash
git fetch origin feat/herdr-plugin-14
git checkout feat/herdr-plugin-14
herdr plugin link "$PWD/herdr"
herdr plugin action list --plugin machineroom
herdr plugin pane open --plugin machineroom --entrypoint skills-pane
herdr plugin unlink machineroom      # lo retira sin tocar ficheros
```

El gate de esa rama comprueba el manifiesto, que cada acción apunte a un panel
existente y que el panel de skills liste todas las entradas de
`skill-index.json`.

## Límites

- No es parte del contrato de producto: ni el pipeline ni `ci-gate` dependen de
  Herdr.
- No sustituye a Pi ni a Cursor; es una tercera superficie de consulta.
- No es un catálogo: `skills/` sigue siendo el único árbol canónico.
- Cualquier número de skills, lista de fases o ruta de herramienta **escrita a
  mano** en el plugin es un defecto: todo se deriva de artefactos.
