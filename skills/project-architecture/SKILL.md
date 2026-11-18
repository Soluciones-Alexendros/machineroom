---
name: project-architecture
description:
  Code architecture verification and analysis. Use when analyzing code
  structure, dependencies, architectural drift, or refactoring opportunities. Not
  for security code review (→ web-owasp) nor SCA/CVE dependency audits (→ role-linux);
  minor implementation without architecture analysis uses role-* skills.
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "7.1.3"
  domain: project
  type: audit
  language: en
  keywords:
    - project-architecture
    - project
    - architecture
    - dependency-mapping
    - drift
    - metrics
compatibility: cursor, pi, opencode
allowed-tools: Read, Grep, Glob
---

# Project Architecture

## Overview

Code architecture verification and analysis. Use when analyzing code structure,
dependencies, architectural drift, or refactoring opportunities. Use when the
operator requests architectural analysis, dependency mapping, or code health assessment.

## When to Use

- When analyzing code structure
- For dependency mapping
- For architectural drift analysis
- When code health assessment is requested

## Not for

not for security code review (→ web-owasp) nor SCA/CVE dependency audits (→ role-linux); minor implementation without architecture analysis uses role-* skills (→ role-clean-code for refactoring outcome).

- Security code review (use web-owasp)
- Minor implementation changes without architectural analysis (use the matching role-* skill; dependency advisories → role-linux)

## Architectural Analysis

| Aspect       | Tool                    | Objective                    |
| ------------ | ----------------------- | ---------------------------- |
| Dependencies | madge, dependency-crawl | Map module relationships     |
| Structure    | eslint, stylelint       | Check code style conventions |
| Metrics      | source-metrics, madric  | Quantitative analysis        |
| Drift        | custom scripts          | Detect unintended changes    |
