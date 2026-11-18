---
name: role-linux
description:
  "Linux application engineering role: app architecture, ABI/glibc compatibility, dependency
  and supply-chain audits, Debian/Ubuntu and Arch/Omarchy packaging, build, deployment and
  installation. Use when building, packaging, shipping or auditing a Linux application or its
  dependencies. Not for host maintenance (→ local-maintenance), host hardening (→ local-security),
  release closure (→ project-status) or generic architecture review (→ project-architecture)."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "8.0.0"
  domain: role
  type: atomic
  language: en
  keywords:
    - role-linux
    - role
    - packaging
    - debian
    - arch
    - dependencies
    - compatibility
  execution: role-linux
compatibility: cursor, pi, opencode
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Role Linux

## Overview

Specialist role for building Linux software that ships correctly. It covers the
whole artifact lifecycle — application architecture on Linux, compatibility and
ABI, dependency and supply-chain audits, Debian/Ubuntu and Arch/Omarchy
packaging, build, deployment and installation — and it audits what it ships
instead of assuming it works.

Boundary contract (read this before working):

- **This role builds the artifact and its package specs.** `project-status`
  closes and delivers (versioning, gates, CI/CD, publication).
- **This role works on the product artifact.** `local-maintenance` and
  `local-security` operate the host.
- **This role owns Linux-specific architecture** (packaging boundaries, systemd
  units, sandboxing, ABI surface). `project-architecture` owns stack-agnostic
  structure, drift and coupling analysis.

## When to Use

- Designing or reviewing the architecture of a Linux desktop or CLI application
- Checking ABI/glibc/runtime compatibility and target distro support
- Auditing dependencies: CVE/SCA, malware, typosquatting, unused or outdated
  packages, SBOM generation
- Writing or reviewing Debian packaging (`.deb`, apt, PPA, `debian/` control) or
  Arch packaging (`PKGBUILD`, `pacman`, AUR)
- Preparing the build, deployment or installation path of a Linux artifact

**When NOT to use:** host cleanup, orphan packages or journal maintenance
(→ local-maintenance); host hardening, auditd or AppArmor posture
(→ local-security); version tagging, changelog and release publication
(→ project-status); stack-agnostic architecture drift (→ project-architecture).

## Section A — Application architecture on Linux

Decide and document before packaging:

- **Process model:** single binary, daemon + client, tray/panel integration.
- **Isolation surface:** what the app reads/writes, whether it belongs in XDG
  dirs, whether it needs portals, sandbox or capabilities.
- **Runtime dependencies:** shared libraries vs vendored, glibc floor, kernel
  features, optional integrations that must degrade gracefully.
- **Desktop integration:** `.desktop` entry, icons, MIME types, autostart,
  systemd user units.
- **Distribution targets:** which distros and versions are supported; that list
  is a contract, not an aspiration.

Reference: [app-compatibility.md](references/app-compatibility.md).

## Section B — Dependencies and supply chain

Run the audit pipeline instead of trusting the lockfile:

1. **Recognise** the ecosystem(s) and the direct/transitive tree.
2. **Scan** for vulnerabilities (CVE), malware, typosquatting and risky install
   scripts.
3. **Cross-check** declared vs imported dependencies (unused / undeclared).
4. **Consolidate** into one report ordered by severity, each finding with
   evidence and a concrete action.
5. **Generate SBOM** when the artifact is distributed.

Ecosystems: npm, pip/uv, cargo, go, maven/gradle, composer, gem, plus distro
packages (`apt`, `pacman`).

References: [dependency-audit-pipeline.md](references/dependency-audit-pipeline.md),
[dependency-audit-ecosystems.md](references/dependency-audit-ecosystems.md),
[supply-chain.md](references/supply-chain.md),
[modern-threats.md](references/modern-threats.md),
[remediation-playbook.md](references/remediation-playbook.md).

## Section C — Packaging

### Debian / Ubuntu

Debian directory layout, `control` and `rules`, depends/recommends/suggests,
maintainer scripts (`postinst`, `prerm`), lintian, reproducibility, PPA
distribution and `apt` repository signing.

Reference: [debian-packaging.md](references/debian-packaging.md).

### Arch / Omarchy

`PKGBUILD` structure, `pkgname`/`pkgver`/`depends`/`optdepends`, `package()`,
`makepkg` and `namcap`, AUR submission rules, and how an Omarchy desktop app is
packaged so it appears in the launcher.

Reference: [arch-packaging.md](references/arch-packaging.md).

## Section D — Build, deployment and installation

- **Build:** reproducible flags, `DESTDIR` staging, artifact naming and
  provenance.
- **Deploy:** where files land (`/usr/bin`, `/usr/share`, `/usr/lib`), user vs
  system scope, upgrade and uninstall paths.
- **Install:** idempotent installer, verification step, rollback path, and a
  documented uninstall that leaves no owned residue.

Reference: [deployment-and-install.md](references/deployment-and-install.md).

## Rules

1. Never claim a distro, ABI or dependency is supported without evidence from a
   real build or a documented upstream guarantee.
2. A package that installs but cannot be uninstalled is not done.
3. Report `blocked` / `not_applicable` with a reason instead of promoting a
   missing check to pass.
4. Do not tag a release or publish from this role: hand off to
   `project-status`.

## Re-entry

Re-invoke this role before every packaging, compatibility, dependency or
deployment action; a previous invocation does not cover the next one. Re-evaluate
scope on each re-entry, then hand behavior to `role-front`/`role-back` and
closure to `project-status`.

## Related

- Host maintenance and cleanup → `local-maintenance`
- Host security posture → `local-security`
- Release closure and publication → `project-status`
- Stack-agnostic architecture → `project-architecture`
