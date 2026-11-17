---
version: "1.0.0"
date: "2026-11-17"
status: "Proposed"
adr_id: "ADR-0020"
priority: "P1"
---

# ADR-0020: Plugin de Herdr como superficie opcional (aparcado)

**Fecha:** 2026-11-17
**Estado:** Proposed (no adoptado; trabajo conservado en rama y PR draft)
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Registrar qué pretendía el plugin de [Herdr](https://herdr.dev) para machineroom, qué aporta, qué cuesta y bajo qué condiciones se retomaría. Deja el trabajo conservado, no borrado, y fuera de `main` hasta que se decida.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Objetivos, Potencial, Costes, Condiciones para retomarlo, Consecuencias, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** Es una decisión del producto machineroom. Un repo de producto que quiera la misma superficie puede adoptarla por su cuenta con su propio ADR; no se copia.

## Contexto

Herdr es un workspace de terminal con sistema de plugins: manifiesto declarativo
(`actions`, `panes`), atajos y paneles interactivos. Su modelo encaja con
machineroom porque el pipeline ya expone todo lo necesario por CLI y por
artefactos: `skill-index.json`, `tools/skill-router`, `tools/workspace-router`,
`tools/harness/doctor.py` y `make validate`.

Se escribió un plugin (`herdr/herdr-plugin.toml` + `herdr/bin/mmctl.py`) que
envuelve exactamente esas herramientas. El PR #72 quedó sin mergear: estaba
construido sobre el catálogo de 17–18 skills y su CI no volvió a ejecutarse tras
la reestructuración 9.0.0, además de que el repo se organiza con reglas
estrictas sobre qué árboles son canónicos.

## Decisión

1. **No adoptar Herdr ahora.** `main` no contiene `herdr/` ni el paso `[10]` de
   `run-validation.sh`.
2. **No borrar el trabajo.** El plugin se mantiene actualizado al catálogo vivo
   (14 skills, lectura derivada de `skill-index.json`) en la rama
   `feat/herdr-plugin-14` y en su PR draft.
3. **Documentar objetivos, potencial y costes** en este ADR y en
   `docs/herdr-plugin.md`, para que la decisión se pueda retomar con contexto y
   no se reabra desde cero.
4. **Reevaluar** cuando se cumplan las condiciones de la sección siguiente. La
   adopción exigirá pasar este ADR a `Accepted` y mergear el contenido
   actualizado, no resucitar el PR #72.

## Objetivos del plugin

- **Hacer visible el catálogo** sin abrir ficheros: skills por dominio, con tipo
  y propósito, leídos de `skill-index.json` (nunca una lista mantenida a mano).
- **Enrutar desde el texto seleccionado**: `route` pasa la selección por
  `tools/skill-router/route.py --top 3` y propone candidatas.
- **Navegar el pipeline**: `phase` ofrece DEFINE→…→STATUS y delega en
  `tools/workspace-router/run.py`.
- **Ver estado sin salir del editor de terminal**: `status`/`dashboard` muestran
  git, fase declarada y contenido de `.machineroom/`.
- **Ejecutar el gate a un atajo**: `validate` lanza `make validate` (o
  `run-validation.sh`) en un panel dividido.
- **Diagnosticar harnesses**: `doctor` combina `tools/harness/doctor.py` con el
  estado de los enlaces de skills en Pi y Cursor.

Principio de diseño que sí merece conservarse: **el puente no reimplementa
nada**. `mmctl.py` solo conduce herramientas existentes; si una capacidad no está
en `tools/`, el panel no la inventa.

## Potencial

- **Adopción sin fricción**: el plugin se enlaza en local (`herdr plugin link`),
  no requiere publicación ni instalación desde GitHub, y `unlink` lo retira sin
  dejar residuos.
- **Una sola fuente**: al derivar catálogo y fases de artefactos reales, el panel
  no puede contradecir al router.
- **Bajo coste de mantenimiento** si se respeta esa premisa: sin lógica de
  dominio propia, el trabajo se reduce a ajustar el manifiesto cuando cambie el
  número de acciones o paneles.
- **Reutilizable por otras flotas**: el patrón (manifiesto + puente que invoca el
  CLI del repo) sirve para cualquier producto con router y gate propios.

## Costes y riesgos

| Riesgo                      | Detalle                                                                   | Mitigación                                                              |
| --------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Dependencia de terceros     | El catálogo pasaría a recomendar Herdr ≥ 0.9.5 para una función cosmética | Declararlo **opcional**: nada del pipeline depende de él                |
| Duplicación de conocimiento | `mmctl.py` codifica fases, comandos y layout del checkout                 | Derivar de artefactos; sin listas propias; paso `[10]` que lo comprueba |
| Cuarto árbol de artefactos  | `skills/` es el único catálogo versionado; `herdr/` no es skill ni tool   | ADR explícito + exclusión del contrato de producto                      |
| Deriva silenciosa           | Ya ocurrió: «18 skills», snapshot 8.0.0, pytest con `tools/email/`        | Validación en el gate: manifiesto ↔ paneles ↔ `skill-index.json`        |
| Alcance de soporte          | 377 líneas de TUI + README mantenidos en el repo canónico                 | Solo se adopta si se acepta ese coste de soporte                        |

## Condiciones para retomarlo

1. El catálogo y el pipeline están estables (sin reestructuraciones abiertas).
2. El plugin deriva todo de artefactos: cero números de skills, cero listas de
   fases escritas a mano.
3. El paso de validación del plugin no bloquea `ci-gate` si Herdr no está
   instalado: se ejecuta la comprobación estática del manifiesto y el render del
   panel, sin requerir el binario.
4. Este ADR pasa a `Accepted` con la decisión explícita del operador.
5. Se documenta en `ARCHITECTURE.md` como superficie opcional, fuera del contrato
   de flota.

## Consecuencias

- El repo canónico sigue con 14 skills y tres superficies de uso (Pi, Cursor y
  CLI); Herdr no entra en el contrato.
- El trabajo no se pierde: está actualizado y verificado en un PR draft, listo
  para mergear si se cumplen las condiciones.
- Cualquiera que pregunte «¿y el plugin de Herdr?» tiene una respuesta escrita en
  lugar de una rama huérfana.

## Alternativas consideradas

- **Mergear ya y arreglar después.** Rechazada: mete una dependencia de terceros
  y un cuarto árbol en el repo canónico sin decisión registrada.
- **Borrar el trabajo.** Rechazada: se pierde una integración verificada y se
  vuelve a empezar si el interés reaparece.
- **Mantenerlo en un repo aparte desde el inicio.** Viable y probablemente el
  destino final si se adopta; hoy no hay consumidor más allá del operador, y el
  coste de un repo extra supera el de una rama con PR draft.

## Relacionados

- `docs/herdr-plugin.md` — objetivos, superficie y cómo probarlo sin mergear.
- PR #72 (cerrado) y PR #84 (draft, contenido actualizado al catálogo de 14).
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) — árbol del producto.
- [ADR-0018](ADR-0018-rename-a-machineroom.md) — contrato de nombres y superficies.
