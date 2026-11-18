# Machineroom

### Propósito de este documento

- **Objetivos:** Presentar el pipeline, el catálogo de 14 skills y la instalación en los harnesses.
- **Estructura:** Esta meta-sección → qué es el producto → inicio rápido → skills por dominio → nomenclatura → validación.
- **Contenido a integrar según contexto:** El canon de flota vive en este mismo repo (`docs/architecture/`, `stacks/`, `templates/product/`). Este README presenta el producto y apunta al índice del canon.

**Machineroom** (antes machineroom) es el workspace agéntico de Soluciones-Alexendros (MIT): no es una vitrina de skills, sino un pipeline preprogramado con variables por proyecto — especificación → esquemas/tests → código → validación → integración → status declarativo versionado. También es el **host público del canon de flota** (antes `repo-standard`).

Versión **9.0.2**. 14 skills en 5 dominios (`plan`, `local`, `project`, `web`, `role`). Nombres y contenido de skills en inglés; conversaciones en español.

**Deps:** version-updates vía [Renovate](.github/renovate.json) (Dependabot Alerts de seguridad pueden quedar ON). App Renovate en la org es prerrequisito humano.

## Inicio rápido

Pi, instalación de una release pineada:

```bash
pi install git:github.com/Soluciones-Alexendros/machineroom@v7.1.1
```

Desarrollo del checkout o instalación Cursor de solo skills:

```bash
git clone https://github.com/Soluciones-Alexendros/machineroom.git
bash machineroom/scripts/install-cursor.sh --user
```

## Configuración en Cursor y Pi

Cursor (IDE) y Pi (terminal) son los dos harnesses, ambos en nivel A: la puerta es el symlink, no un binario en CI. El catálogo versionado es solo `skills/`. Cursor versiona hooks, rules y agents bajo `.cursor/`; los symlinks de skills se crean con `install-cursor.sh`.

```bash
git clone https://github.com/Soluciones-Alexendros/machineroom.git
cd machineroom
bash scripts/install-cursor.sh --target .cursor/skills
bash scripts/install-cursor.sh --user
bash scripts/install-pi.sh --target .pi/skills
bash scripts/install-pi.sh --user
bash scripts/install.sh --harness pi --target /tmp/ai-pi --yes --json
bash run-validation.sh
```

Comprueba el enrutado con:

```bash
python tools/skill-router/route.py "limpia mi sistema Arch" --top 3
python tools/workspace-router/run.py --init --repo .   # scaffold once
python tools/workspace-router/run.py --phase DEFINE --repo . --json   # read-only route
```

La ejecución mutadora se declara en `tools/execution/registry.yaml` (schema validado). Las skills enlazan con `metadata.execution: <tool_id>` cuando aplica; las de tipo `audit` no tienen entrada. Mutación solo vía `run_registered` + aprobación. Migraciones del cierre verificable: `docs/verifiable-closure-migrations.md`. Harnesses: `docs/harness-integration.md` (Cursor y Pi, nivel A). [ADR-0017](docs/architecture/decisions/ADR-0017-centralizacion-execution-min-priv.md).

Plantillas de proyecto: `templates/harness/` → copiar a `<repo>/.machineroom/`.

Consulta `docs/harness-integration.md`, `docs/harness-setup.md` y `docs/routing.md`.

## Skills por dominio

14 skills en 5 dominios. La tabla la escribe `tools/skill-index/generate.py` entre los marcadores.

<!-- SKILL-INDEX:START -->

