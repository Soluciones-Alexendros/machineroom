# Plan: Skills Repertoire Improvement (SDD)

## Objective

Transform the current 16-skills catalog into a coherent, fluid, well-referenced, and effective repertoire that:

- Follows the fleet canon (STANDARD.md, TAXONOMY.md, GLOSARIO.md) without deviation
- Applies progressive disclosure (≤500 lines/skill, references/ for depth)
- Has consistent metadata, naming, cross-references, and type classification
- Eliminates overlaps, gaps, and architectural drift
- Enables reliable skill discovery and invocation in both Pi and Cursor

---

## Phase 0: Scope Check — Capability Map

The request bundles **multiple independently shippable capabilities**:

| Capability ID                | Description                                                                                    | Consumer                 | Shippable Alone |
| ---------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------ | --------------- |
| `metadata-normalization`     | Unify frontmatter fields, version scheme, type/domain accuracy across all 16 skills            | All skills               | Yes             |
| `naming-coherence`           | Verify/enforce `<domain>-<slug>` kebab-case, fix `local-email` specificity                     | Taxonomy, discovery      | Yes             |
| `references-structure`       | Ensure every skill has `references/` with progressive-disclosure content; migrate inline docs  | Skill authors, operators | Yes             |
| `cross-reference-integrity`  | Fix broken/missing `→ skill` arrows, add missing neighbor links                                | Discovery, routing       | Yes             |
| `type-reclassification`      | Align `metadata.type` (atomic/orchestrator/router/audit) with actual behavior                  | Orchestration, routing   | Yes             |
| `orchestrator-deduplication` | Clarify `plan-continue` vs `project-machineroom` responsibilities                              | Plan runtime, self-audit | Yes             |
| `skill-gap-analysis`         | Identify missing skills per domain (e.g., `local-network`, `project-dependencies`, `role-api`) | Future planning          | Yes             |
| `validation-tooling`         | Add/extend `tools/validate/skill_spec.py` checks for new rules                                 | CI, contributors         | Yes             |

**Dependencies:** `metadata-normalization` → `cross-reference-integrity` → `type-reclassification` → `orchestrator-deduplication`. Others can run in parallel after `metadata-normalization`.

---

## Phase 1: Specification

### 1.1 Assumptions (Locked)

| Assumption             | Value                                                         | Source                       |
| ---------------------- | ------------------------------------------------------------- | ---------------------------- |
| Stack                  | Python (tools), Markdown (skills), YAML (frontmatter)         | Repo structure               |
| Validation             | `tools/validate/skill_spec.py` + `skill_links.py`             | STANDARD.md                  |
| Distribution           | Pi package (Git), Cursor plugin (symlinks)                    | harnesses.md                 |
| Canon sources          | AGENTS.md, STANDARD.md, TAXONOMY.md, GLOSARIO.md, ADRs        | canon-map.md                 |
| Language rule          | Skill bodies in English; operator plans in Spanish            | GLOSARIO.md §Regla de idioma |
| Progressive disclosure | ≤500 lines, ≤5000 tokens per SKILL.md; depth in `references/` | STANDARD.md                  |
| Forbidden patterns     | `What it does`, `Usage`, `Structure`, host-specific paths     | STANDARD.md                  |

### 1.2 Specification: Target State

#### A. Metadata Normalization (All Skills)

