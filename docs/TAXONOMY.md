# Skill taxonomy

14 skills in 5 domains. The `metadata.domain` frontmatter field reflects this table, and the name prefix is the domain (normative, not advisory). The taxonomy is closed: every new skill must fit an existing domain or propose a new one in the PR (see CONTRIBUTING.md).

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

## Closed sets (normative)

**Domain** (metadata.domain): `plan` | `local` | `project` | `web` | `role`

**Type** (metadata.type): `atomic` | `orchestrator` | `router` | `audit`

- `atomic`: single-capability skill, executed directly
- `orchestrator`: runs a multi-step workflow end to end
- `router`: dispatches to other skills (runs no domain logic itself)
- `audit`: read-only assessment producing findings and a remediation plan

## Rules

1. The `name` frontmatter field in `SKILL.md` is identical to the directory name.
2. The `metadata.domain` field reflects this table — the name prefix IS the domain (normative, not advisory): every skill is named `<domain>-<slug>` in kebab-case.
3. The `metadata.type` field is required and must be one of the closed set; `metadata.language` is `en`.
4. The `description` field declares scope and limits (`Use when` plus an exclusion clause) with cross-references (`→ other-skill`) where scopes overlap; every arrow target must exist.
5. Body has `## Overview` and `## When to Use`; skills bundling executables also have `## Tools` plus `scripts/tests/smoke_sh.sh`.

## Domain semantics (why a skill belongs where it does)

| Domain    | Owns                                                                                              | Does not own                                    |
| --------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `plan`    | Method and artefacts of planning: specification, task decomposition, integrated-test plans        | The repo/product state, implementation surfaces |
| `project` | The repository or product as a unit: architecture, status/hygiene/release, machineroom self-audit | Methodology, per-surface implementation         |
| `role`    | An implementation surface: backend, frontend, clean code, Linux artifact engineering              | Host operation, release closure                 |
| `local`   | The host machine: maintenance and defensive security                                              | Application code or packaging                   |
| `web`     | Audit of a web surface: compliance, security review, performance                                  | Backend/frontend implementation                 |

A new skill goes in the domain that owns the _decision it makes_, not the domain
of the tooling it runs.

## Versioning signals

Three independent signals; conflating them is how the catalog drifts:

| Signal          | Meaning                                                  | Where                                                                                          |
| --------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Product version | The published contract of the catalog (breaking = MAJOR) | `package.json`, `CHANGELOG.md`, git tags                                                       |
| Index version   | The schema/generator version of `skill-index.json`       | `tools/skill-index/generate.py` (`INDEX_VERSION`) and `docs/architecture/skill-index-<v>.json` |
| Skill version   | SemVer of one skill, bumped when that skill changes      | `metadata.version` in `SKILL.md`, enforced by `tools/version/bump.py --check`                  |

A catalog-wide breaking change bumps the product to a new MAJOR and bumps every
touched skill with `bump.py`; the index version moves only when the index shape
or the generator changes.

## Enforced invariants

`tools/validate/skill_spec.py` fails the gate when:

- a `→ other-skill` arrow in the **body** (not only in `description`) names a skill outside the catalog;
- the intro prose of `README.md` or `docs/TAXONOMY.md` claims a skill count that differs from the generated catalog;
- a `role-*` mentioned in `AGENTS.md`, `README.md` or `skills/plan-specification/SKILL.md` is outside the `plan.schema.json` role enum, or the enum names a role with no skill.

`tools/workspace-router/run.py` refuses to route when `.machineroom/project.yaml`
declares a `handoff` that no longer resolves, and reports the documented
replacement. `tools/harness/doctor.py` reports the same as a `handoffs` check.
