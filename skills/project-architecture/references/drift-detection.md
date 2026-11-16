# Drift Detection

## Overview

Detecting unintended architectural changes between baseline and current state.

## Types of Drift

| Type | Description | Detection Method |
|------|-------------|------------------|
| Dependency drift | New/removed dependencies | Compare `package-lock.json`, `Cargo.lock`, `go.sum` |
| Structural drift | New modules, circular deps | madge, pydeps diff |
| API drift | Changed public interfaces | OpenAPI diff, protoc compatibility |
| Config drift | Changed build/runtime config | git diff on config files |
| Test drift | Coverage decrease | Coverage threshold gates |

## Baseline Management

### Create Baseline

```bash
# Store current state as baseline
mkdir -p .arch/baseline/$(date +%Y%m%d)
madge --json src/ > .arch/baseline/$(date +%Y%m%d)/deps.json
radon cc src/ -a > .arch/baseline/$(date +%Y%m%d)/complexity.txt
coverage run -m pytest && coverage json -o .arch/baseline/$(date +%Y%m%d)/coverage.json
```

### Compare Against Baseline

```bash
# Dependency drift
madge --json src/ | jq -s '.[0] * .[1] | .[] | select(.imports != .[1].imports)' .arch/baseline/latest/deps.json -

# Complexity drift
radon cc src/ -a | diff -u .arch/baseline/latest/complexity.txt -
```

## CI Integration

```yaml
# .github/workflows/arch-drift.yml
name: Architecture Drift
on: [pull_request]
jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Check dependency drift
        run: |
          BASE=$(git merge-base origin/main HEAD)
          git show $BASE:package-lock.json > /tmp/base-lock.json
          # compare with current package-lock.json
```

## Automated Remediation

| Drift Type | Auto-fix | Manual Required |
|------------|----------|-----------------|
| Dependency version | `npm update` / `cargo upgrade` | Breaking changes |
| Unused dependency | `depcheck` / `cargo machete` | False positives |
| Circular dependency | Refactor | Always |
| Coverage drop | Add tests | Always |

## References

- [ArchUnit](https://www.archunit.org/) — Architecture tests for Java
- [Dependency Cruiser](https://github.com/sverweij/dependency-cruiser) — JS/TS architecture rules
- [Architecture Decision Records](https://adr.github.io/) — Documenting baseline decisions