| Field                      | Rule                                                                                             | Current Violations                                                                                                                                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                     | = directory name, kebab-case, 1–64 chars                                                         | ✓ All compliant                                                                                                                                                                                                         |
| `description`              | 1–1024 chars; template: `[Capability]. Use when [contexts]. Not for [limit] (→ neighbor-skill).` | `plan-continue` too long; `local-email` missing exclusion arrow for some cases                                                                                                                                          |
| `license`                  | `MIT` (repo-wide)                                                                                | ✓ All compliant                                                                                                                                                                                                         |
| `metadata.author`          | `Soluciones-Alexendros`                                                                          | `plan-continue`, `plan-specification`, `plan-validators`, `project-architecture`, `project-libraries`, `web-compliance`, `web-owasp`, `web-performance` use `addyosmani (adapted)` or `Soluciones-Alexendros (adapted)` |
| `metadata.version`         | SemVer string; bump on PR touch                                                                  | `local-maintenance` v8.0.0 vs others v7.1.x; `local-security` v7.1.1                                                                                                                                                    |
| `metadata.domain`          | One of: `plan`, `local`, `project`, `web`, `role`                                                | ✓ All compliant (prefix matches)                                                                                                                                                                                        |
| `metadata.type`            | One of: `atomic`, `orchestrator`, `router`, `audit`                                              | `plan-continue`=orchestrator ✓; `project-machineroom`=orchestrator ✓; `project-architecture`=audit but has analysis tools; `project-libraries`=audit but has pipeline; `web-*`=audit ✓                                  |
| `metadata.language`        | `en`                                                                                             | ✓ All compliant                                                                                                                                                                                                         |
| `metadata.keywords`        | Array, includes skill name                                                                       | Most have single string; should be array                                                                                                                                                                                |
| `metadata.execution`       | = skill name (for run_registered)                                                                | Mostly ✓                                                                                                                                                                                                                |
| `compatibility`            | `["cursor", "pi"]` or subset                                                                     | Some missing                                                                                                                                                                                                            |
| `allowed-tools`            | Minimal set; no `Write` for audit skills                                                         | `project-architecture` has only Read/Grep/Glob ✓; `web-*` have only Read/Grep/Glob ✓; `local-*` have Bash/Write via run_registered ✓                                                                                    |
| `disable-model-invocation` | Only for skills that must not call the model (e.g., `project-publish`, `local-*`)                | `local-email`, `local-maintenance`, `local-security`, `project-publish` have it; `role-*` don't but should they?                                                                                                        |

#### B. Naming Coherence

| Skill         | Current                                       | Issue                             | Fix                                                                          |
| ------------- | --------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------- |
| `local-email` | —                                             | **Retirada** (orden del operador) | `SKILL.md`, `references/` y driver `tools/email/` eliminados; catálogo en 16 |
| `data-linkml` | Directorio con `__pycache__` y sin `SKILL.md` | Huérfano                          | **Eliminado**                                                                |

#### C. References Structure (Per Skill)

| Skill                  | Current Refs | Target                                                                                                                                    | Gap    |
| ---------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `plan-continue`        | 18 files     | ✓ Comprehensive                                                                                                                           | —      |
| `plan-specification`   | 5 files      | ✓ Good                                                                                                                                    | —      |
| `plan-validators`      | 3 files      | Add `test-patterns.md`, `cookbook.md`                                                                                                     | Medium |
| `project-architecture` | 0 files      | Add `dependency-mapping.md`, `metrics-guide.md`, `drift-detection.md`                                                                     | High   |
| `project-libraries`    | 4 files      | Add `ecosystem-guides/`, `remediation-playbook.md`                                                                                        | Medium |
| `project-machineroom`  | 5 files      | ✓ Good                                                                                                                                    | —      |
| `project-publish`      | 6 files      | Add `versioning-guide.md`, `changelog-guide.md`                                                                                           | Low    |
| `role-back`            | 0 files      | Add `cache-patterns.md`, `queue-patterns.md`, `rate-limit-patterns.md`, `storage-patterns.md`, `search-patterns.md`, `vector-patterns.md` | High   |
| `role-clean-code`      | 4 files      | ✓ Good                                                                                                                                    | —      |
| `role-design`          | 11 files     | ✓ Comprehensive                                                                                                                           | —      |
| `role-front`           | 0 files      | Add `state-management.md`, `routing-patterns.md`, `form-patterns.md`, `api-contracts.md`                                                  | High   |
| `web-compliance`       | 10 files     | ✓ Good                                                                                                                                    | —      |
| `web-owasp`            | 28 files     | ✓ Comprehensive (consider splitting)                                                                                                      | —      |
| `web-performance`      | 2 files      | Add `cwv-deep-dive.md`, `rendering-modes.md`, `caching-strategies.md`, `lighthouse-guide.md`                                              | High   |
| `local-email`          | 6 files      | Add `driver-interface.md`, `proton-bridge-api.md`                                                                                         | Low    |
| `local-maintenance`    | 9 files      | ✓ Good                                                                                                                                    | —      |
| `local-security`       | 6 files      | Add `hardening-checklist.md`, `cve-tracking.md`, `forensics-guide.md`                                                                     | Medium |

#### D. Cross-Reference Integrity

Every skill's `description` and `When to Use`/`Not for` must have valid `→ skill` arrows where scopes overlap. Current gaps:

