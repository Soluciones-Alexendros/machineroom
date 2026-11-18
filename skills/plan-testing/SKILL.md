---
name: plan-testing
description:
  "Read the project as it stands, then produce and execute a complete integrated-test plan:
  every route, function, job, component and end-to-end flow covered by real, non-trivial tests with
  explicit expected behaviour. Use when planning or implementing test coverage, when a feature or
  bug fix needs proof, or when the suite must be brought to a professional standard. Not for
  writing the product spec (→ plan-specification), closing and releasing an increment
  (→ project-status) or production host debugging (→ local-maintenance)."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "8.0.0"
  domain: plan
  type: orchestrator
  language: en
  keywords:
    - plan-testing
    - plan
    - test-plan
    - integration-tests
    - coverage
    - red-green
    - quality-gates
  execution: plan-testing
compatibility: cursor, pi, opencode
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Plan Testing

## Overview

This skill does not start from a blank page and does not stop at one happy-path
assertion. It reads the project as it actually is, writes a complete
integrated-test plan grounded in professional references, and then executes it
with red-green-refactor until every route, function, job, component and critical
flow is proven by a test that would fail if the behaviour broke.

The output is a **test plan document plus executed tests**, not a coverage
number.

## When to Use

- Operator asks to plan or implement tests, raise quality, or "cover this"
- A feature, route, job or component lands without real proof
- A bug needs a reproduction that survives the fix
- The suite exists but asserts trivialities instead of behaviour

**When NOT to use:** writing the specification or task list
(→ plan-specification); closing an increment, tagging a release or cleaning
branches (→ project-status); debugging a production host (→ local-maintenance).

## Stage 1 — Read the project

Do not assume the stack or the commands. Discover:

1. **Toolchain:** language, build file (`package.json`, `pyproject.toml`,
   `Cargo.toml`, `go.mod`, `pom.xml`/`build.gradle`, `Gemfile`), package manager
   and lockfile.
2. **Test framework and runners:** checked-in wrappers (`./gradlew`, `./mvnw`,
   `make test`), focused-test versus full-suite commands, watch mode.
3. **Test layout and conventions:** directories, file naming, fixture and factory
   patterns, existing doubles.
4. **Documented commands:** README, CONTRIBUTING, Makefile, CI workflows. The CI
   command is the contract; a test that never runs in CI is documentation.
5. **What already exists:** count of tests per area, obvious gaps, duplicated or
   dead tests, flaky markers, disabled tests with no reason.

Record the inventory before writing anything.

## Stage 2 — Write the test plan

Produce `tasks/test-plan.md` (or the target the repository already uses) with
one row per surface:

| Surface           | Kind      | Cases                                                | Level              | Proof of break         |
| ----------------- | --------- | ---------------------------------------------------- | ------------------ | ---------------------- |
| `POST /api/tasks` | route     | create ok, validation error, authn, authz, conflict  | integration        | response shifts        |
| `createTask()`    | function  | normal, boundary, invalid input, persistence failure | unit + integration | return contract        |
| `reminder-job`    | job       | trigger, success, failure, retry, idempotency        | integration        | observable side effect |
| `TaskForm`        | component | render, validation, submit, error state, a11y roles  | component          | DOM/behaviour          |
| checkout          | e2e       | happy path, payment failure, resume                  | e2e                | user journey           |

Rules for the plan:

- **Every changed or new surface gets cases.** Mark `N/A` only with a reason.
- **Cover the failure paths**, not just the success path: empty, boundary,
  invalid, unauthorized, conflict, timeout.
- **State the level** (unit / integration / component / e2e) and justify e2e.
- **Name the assertion** that proves the behaviour — "it returns 200" is weaker
  than "it persists the entity and returns its id".
- **Reuse the repository's suite**: the new tests run with the standard command,
  not as a separate ad-hoc script.
- **Reference the standard**: cite the pattern source you are applying
  (pyramid, AAA, testing trophy, contract test) from `references/`.

Reference: [test-pyramid-and-sizes.md](references/test-pyramid-and-sizes.md),
[test-patterns.md](references/test-patterns.md),
[cookbook.md](references/cookbook.md).

## Stage 3 — Execute with red-green-refactor

For each row of the plan:

1. **RED:** write the test, run it, confirm it fails for the _expected_ reason.
   A test that passes immediately proves nothing.
2. **GREEN:** minimum code to pass. No speculative generality.
3. **REFACTOR:** with tests green, improve naming, extract duplication, remove
   dead code. Re-run after every step.

For a bug, the reproduction test comes first and must fail before the fix.

## Quality bar

A test earns its place when it fails if the behaviour breaks and survives a
refactor that preserves the behaviour.

- Assert observable behaviour, not private internals.
- One logical assertion per test; a descriptive name that states the guarantee.
- Deterministic: no wall-clock, network or ordering dependence without control.
- Isolated: no shared mutable state across tests; explicit setup.
- DAMP over DRY in tests: a little repetition beats an unreadable helper.
- No assertion-free tests, no `assert True`, no snapshot-of-everything, no
  testing third-party internals.
- Do not lower an existing coverage gate; do not add a coverage gate and call it
  done.

Reference: [writing-good-tests.md](references/writing-good-tests.md),
[rationalizations-and-flags.md](references/rationalizations-and-flags.md).

## Stage 4 — Report

Deliver, next to the tests:

- the plan with each row marked `covered` / `blocked` / `not_applicable` + reason;
- the commands used (focused loop and full suite);
- the residual gaps and why they remain open.

Never promote a skipped test, a missing dependency or a `not_run` suite to
`covered`.

## Browser and runtime proof

For code that runs in a browser, add runtime verification — DOM inspection,
console errors, network requests, accessibility snapshot — instead of trusting
the unit test alone. For complex bugs, write the reproduction without knowledge
of the fix, then verify it fails before implementing.

## Boundaries

- **Specify what to build** → `plan-specification`.
- **Close the increment and release** → `project-status`.
- **Security review** → `web-owasp`; **performance** → `web-performance`.

## References

- [test-pyramid-and-sizes.md](references/test-pyramid-and-sizes.md) — pyramid, levels, decision guide.
- [test-patterns.md](references/test-patterns.md) — AAA, Given-When-Then, doubles, fixtures.
- [writing-good-tests.md](references/writing-good-tests.md) — state-based tests, DAMP, naming, anti-patterns.
- [cookbook.md](references/cookbook.md) — worked cases per surface type.
- [rationalizations-and-flags.md](references/rationalizations-and-flags.md) — rationalizations, red flags, checklist.
