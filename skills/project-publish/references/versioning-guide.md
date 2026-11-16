# Versioning Guide

## Overview

Semantic Versioning (SemVer 2.0.0) applied to machineroom and its skills.

## Version Format

`MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

| Component | When to Increment | Example |
|-----------|-------------------|---------|
| MAJOR | Incompatible API/instruction changes | 1.0.0 → 2.0.0 |
| MINOR | New compatible capabilities | 1.0.0 → 1.1.0 |
| PATCH | Compatible fixes, docs, typos | 1.0.0 → 1.0.1 |

## Skill Versioning

Each skill in `skills/<name>/SKILL.md` has independent `metadata.version`.

| Change Type | Skill Version | Repo Version |
|-------------|---------------|--------------|
| Skill instruction change | Minor (if compatible) / Major (if breaking) | Minor |
| Skill metadata fix (author, keywords) | Patch | Patch |
| New skill added | N/A | Minor |
| Skill removed | N/A | Minor (with `Removed` in CHANGELOG) |
| Tool/registry change | N/A | Minor |
| Pipeline phase change | N/A | Major |

## Version Bump Process

```bash
# Auto-bump skill versions on PR
python3 tools/version/bump.py --check --auto --base origin/main

# Dry-run all skills
python3 tools/version/bump.py --type patch --all --dry-run

# Bump specific skill
python3 tools/version/bump.py --type minor --skills project-publish
```

## Release Tags

- Format: `vMAJOR.MINOR.PATCH` (e.g., `v8.1.0`)
- Created by `tools/version/cut_tag.py` on merge to main
- Only when `package.json` version > last tag
- CHANGELOG.md section required

## Pre-release Versions

- Alpha: `v8.1.0-alpha.1` — early development
- Beta: `v8.1.0-beta.1` — feature complete, testing
- RC: `v8.1.0-rc.1` — release candidate

## References

- [SemVer 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- ADR-0010: SemVer contrato estándar