| From Skill             | Missing Arrow         | Target Skill                                                | Reason                              |
| ---------------------- | --------------------- | ----------------------------------------------------------- | ----------------------------------- |
| `plan-continue`        | —                     | `project-machineroom`                                       | Self-audit vs plan continuation     |
| `plan-specification`   | `→ plan-validators`   | `plan-validators`                                           | Implementation phase                |
| `plan-validators`      | `→ role-*`            | `role-back`, `role-front`, `role-design`, `role-clean-code` | Implementation roles                |
| `project-architecture` | `→ role-clean-code`   | `role-clean-code`                                           | Refactoring outcome                 |
| `project-libraries`    | `→ project-publish`   | `project-publish`                                           | Dependency updates → release        |
| `project-machineroom`  | `→ plan-continue`     | `plan-continue`                                             | Plan continuation after self-audit  |
| `role-back`            | `→ project-libraries` | `project-libraries`                                         | Supply chain before new deps        |
| `role-front`           | `→ role-design`       | `role-design`                                               | Visual polish handoff               |
| `role-design`          | `→ role-front`        | `role-front`                                                | Implementation handoff              |
| `web-compliance`       | `→ web-owasp`         | `web-owasp`                                                 | Security overlap                    |
| `web-owasp`            | `→ web-compliance`    | `web-compliance`                                            | Compliance overlap                  |
| `web-performance`      | `→ web-compliance`    | `web-compliance`                                            | CWV overlaps with SEO/accessibility |
| `local-maintenance`    | `→ local-security`    | `local-security`                                            | ✓ Present                           |
| `local-security`       | `→ local-maintenance` | `local-maintenance`                                         | ✓ Present                           |

#### E. Type Reclassification

| Skill                  | Current      | Actual Behavior                                        | Proposed         | Rationale                                          |
| ---------------------- | ------------ | ------------------------------------------------------ | ---------------- | -------------------------------------------------- |
| `plan-continue`        | orchestrator | Routes phases, scaffolds .machineroom                  | **router**       | Dispatches to other skills; runs no domain logic   |
| `project-machineroom`  | orchestrator | Audits, plans changes, no direct execution             | **audit**        | Read-only assessment; publishes via separate skill |
| `project-architecture` | audit        | Analysis + mapping tools (madge, etc.)                 | **audit**        | ✓ Correct                                          |
| `project-libraries`    | audit        | Multi-language pipeline (active scanning)              | **atomic**       | Executes pipeline; not read-only                   |
| `project-publish`      | atomic       | Gates + git/gh operations                              | **orchestrator** | Multi-step workflow with external effects          |
| `web-compliance`       | audit        | Scripts produce verdict + remediation                  | **audit**        | ✓ Correct                                          |
| `web-owasp`            | audit        | Code review with extensive references                  | **audit**        | ✓ Correct                                          |
| `web-performance`      | audit        | Lighthouse/CWV audits                                  | **audit**        | ✓ Correct                                          |
| `local-maintenance`    | atomic       | Read-only audit + optional mutation via run_registered | **atomic**       | ✓ Correct (health=read, remediation=mutate)        |
| `local-security`       | atomic       | Hardening via run_registered                           | **atomic**       | ✓ Correct                                          |
| `local-email`          | atomic       | Driver operations via run_registered                   | **atomic**       | ✓ Correct                                          |
| `role-back`            | atomic       | Implements backend code                                | **atomic**       | ✓ Correct                                          |
| `role-front`           | atomic       | Implements frontend code                               | **atomic**       | ✓ Correct                                          |
| `role-design`          | atomic       | Mutates tokens/CSS/components                          | **atomic**       | ✓ Correct                                          |
| `role-clean-code`      | atomic       | Refactors with verification                            | **atomic**       | ✓ Correct                                          |
| `plan-specification`   | orchestrator | SPEC→PLAN→TASKS→IMPLEMENT                              | **orchestrator** | ✓ Correct                                          |
| `plan-validators`      | atomic       | TDD cycle per task                                     | **atomic**       | ✓ Correct                                          |

#### F. Orchestrator Deduplication

**Current Overlap:**

- `plan-continue`: "continue from roadmap or .machineroom status; when missing, audit the repo, scaffold .machineroom/status.yaml, and route DEFINE→SCHEMAS→IMPLEMENT→VALIDATE→INTEGRATE→STATUS"
- `project-machineroom`: "audit and improve the machineroom system itself: canon map, control plane, harnesses, migrations and self-change protocol"

**Resolution:**

