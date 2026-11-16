# Metrics Guide

## Overview

Quantitative code health metrics for architectural assessment.

## Metrics Catalog

### Structural Metrics

| Metric | Description | Tool | Good Range |
|--------|-------------|------|------------|
| Lines of Code (LOC) | Total non-comment lines | cloc, tokei | < 500 per module |
| Cyclomatic Complexity | Decision points per function | radon, complexity | < 10 per function |
| Cognitive Complexity | Nesting + structural complexity | sonar, codeclimate | < 15 per function |
| Halstead Volume | Information content | halstead | Context-dependent |
| Maintainability Index | Composite (0-100) | radon, mi | > 70 |

### Architectural Metrics

| Metric | Description | Tool | Good Range |
|--------|-------------|------|------------|
| Afferent Coupling (Ca) | Incoming dependencies | madge, pydeps | < 20 |
| Efferent Coupling (Ce) | Outgoing dependencies | madge, pydeps | < 20 |
| Instability (I) | Ce / (Ca + Ce) | calculated | 0.2–0.8 |
| Abstractness (A) | Abstract / Total classes | calculated | > 0.5 |
| Distance from Main Sequence | \|A + I - 1\| | calculated | < 0.3 |

### Test Metrics

| Metric | Description | Tool | Good Range |
|--------|-------------|------|------------|
| Line Coverage | % lines executed | coverage.py, llvm-cov | > 80% |
| Branch Coverage | % branches taken | coverage.py | > 70% |
| Mutation Score | % mutants killed | mutmut, stryker | > 60% |

## Collection Pipeline

```bash
# Python
radon cc src/ -a -nc
radon mi src/
coverage run -m pytest && coverage report

# JavaScript
npx complexity-report src/
nyc npm test

# Rust
cargo tarpaulin --out Xml
```

## Thresholds by Language

| Language | Complexity | Coverage | MI |
|----------|------------|----------|-----|
| Python | < 10 | > 80% | > 70 |
| TypeScript | < 10 | > 80% | > 70 |
| Rust | < 15 | > 70% | N/A |
| Go | < 10 | > 70% | N/A |

## Reporting

Generate HTML report:

```bash
radon cc src/ -a -nc --html > complexity.html
radon mi src/ --html > maintainability.html
```

## References

- [radon documentation](https://radon.readthedocs.io/)
- [SonarQube metric definitions](https://docs.sonarqube.org/latest/user-guide/metric-definitions/)
- Martin Fowler, "Refactoring" — Code metrics chapter