| Skill                  | Domain  | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `local-maintenance`    | local   | Systematic Linux system maintenance with hygiene, updates, optimization and health KPIs. Use when auditing a Linux system, routine review, cleaning packages/caches/logs, orphan pacman/AUR, boot or resource optimization, OS health-check, or periodic maintenance of Arch/EndeavourOS/CachyOS/Debian/RHEL. Not for defensive security hardening or forensics (→ local-security).                                                                                                                                                              |
| `local-security`       | local   | Defensive Linux host security: posture, forensic record management, CVEs, sysctl/SSH hardening, AppArmor/SELinux, auditd and fail2ban. Use when the operator requests system security audit, host hardening or auth log review. Not for application code vulnerabilities (→ web-owasp) nor disk cleanup (→ local-maintenance).                                                                                                                                                                                                                   |
| `plan-specification`   | plan    | Write a structured specification before writing any code, then decompose it into small verifiable tasks with explicit acceptance criteria. Use when starting a project or feature, when requirements are ambiguous, or when the change touches multiple modules. Not for single-line fixes or typo corrections (→ plan-testing for implementation).                                                                                                                                                                                              |
| `plan-testing`         | plan    | Read the project as it stands, then produce and execute a complete integrated-test plan: every route, function, job, component and end-to-end flow covered by real, non-trivial tests with explicit expected behaviour. Use when planning or implementing test coverage, when a feature or bug fix needs proof, or when the suite must be brought to a professional standard. Not for writing the product spec (→ plan-specification), closing and releasing an increment (→ project-status) or production host debugging (→ local-maintenance). |
| `project-architecture` | project | Code architecture verification and analysis. Use when analyzing code structure, dependencies, architectural drift, or refactoring opportunities. Not for security code review (→ web-owasp) nor SCA/CVE dependency audits (→ role-linux); minor implementation without architecture analysis uses role-* skills.                                                                                                                                                                                                                                 |
| `project-machineroom`  | project | Audit and improve the machineroom system itself: canon map, control plane, harnesses, migrations and self-change protocol. Use when self-auditing machineroom, checking harness A/B/C drift, or planning an approved change to the pipeline. Not for generic architecture reviews (→ project-architecture); not for product status, hygiene or release closure (→ project-status).                                                                                                                                                               |
| `project-status`       | project | Product status orchestrator: read development state (branch, plans, uncommitted work, CI), report health and pending work, hygienise branches and uncommitted changes, then close the increment with local gates, versioning, packaging and publication. Use when asking about repo status, where work stands, cleaning up branches before continuing, or closing and releasing an increment. Not for spec authorship (→ plan-specification), test plans (→ plan-testing) or machineroom self-audit (→ project-machineroom).                     |
| `role-back`            | role    | Specialist role for backend application work: data at rest and in motion, routes, deployments, robustness and application security. Includes patterns for cache/KV, queues, rate limiting, object storage and search. Use when implementing APIs, persistence, jobs or server-side integrations. Not for host hardening (→ local-security), OWASP code audit (→ web-owasp), or dependency SCA (→ role-linux).                                                                                                                                    |
| `role-clean-code`      | role    | Implements Clean Code principles to write expressive, maintainable software and refactor existing code safely in any language. Use when the operator asks for clean code, refactoring, meaningful names, smaller functions, fewer code smells, or cleanup of duplicated logic. Not for architecture-only assessments (→ project-architecture), test-suite audits (→ plan-testing), or security reviews (→ web-owasp).                                                                                                                            |
| `role-front`           | role    | Specialist role for frontend application work: UI stability, browser compatibility, state coherence across routes, and clear communication contracts between client and server. Use when implementing or fixing frontend features, client state, routing surfaces or interaction flows. Not for visual direction or design tokens (external Impeccable skill), a11y/SEO audits (→ web-compliance), or performance audits (→ web-performance).                                                                                                    |
| `role-linux`           | role    | Linux application engineering role: app architecture, ABI/glibc compatibility, dependency and supply-chain audits, Debian/Ubuntu and Arch/Omarchy packaging, build, deployment and installation. Use when building, packaging, shipping or auditing a Linux application or its dependencies. Not for host maintenance (→ local-maintenance), host hardening (→ local-security), release closure (→ project-status) or generic architecture review (→ project-architecture).                                                                      |
| `web-compliance`       | web     | Web compliance audit: accessibility (WCAG 2.2 AA / EN 301 549), legal (GDPR, Consent Mode v2, privacy policy, cookies), SEO on-page/off-page/SEM/analytics. PASS/FAIL/N/A matrix, weighted scoring, web compliance verdict POSITIVE/NEGATIVE/PARTIAL and remediation plan RICE. Use when auditing web compliance, dictating web compliance or remediation plan for SEO/accessibility/legal. Not for performance audits (→ web-performance) nor dependency scanning (→ role-linux).                                                               |
| `web-owasp`            | web     | Code security review (OWASP): injection, XSS, authn/authz, cryptography, SSRF, secrets and misconfiguration. Use when performing security review, OWASP or searching for vulnerabilities in this code. Not for dependency CVEs (→ role-linux) nor web compliance (→ web-compliance).                                                                                                                                                                                                                                                             |
| `web-performance`      | web     | Web performance audit: Core Web Vitals (LCP, INP, CLS), Lighthouse 12, TTFB/FCP, rendering (SSR/SSG/ISR/islands), caching HTTP/CDN, load optimization and technical frontend diagnosis. Use when performing performance audit, Lighthouse/CWV, load optimization, stability visual, caching or technical frontend diagnosis. Not for compliance audits (→ web-compliance) nor backend load testing.                                                                                                                                              |