- `plan-continue` → **router** (renamed to `plan-router`?): Pure phase router + status bump. No repo audit. Entry point for "where to start" / "bring up to date".
- `project-machineroom` → **audit**: Self-audit of machineroom (canon, harnesses, control plane). Produces findings → feeds `plan-specification` for changes.
- New `plan-audit` (or extend `plan-continue`): Repo audit → status board → evolution plan. Separate from machineroom self-audit.

#### G. Skill Gap Analysis (Future)

| Domain    | Missing Capability                                  | Proposed Skill         | Priority |
| --------- | --------------------------------------------------- | ---------------------- | -------- |
| `local`   | Network diagnostics, firewall, DNS                  | `local-network`        | P1       |
| `local`   | Container/podman/docker host ops                    | `local-containers`     | P2       |
| `project` | Dependency update automation (Renovate PR handling) | `project-dependencies` | P1       |
| `project` | License compliance / SBOM policy                    | `project-licenses`     | P2       |
| `role`    | API contract design (OpenAPI/GraphQL)               | `role-api`             | P1       |
| `role`    | Database schema/migration design                    | `role-data`            | P2       |
| `web`     | API security testing (fuzzing, contract testing)    | `web-api-security`     | P2       |

---

## Phase 2: Technical Plan

### 2.1 Work Order (Dependency-Respecting)

```
1. metadata-normalization (foundation)
   ├─ 1.1 Fix author, version, keywords array, compatibility, allowed-tools
   ├─ 1.2 Normalize description template across all 16 skills
   └─ 1.3 Add/fix disable-model-invocation per policy

2. cross-reference-integrity (depends on 1)
   ├─ 2.1 Audit all → arrows in descriptions and When to Use
   ├─ 2.2 Add missing neighbor links (table above)
   └─ 2.3 Validate with skill_links.py

3. references-structure (parallel after 1)
   ├─ 3.1 Create missing references/ for: project-architecture, project-libraries, role-back, role-front, web-performance
   ├─ 3.2 Migrate inline procedural content from SKILL.md to references/
   ├─ 3.3 Ensure each SKILL.md ≤500 lines / ≤5000 tokens
   └─ 3.4 Add reference index to each SKILL.md

4. type-reclassification (depends on 1, 2)
   ├─ 4.1 Update metadata.type per table in 1.2.E
   ├─ 4.2 Update TAXONOMY.md type column
   └─ 4.3 Update skill_spec.py validator for new types

5. orchestrator-deduplication (depends on 1, 4)
   ├─ 5.1 Redefine plan-continue as pure router (phase routing only)
   ├─ 5.2 Redefine project-machineroom as pure audit (self-audit only)
   ├─ 5.3 Create plan-audit skill for repo audit + status board (or extend plan-continue with clear boundary)
   └─ 5.4 Update AGENTS.md routing contract

6. naming-coherence (parallel)
   ├─ 6.1 Retirar local-email + driver (hecho)
   ├─ 6.2 Eliminar data-linkml huérfano (hecho)
   └─ 6.3 Instaladores con conteo derivado (hecho)

7. validation-tooling (parallel, ongoing)
   ├─ 7.1 Extend skill_spec.py: type enum, description template, keywords array, cross-ref validation
   ├─ 7.2 Add skill_links.py: verify all → targets exist
   ├─ 7.3 Add line/token count check (≤500/≤5000)
   └─ 7.4 Integrate into CI (make validate)

8. documentation-sync (final)
   ├─ 8.1 Update TAXONOMY.md (auto-generated from skills)
   ├─ 8.2 Update GLOSARIO.md if new terms
   ├─ 8.3 Update AGENTS.md skill list and routing rules
   └─ 8.4 Update harness-setup.md / harness-integration.md if distribution changes
```

### 2.2 Risks & Mitigations

| Risk                                       | Likelihood | Impact | Mitigation                                                            |
| ------------------------------------------ | ---------- | ------ | --------------------------------------------------------------------- |
| Breaking Pi/Cursor discovery during rename | Medium     | High   | Keep old names as symlinks during transition; test in both harnesses  |
| Cross-reference cycles                     | Low        | Medium | Validate with DAG check in skill_links.py                             |
| Skill body truncation loses nuance         | Medium     | Medium | Progressive disclosure: move to references/, keep summary in SKILL.md |
| Type change breaks orchestration logic     | Low        | High   | Update workspace-router and orchestration code in same PR             |
| Validator false positives                  | Medium     | Low    | Dry-run on all skills before enforcing in CI                          |

