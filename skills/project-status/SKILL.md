---
name: project-status
description:
  "Product status orchestrator: read development state (branch, plans, uncommitted work, CI),
  report health and pending work, hygienise branches and uncommitted changes, then close the
  increment with local gates, versioning, packaging and publication. Use when asking about repo
  status, where work stands, cleaning up branches before continuing, or closing and releasing an
  increment. Not for spec authorship (→ plan-specification), test plans (→ plan-testing) or
  machineroom self-audit (→ project-machineroom)."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "9.0.2"
  domain: project
  type: orchestrator
  language: en
  keywords:
    - project-status
    - project
    - status-board
    - hygiene
    - release
    - branch-cleanup
  execution: project-status
compatibility: cursor, pi, opencode
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Project Status

## Overview

One door for "where does this product stand, what needs cleaning, and how does
this increment close". It works in three ordered stages — **observe → hygienise
→ close** — and never merges one stage's evidence into another's verdict.

It reads, it reports, it cleans and it releases. It does not author
specifications, design test plans, review code security or audit machineroom
itself.

## When to Use

- Operator asks where work stands, what is pending, or what to do next
- Bringing a repo up to date before starting or resuming a plan
- Cleaning merged branches and integrating uncommitted work
- Closing an increment: local gates, version bump, changelog, packaging, PR,
  merge-watch and publication

**When NOT to use:** writing or revising a spec and its task list
(→ plan-specification); planning integrated tests (→ plan-testing); auditing
machineroom internals (→ project-machineroom); stack-agnostic architecture drift
(→ project-architecture); building or packaging the Linux artifact
(→ role-linux).

## Stage 1 — Observe

Read state, never guess it:

1. **Branch and tree:** current branch, upstream divergence, uncommitted and
   untracked files, stash entries.
2. **Declared state:** `.machineroom/status.yaml`, `project.yaml`, open plans in
   `tasks/` or `docs/plans/`, roadmap files.
3. **Repository health:** P0/P1/P2 findings, health score, Renovate and CI
   status for the default branch.
4. **Staleness:** `handoffs` in `project.yaml` that name skills no longer in the
   catalog, outdated plan files, branches already merged.

Output is a status board plus a short verdict: `in progress`, `blocked`,
`ready to close` or `needs hygiene` — each with the evidence that supports it.

```bash
python skills/project-status/scripts/inicio_plan.py . --out /tmp/status
python skills/project-status/scripts/scan_repo.py .
python skills/project-status/scripts/audit-repo.sh .
python skills/project-status/scripts/check-product-structure.sh .
```

Reference: [inicio-plan.md](references/inicio-plan.md),
[plantilla-informe.md](references/plantilla-informe.md).

## Stage 2 — Hygienise

Cleaning is a mutation and needs an explicit target:

- **Merged branches:** delete local and remote branches already merged into the
  default branch. Never delete a branch with unmerged commits.
- **Uncommitted work:** classify as intentional (commit it with a conventional
  message), accidental (restore), or unknown (stop and ask). Do not `git
checkout --` over work you did not classify.
- **Stale state:** fix `handoffs` naming removed skills, remove superseded plan
  files, prune merged worktrees.
- **Hygiene evidence:** record what was deleted, what was committed and what was
  left untouched.

Reference: [higiene-community.md](references/higiene-community.md).

## Stage 3 — Close and release

Only after observe and hygienise are green:

1. **Local gates:** run the repository's own quality commands and install
   conventional hooks when missing.
2. **Version:** semantic bump per the catalog's versioning contract; changelog
   entry in Keep a Changelog with Added/Changed/Removed/Fixed.
3. **Packaging:** delegate artifact build and package specs to `role-linux` when
   the release ships a Linux package.
4. **CI/CD audit:** required checks, pinned actions with explicit permissions,
   Renovate as the only version updater.
5. **PR + merge-watch:** open the PR, subscribe to CI and PR events, declare what
   is expected and stop the turn instead of polling.
6. **Publication:** tag and release only with explicit authorization; the
   `publish` operation carries `approval_required: true` in the registry.

Reference: [cierre-trabajo.md](references/cierre-trabajo.md),
[versioning-guide.md](references/versioning-guide.md),
[changelog-guide.md](references/changelog-guide.md),
[ci-cd-patterns.md](references/ci-cd-patterns.md),
[actions-security.md](references/actions-security.md),
[merge-watch.md](references/merge-watch.md),
[renovate-grouped.md](references/renovate-grouped.md).

## Pipeline position

```text
DEFINE → SCHEMAS → IMPLEMENT → VALIDATE → INTEGRATE → STATUS
  plan-     project-    role-*     plan-    project-   project-
  specifi-  status                 testing  status     status
  cation
```

This skill owns SCHEMAS, INTEGRATE and STATUS. Route a phase with:

```bash
python tools/workspace-router/run.py --phase STATUS --repo . --json
```

## Boundaries

- **Read freely, mutate with evidence.** Reporting never needs approval; branch
  deletion, integration of uncommitted work and publication do.
- **No force-push, no history rewrite, no `--admin` merge.** Those are operator
  decisions, not hygiene.
- **Never promote a skip, a missing dependency or a `not_run` to pass.** Use
  `blocked` / `not_applicable` / `not_run` with a reason.
- **Never invent a second test stack.** Test plans belong to `plan-testing`.
- **Never publish from an ambiguous state.** A dirty tree or a stale handoff
  blocks the close stage.

## Tools

- `scripts/inicio_plan.py` — plan starting point: git state, structure, roadmap,
  findings; writes `ESTADO.md`/`inicio.json` (read-only over the repo).
- `scripts/scan_repo.py` — repository scan (structure, dependencies, CI; secret
  findings as path/line/fingerprint only).
- `scripts/audit-repo.sh` — repo audit wrapper.
- `scripts/check-product-structure.sh` — product structure check against the
  fleet canon.
- `scripts/gate-husky.sh` — install conventional hooks and run the local gate.
- `scripts/review-vs-plan.py` — contrast plan against execution when closing.
- `scripts/tests/smoke_sh.sh`, `scripts/tests/smoke_hooks.sh` — smoke for the script set.
- `actions/{setup-node,actionlint,secret-scan}/action.yml` — pinned composite actions
  the close stage references instead of re-writing workflow steps.

## References

- [inicio-plan.md](references/inicio-plan.md) — status board generation.
- [plantilla-informe.md](references/plantilla-informe.md) — report template.
- [readiness-checklist.md](references/readiness-checklist.md) — close gate checklist (OK/WARN/BLOCK/N/A).
- [higiene-community.md](references/higiene-community.md) — branch and tree hygiene.
- [cierre-trabajo.md](references/cierre-trabajo.md) — ordered closure, PR, merge-watch.
- [versioning-guide.md](references/versioning-guide.md) — semantic version and bump policy.
- [changelog-guide.md](references/changelog-guide.md) — Keep a Changelog entries.
- [ci-cd-patterns.md](references/ci-cd-patterns.md) — caller workflows per stack.
- [actions-security.md](references/actions-security.md) — pinned actions, permissions.
- [merge-watch.md](references/merge-watch.md) — listen, do not poll.
- [renovate-grouped.md](references/renovate-grouped.md) — grouped dependency updates.
- [verification-guide.md](references/verification-guide.md) — evidence checklist.
- [source-guide.md](references/source-guide.md) — authority hierarchy.
- [citation-guide.md](references/citation-guide.md) — citation formats.