<!-- SKILL-INDEX:END -->

Al iniciar un plan y antes de cada tarea o acción independiente, reevalúa el
alcance e invoca todos los roles aplicables. Las invocaciones anteriores no
cubren acciones posteriores; el trabajo mixto exige contratos y handoffs entre
roles.

## Nomenclatura y frontmatter

- Estructura plana: `skills/<nombre-de-la-skill>/SKILL.md`.
- El campo `name` es idéntico al nombre del directorio: `<dominio>-<slug>` en kebab-case. El prefijo es el dominio (normativo, no orientativo).
- El frontmatter lleva exactamente 6 claves: `name`, `description` (alcance y límites), `license: MIT`, `compatibility: "cursor, pi"`, `allowed-tools` y `metadata` con `author`, `version` (semver), `domain`, `type`, `keywords` y `language: en`. Opcional en metadata: `execution: <tool_id>` (referencia al registry central).
- Conjunto cerrado de tipos: `atomic` (una sola capacidad) · `orchestrator` (flujo de varios pasos) · `router` (deriva a otras skills) · `audit` (evaluación de solo lectura con informe).
- Máximo de `allowed-tools` por tipo (mínimo privilegio; gate en `skill_spec.py`): `audit` → Read, Grep, Glob; `atomic` → Read, Write, Grep, Glob (+ Bash si muta); `orchestrator` → Read, Grep, Glob, Bash, Write; `router` → Read, Glob.

## Añadir una nueva skill

Crea un directorio de primer nivel (estructura plana, sin anidamiento):

```bash
mkdir -p skills/<nombre-de-la-skill>
```

Incluye `SKILL.md` con el frontmatter estándar:

```yaml
---
name: <nombre-de-la-skill>
description: >-
  Qué hace. Use when the operator requests it. Not for other families.
license: MIT
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob"
metadata:
  author: Soluciones-Alexendros
  version: 1.0.0
  domain: plan
  type: audit
  language: en
  keywords: <nombre-de-la-skill>
---
```

Para skills mutadoras, usa el set permitido por tipo y, si hay ops en el registry, `metadata.execution: <tool_id>`.

El cuerpo debe incluir `## Overview` y `## When to Use`. Las skills que empaquetan scripts ejecutables también incluyen `## Tools` y `scripts/tests/smoke_sh.sh`.

## Referencias cruzadas

Las flechas (`→ otra-skill`) de las descripciones deben apuntar a una skill existente en este catálogo.

## Canon de flota

Este repositorio aloja el contrato P0/P1 de la flota. Índice rápido:

| Pieza                 | Ruta                                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------- |
| ADRs                  | [`docs/architecture/decisions/`](docs/architecture/decisions/) (ADR-0001…; host: ADR-0016; execution: ADR-0017) |
| Reutilización         | [`docs/REUTILIZACION.md`](docs/REUTILIZACION.md)                                                                |
| Callers por stack     | [`stacks/`](stacks/)                                                                                            |
| Reusables CI          | [`.github/workflows/reusable-*.yml`](.github/workflows/)                                                        |
| Plantilla de producto | [`templates/product/`](templates/product/) — `gh repo create … && cp -a templates/product/. <repo>/`            |
| Glosario              | [`docs/GLOSARIO.md`](docs/GLOSARIO.md) — un término canónico por concepto                                       |

Norma de planes (plantilla en `docs/` + carpeta `docs/plans/`) llegan en T2. Rulesets como código llegan con P2/P10 (`rulesets/`).

## Validación

```bash
bash run-validation.sh
# o: make validate && make test && make smoke
```

Comprueba: esquema del frontmatter, cláusulas de alcance de las descripciones, canon de encabezados, paridad del catálogo entre carpetas, README y TAXONOMY, resolución de referencias y smoke tests.