### 2.3 Verification Checkpoints

| Checkpoint        | Command                                                      | Expected                     |
| ----------------- | ------------------------------------------------------------ | ---------------------------- |
| Metadata valid    | `python tools/validate/skill_spec.py --all`                  | All PASS                     |
| Links valid       | `python tools/validate/skill_links.py`                       | All PASS                     |
| Size limits       | `python tools/validate/skill_spec.py --size`                 | All ≤500 lines, ≤5000 tokens |
| Taxonomy sync     | `python tools/validate/skill_spec.py --taxonomy`             | TAXONOMY.md matches skills   |
| Harness discovery | `pi skill list` / Cursor `/skills`                           | All 16 skills discoverable   |
| Self-audit        | `uv run python tools/harness/doctor.py --harness all --json` | No drift                     |

---

## Phase 3: Tasks (Todo List)

### 3.1 metadata-normalization

- [ ] **TASK-001**: Normalize `metadata.author` to `Soluciones-Alexendros` for all 16 skills
- [ ] **TASK-002**: Align `metadata.version` scheme (patch for docs, minor for capability, major for breaking)
- [ ] **TASK-003**: Convert `metadata.keywords` from string to array; include skill name + domain + 3-5 keywords
- [ ] **TASK-004**: Add `compatibility: ["cursor", "pi"]` to all skills
- [ ] **TASK-005**: Audit `allowed-tools` — remove `Write` from audit skills, ensure `run_registered` path for mutating skills
- [ ] **TASK-006**: Set `disable-model-invocation: true` for `local-*`, `project-publish`; remove from others
- [ ] **TASK-007**: Rewrite all `description` fields to template: `[Capability]. Use when [contexts]. Not for [limit] (→ neighbor-skill).`

### 3.2 cross-reference-integrity

- [ ] **TASK-008**: Audit all `→ skill` arrows in descriptions and `When to Use`/`Not for` sections
- [ ] **TASK-009**: Add missing arrows per table in 1.2.D (14 arrows)
- [ ] **TASK-010**: Run `skill_links.py` validator; fix all broken references

### 3.3 references-structure

- [ ] **TASK-011**: Create `references/` for `project-architecture` (3 files: dependency-mapping, metrics-guide, drift-detection)
- [ ] **TASK-012**: Create `references/` for `project-libraries` (2 files: ecosystem-guides, remediation-playbook)
- [ ] **TASK-013**: Create `references/` for `role-back` (6 pattern files per table in 1.2.C)
- [ ] **TASK-014**: Create `references/` for `role-front` (4 files: state-management, routing-patterns, form-patterns, api-contracts)
- [ ] **TASK-015**: Create `references/` for `web-performance` (4 files: cwv-deep-dive, rendering-modes, caching-strategies, lighthouse-guide)
- [ ] **TASK-016**: Migrate inline procedural content from SKILL.md to references/ for skills exceeding 500 lines
- [ ] **TASK-017**: Add reference index (table) to each SKILL.md linking to references/

### 3.4 type-reclassification

- [ ] **TASK-018**: Update `metadata.type` for 7 skills per table in 1.2.E
- [ ] **TASK-019**: Update TAXONOMY.md type column (auto-generate or manual)
- [ ] **TASK-020**: Update `tools/validate/skill_spec.py` type enum and validation logic

### 3.5 orchestrator-deduplication

- [ ] **TASK-021**: Redefine `plan-continue` SKILL.md as pure router (phase routing + status bump only)
- [ ] **TASK-022**: Redefine `project-machineroom` SKILL.md as pure audit (self-audit only, no phase routing)
- [ ] **TASK-023**: Create `plan-audit` skill for repo audit + status board + evolution plan (or document boundary in plan-continue)
- [ ] **TASK-024**: Update AGENTS.md routing contract to reflect new boundaries
- [ ] **TASK-025**: Update `tools/workspace-router/run.py` to use new router skill

### 3.6 naming-coherence

- [x] **TASK-026**: Retirar `local-email` y su driver (hecho 2026-11-15)
- [x] **TASK-027**: Eliminar `skills/data-linkml/` huérfano (hecho 2026-11-15)
- [x] **TASK-028**: Instaladores y matriz de instalación con conteo derivado del catálogo (hecho 2026-11-15)
- [ ] **TASK-028b**: Nota `Removed` de `local-email` en `CHANGELOG.md` junto al bump a `8.1.0` (D8). El gate `check-bump` exige versión por delante del tag cuando cambia `CHANGELOG.md`, así que la entrada viaja con el PR de release, no con el de la retirada.

