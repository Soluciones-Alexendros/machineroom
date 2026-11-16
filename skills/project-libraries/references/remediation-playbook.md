# Remediation Playbook

## Overview

Actionable remediation steps for dependency vulnerabilities, malware, and supply-chain issues detected by the SCA pipeline.

## Vulnerability Remediation

### By Severity

| Severity | SLA | Action |
|----------|-----|--------|
| Critical (CVSS ≥ 9.0) | 24h | Immediate patch or isolation |
| High (CVSS 7.0–8.9) | 72h | Patch or mitigating control |
| Medium (CVSS 4.0–6.9) | 30d | Scheduled patch |
| Low (CVSS < 4.0) | 90d | Next routine update |

### Remediation Strategies

| Strategy | When | Effort | Risk |
|----------|------|--------|------|
| Direct upgrade | Patch/minor version available | Low | Low |
| Major upgrade | Breaking changes required | High | Medium |
| Patch backport | No upstream fix | Medium | Low |
| Workaround | No fix available | Low | Medium |
| Isolation | Cannot upgrade | Medium | Low |
| Accept risk | Business justification | None | Documented |

### Automation

```bash
# Auto-create PR for dependabot/renovate
renovate --dry-run --platform=github

# Generate SBOM for audit trail
syft packages dir:. -o spdx-json > sbom.spdx.json
```

## Malware / Typosquatting Response

1. **Quarantine**: Remove from lockfile immediately
2. **Investigate**: Check install timestamps, network calls
3. **Rotate**: Any credentials exposed during install window
4. **Report**: Submit to ecosystem security team (npm security, PyPI security, etc.)
5. **Replace**: Find legitimate alternative

## Supply Chain Hardening

| Control | Implementation |
|---------|----------------|
| Pin exact versions | `package-lock.json`, `Cargo.lock`, `go.sum` |
| Verify signatures | `npm audit signatures`, `cargo verify-project` |
| Reproducible builds | `npm ci`, `cargo build --locked` |
| Private registry | Nexus, Artifactory, GitHub Packages |
| Allowlist | `renovate.json` packageRules |

## Runbook: CVE Response

```
1. DETECT: SCA scan reports CVE-XXXX-XXXX in dep@version
2. ASSESS: Check CVSS, exploit availability, reachability
3. DECIDE: Upgrade / workaround / accept / isolate
4. ACT: Create PR, test, merge, deploy
5. VERIFY: Re-scan confirms remediation
6. DOCUMENT: Update security log, SBOM
```

## References

- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — SA-12 Supply Chain Protection
- [SLSA Framework](https://slsa.dev/) — Supply Chain Levels for Software Artifacts
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [Renovate Documentation](https://docs.renovatebot.com/)