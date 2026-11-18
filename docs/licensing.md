# Política de licencias (machineroom)

### Propósito de este documento

- **Objetivos:** Declarar qué licencias SPDX acepta el canon MIT al publicar el SBOM CycloneDX de release, y cómo falla el gate.
- **Estructura:** Alcance → allowlist → denylist → expresiones → `NOASSERTION` → verificación.
- **Contenido a integrar según contexto:** El checker de máquina es [`tools/validate/license_gate.py`](../tools/validate/license_gate.py). La allowlist de ids es [`tools/validate/license_allowlist.txt`](../tools/validate/license_allowlist.txt). El SBOM lo genera Syft en [`.github/workflows/release.yml`](../.github/workflows/release.yml).

## Alcance

El proyecto se publica bajo **MIT**. El gate no sustituye el consejo legal: bloquea en CI y en provenance de release un SPDX **declarado** que la política no acepta.

Fuente de verdad del árbol publicado: el JSON CycloneDX producido por Syft sobre el `git archive` de release (no un venv pip).

## Allowlist

Ids SPDX aceptados, un id por línea (comentarios `#` permitidos):

[`tools/validate/license_allowlist.txt`](../tools/validate/license_allowlist.txt)

El gate lee ese fichero; no parsea este Markdown.

## Denylist (código)

Aunque un id aparezca en la allowlist, el checker lo rechaza si pertenece a estas familias (y variantes SPDX `-only`, `-or-later`, con versión):

- `GPL`
- `AGPL`
- `SSPL`
- `CPAL`

## Expresiones SPDX (v1)

| Forma                            | Resultado                                                                                  |
| -------------------------------- | ------------------------------------------------------------------------------------------ |
| Id o name suelto                 | Debe estar en la allowlist y no ser denylist                                               |
| Solo `OR`                        | Pasa si **algún** disjunto está en allowlist y no es denylist (`MIT OR GPL-3.0-only` pasa) |
| `AND` o `WITH`                   | Pasan solo si **todos** los ids lo hacen                                                   |
| `OR` mezclado con `AND` o `WITH` | Falla                                                                                      |

## Licencias no declaradas

Vacío, `NONE` y `NOASSERTION` **no** son error. Syft puede catalogar Actions o ficheros sin campo `license`; el gate solo juzga SPDX declarado. Un id declarado ausente de la allowlist sí falla.

## Verificación

```bash
python3 tools/validate/license_gate.py \
  --sbom machineroom-${VERSION}.cdx.json \
  --allowlist tools/validate/license_allowlist.txt
```

Exit 0 = OK. Exit 1 = rechazos (stderr nombra componente e id) o entrada ilegible.

## Related

- [`docs/reproducible-builds.md`](reproducible-builds.md) — archive, checksum, attestation, cosign
- [`SECURITY.md`](../SECURITY.md) — canal de vulnerabilidades