### 3.7 validation-tooling

- [ ] **TASK-029**: Extend `skill_spec.py`: description template regex, keywords array, cross-ref existence, size limits
- [ ] **TASK-030**: Extend `skill_links.py`: verify all `→ skill` targets exist in skills/
- [ ] **TASK-031**: Add `make validate-skills` target running all validators
- [ ] **TASK-032**: Integrate into CI workflow (`.github/workflows/ci.yml`)

### 3.8 documentation-sync

- [ ] **TASK-033**: Regenerate TAXONOMY.md from skills (script or manual)
- [ ] **TASK-034**: Update GLOSARIO.md if new canonical terms introduced
- [ ] **TASK-035**: Update AGENTS.md skill discovery and routing sections
- [ ] **TASK-036**: Update docs/harness-setup.md and harness-integration.md if distribution changed

---

## Phase 4: Acceptance Criteria

### 4.1 Definition of Done (Per Capability)

| Capability                   | Acceptance Criteria                                                                                   |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| `metadata-normalization`     | All 16 skills pass `skill_spec.py --metadata`; author/version/keywords/compatibility/tools consistent |
| `cross-reference-integrity`  | `skill_links.py` reports 0 broken arrows; all 14 missing arrows added                                 |
| `references-structure`       | All 16 skills have `references/`; all SKILL.md ≤500 lines / ≤5000 tokens; reference index present     |
| `type-reclassification`      | TAXONOMY.md type column matches SKILL.md; validator enforces closed set                               |
| `orchestrator-deduplication` | `plan-continue` routes only; `project-machineroom` audits only; no overlap in AGENTS.md               |
| `naming-coherence`           | No orphan directories; all skills follow `<domain>-<slug>`; install scripts work                      |
| `validation-tooling`         | `make validate-skills` passes; CI gate `ci-gate` includes skill validation                            |
| `documentation-sync`         | TAXONOMY.md, GLOSARIO.md, AGENTS.md, harness docs reflect final state                                 |

### 4.2 Global Verification

```bash
# Run from repo root
make validate-skills          # All validators pass
python tools/workspace-router/run.py --status --repo . --json  # Status clean
uv run python tools/harness/doctor.py --harness all --json     # No drift
pi skill list                  # All skills discoverable in Pi
# In Cursor: /skills shows all skills
```

---

## Phase 5: Implementation Roles & Handoffs

| Task Group              | Implementation Role                                                                             | Test Surface                         | Handoff                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------- |
| Metadata, types, naming | `role-clean-code` (consistency) + `plan-specification` (structure)                              | Validator output                     | → `plan-validators` for validator tests |
| References content      | `role-back` (project-*), `role-front` (role-front), `role-design` (role-design), domain experts | Reference readability, link validity | → `plan-validators` for link checks     |
| Orchestrator logic      | `plan-continue` (router), `project-machineroom` (audit)                                         | Phase routing, audit output          | → `plan-validators` for E2E phase test  |
| Validator code          | `role-back` (Python tooling)                                                                    | Unit tests for validators            | → `plan-validators` for integration     |
| Documentation sync      | `plan-specification` (canonical docs)                                                           | Doc render, terminology check        | → `project-publish` for release         |

**Recurrent routing:** Before each task group, re-evaluate and invoke matching roles per AGENTS.md.

---

## Open Questions

Resueltas: `local-email` retirada y `data-linkml` eliminado (orden del operador,
2026-11-15). El resto vive en
[`tasks/decisions-skills-repertoire.md`](decisions-skills-repertoire.md) con
opciones y recomendación: frontera `plan-continue`/`project-machineroom`, tipos,
estrictez del validador, tamaño del catálogo, keywords/triggers, prefijos de
dominio, `disable-model-invocation` y versionado.

---

## Next Steps

1. **Operator approval** of this spec (Phase 1)
2. **Plan** generation (Phase 2) — this document serves as both spec and plan
3. **Task breakdown** (Phase 3) — detailed in Section 3 above
4. **Implementation** (Phase 4) — execute tasks in dependency order with role routing
5. **Validation & closure** (Phase 5) — `make validate-skills`, harness doctor, publish
