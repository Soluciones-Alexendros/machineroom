---
name: project-audit
description:
  "Repo health board and evolution plan: scan repository, generate status
  board (P0/P1/P2 findings, health score, Renovate/CI status), and produce evolution
  plan. Use when starting a project, bringing a repo up to date, or needing a status
  snapshot. Not for machineroom self-audit (→ project-machineroom); not for phase
  routing (→ plan-continue); not for dependency SCA/CVE scanning (→ project-libraries);
  not for architecture drift analysis (→ project-architecture)."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: 1.0.0
  domain: project
  type: atomic
  language: en
  keywords:
    - project-audit
    - project
    - repo-audit
    - health-board
    - evolution-plan
    - status
  execution: project-audit
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Project Audit

## Overview

Repo health board and evolution plan. Scans the repository, generates a status board with P0–P4 findings, health score (0–100), Renovate/CI status, and produces an evolution plan for the next increment.

## When to Use

- Repo starting / bring a project up to date
- Periodic health check of a product repository
- Generate `ESTADO.md` status board for planning
- Need evolution plan before DEFINE phase

## Not for:

- Machineroom self-audit (→ project-machineroom)
- Phase routing and status bump (→ plan-continue)
- Dependency SCA/CVE scanning (→ project-libraries)
- Architecture drift analysis (→ project-architecture)

## Scripts

- `scripts/scan_repo.py` — Repository scan (secrets, structure, deps, CI)
- `scripts/audit_repo.sh` — Full repo audit wrapper
- `scripts/check-product-structure.sh` — Product structure validation
- `scripts/inicio_plan.py` — Status board generation (P0/P1/P2, health score, Renovate, CI)

## References

| File                                                      | Description                                                   |
| --------------------------------------------------------- | ------------------------------------------------------------- |
| [inicio-plan.md](references/inicio-plan.md)               | Status board generation: P0/P1/P2, health score, Renovate, CI |
| [plantilla-informe.md](references/plantilla-informe.md)   | Report template for audit output                              |
| [verification-guide.md](references/verification-guide.md) | Verification checklist and evidence standards                 |

## Outputs

- `ESTADO.md` — Status board (P0/P1/P2 findings, health score, Renovate/CI status)
- `inicio.json` — Machine-readable audit data
- Evolution plan → feeds `plan-specification` for DEFINE phase

## Tools

- `scripts/scan_repo.py` — repository scan (secrets, structure, deps, CI)
- `scripts/audit-repo.sh` — full repo audit wrapper
- `scripts/check-product-structure.sh` — product structure validation
- `scripts/inicio_plan.py` — status board generation (P0/P1/P2, health score, Renovate, CI)

## Relationship

```
project-audit (repo health) ──feeds──► plan-specification (DEFINE)
       │
       └── not: project-machineroom (self-audit), plan-continue (phase routing)
```
