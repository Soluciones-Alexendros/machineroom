# Dependency Mapping

## Overview

Mapping module and package dependencies to detect architectural drift, circular dependencies, and coupling metrics.

## Tools

- **madge**: JavaScript/TypeScript dependency graphs
- **dependency-crawl**: Multi-language dependency analysis
- **pydeps**: Python module dependencies
- **cargo-deps**: Rust crate dependencies
- **go mod graph**: Go module dependencies

## Procedures

### Generate Dependency Graph

```bash
# JavaScript/TypeScript
npx madge --image graph.png src/

# Python
pydeps mypackage --show-deps --max-bacon=2

# Rust
cargo deps --format dot | dot -Tpng -o graph.png

# Go
go mod graph | grep -v test | head -100
```

### Detect Circular Dependencies

```bash
# JavaScript
npx madge --circular src/

# Python
pydeps mypackage --show-cycles
```

### Coupling Metrics

| Metric | Tool | Threshold |
|--------|------|-----------|
| Afferent coupling (Ca) | madge, pydeps | < 20 |
| Efferent coupling (Ce) | madge, pydeps | < 20 |
| Instability (I = Ce/(Ca+Ce)) | calculated | 0.2–0.8 |
| Abstractness (A) | calculated | > 0.5 for stable packages |

## Integration with CI

Add to `ci.yml`:

```yaml
- name: Check dependency cycles
  run: |
    npx madge --circular src/ || exit 1
    pydeps src --show-cycles || exit 1
```

## References

- [madge documentation](https://github.com/pahen/madge)
- [pydeps documentation](https://github.com/thebjorn/pydeps)
- Martin Fowler, "Refactoring: Improving the Design of Existing Code" — Chapter on package principles