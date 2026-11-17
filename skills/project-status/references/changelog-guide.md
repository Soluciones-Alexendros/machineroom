# Changelog Guide

## Overview

Keep a Changelog 1.1.0 format for all versioned components.

## Format

```markdown
# Changelog

## [Unreleased]

### Added
- New capabilities

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes

## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

## Section Rules

| Section | Required | Description |
|---------|----------|-------------|
| Added | Yes (if applicable) | New user-facing capabilities |
| Changed | Yes (if applicable) | Modifications to existing behavior |
| Deprecated | If applicable | Features scheduled for removal |
| Removed | If applicable | Removed features (reference migration) |
| Fixed | If applicable | Bug fixes with issue/PR refs |
| Security | If applicable | CVE fixes, vulnerability mitigations |

## Entry Style

- **Imperative mood**: "Add X", "Fix Y", not "Added X", "Fixed Y"
- **User-facing**: Describe impact, not implementation
- **Reference**: Link PR/issue: `(#123)`, `[@user](url)`
- **Scope**: Prefix with component: `skills:`, `tools:`, `docs:`, `ci:`

### Good Examples

```markdown
### Added
- skills: repo health board moved into `project-status`

### Changed
- tools: `workspace-router` phase routing now uses `project.yaml` schema v2

### Fixed
- ci: `validate-skills` job no longer fails on warnings (#67)

### Security
- deps: upgrade `yaml` to 0.2.5 (CVE-2024-XXXX)
```

### Bad Examples

```markdown
### Added
- Added new skill (vague, no reference)

### Changed
- Refactored internal code (not user-facing)

### Fixed
- Fixed bug (no context, no reference)
```

## Release Process

1. `tools/version/cut_tag.py --extract-notes vX.Y.Z` generates notes from CHANGELOG
2. Release workflow creates GitHub Release with notes
3. CHANGELOG `[Unreleased]` section moves to versioned section
4. New `[Unreleased]` section added at top

## Skill Changelogs

Each skill may maintain its own changelog in `skills/<name>/CHANGELOG.md` following the same format. The root CHANGELOG aggregates significant changes.

## References

- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
- [Common Changelog anti-patterns](https://keepachangelog.com/en/1.1.0/#anti-patterns)
- ADR-0010: SemVer contrato estándar