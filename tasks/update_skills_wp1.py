#!/usr/bin/env python3
import yaml, pathlib, sys

skills = sorted(pathlib.Path("skills").glob("*/SKILL.md"))

targets = {
    "local-maintenance": {
        "author": "Soluciones-Alexendros",
        "version": "8.0.1",
        "keywords": [
            "local-maintenance",
            "local",
            "maintenance",
            "linux",
            "health",
            "cleanup",
            "optimization",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": True,
        "desc": "Systematic Linux system maintenance with hygiene, updates, optimization and health KPIs. Use when auditing a Linux system, routine review, cleaning packages/caches/logs, orphan pacman/AUR, boot or resource optimization, OS health-check, or periodic maintenance of Arch/EndeavourOS/CachyOS/Debian/RHEL. Not for defensive security hardening or forensics (→ local-security).",
    },
    "local-security": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.2",
        "keywords": [
            "local-security",
            "local",
            "security",
            "hardening",
            "apparmor",
            "forensics",
            "cve",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": True,
        "desc": "Defensive Linux host security: posture, forensic record management, CVEs, sysctl/SSH hardening, AppArmor/SELinux, auditd and fail2ban. Use when the operator requests system security audit, host hardening or auth log review. Not for application code vulnerabilities (→ web-owasp) nor disk cleanup (→ local-maintenance).",
    },
    "plan-continue": {
        "author": "Soluciones-Alexendros",
        "version": "8.0.1",
        "keywords": [
            "plan-continue",
            "plan",
            "phase-router",
            "status-bump",
            "workspace",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Machineroom phase router: continue from roadmap or .machineroom status, scaffold project.yaml/status.yaml, and route DEFINE→SCHEMAS→IMPLEMENT→VALIDATE→INTEGRATE→STATUS. Use when asking where to start, plan mode, repo starting, or bringing a project up to date. Not for release close or version publication (→ project-publish); not for repo health board (→ project-audit).",
    },
    "plan-specification": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "plan-specification",
            "plan",
            "spec",
            "tasks",
            "acceptance-criteria",
            "capability-map",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Write a structured specification before writing any code, then decompose it into small verifiable tasks with explicit acceptance criteria. Use when starting a project or feature, when requirements are ambiguous, or when the change touches multiple modules. Not for single-line fixes or typo corrections (→ plan-validators for implementation).",
    },
    "plan-validators": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "plan-validators",
            "plan",
            "tdd",
            "test-coverage",
            "qa",
            "red-green",
            "prove-it",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Drive implementation and QA with integrated tests: red-green-refactor, bug reproduction, test strategy, quality metrics and behavior coverage for routes, functions and jobs. Use when implementing or changing behavior, writing or reviewing tests, or planning coverage. Not for pure configuration, documentation or static content changes, nor production host debugging (→ local-maintenance).",
    },
    "project-architecture": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "project-architecture",
            "project",
            "architecture",
            "dependency-mapping",
            "drift",
            "metrics",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob",
        "dmi": False,
        "desc": "Code architecture verification and analysis. Use when analyzing code structure, dependencies, architectural drift, or refactoring opportunities. Not for security code review (→ web-owasp) nor SCA/CVE dependency audits (→ project-libraries); minor implementation without architecture analysis uses role-* skills.",
    },
    "project-libraries": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "project-libraries",
            "project",
            "sca",
            "cve",
            "sbom",
            "supply-chain",
            "remediation",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob",
        "dmi": False,
        "desc": "Dependency audit (SCA/CVE): multi-language pipeline (npm/pip/cargo/go/maven/gradle/composer/gem) to detect vulnerabilities, malware, typosquatting, unused dependencies and outdated. Use when performing dependency audit, SCA, CVE scanning, supply chain security or SBOM generation. Not for code security review (→ web-owasp) nor web compliance audits (→ web-compliance).",
    },
    "project-machineroom": {
        "author": "Soluciones-Alexendros",
        "version": "2.0.1",
        "keywords": [
            "project-machineroom",
            "project",
            "self-audit",
            "canon",
            "harness",
            "control-plane",
            "doctor",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash",
        "dmi": False,
        "desc": "Audit and improve the machineroom system itself: canon map, control plane, harnesses, migrations and self-change protocol. Use when self-auditing machineroom, checking harness A/B/C drift, or planning an approved change to the pipeline. Not for generic architecture reviews (→ project-architecture); not for continuing an arbitrary product plan (→ plan-continue); not for publishing a release (→ project-publish). Not for product-repo health (→ project-audit).",
    },
    "project-publish": {
        "author": "Soluciones-Alexendros",
        "version": "8.0.1",
        "keywords": [
            "project-publish",
            "project",
            "release",
            "husky",
            "lint-staged",
            "ci-gate",
            "versioning",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": True,
        "desc": "Close a GitHub repository or work increment with local quality gates, version publication, CI/CD audit, Husky, lint-staged, tests, e2e, PR and merge-watch. Use when configuring or running pre-commit/pre-push gates, publishing versions, or closing a plan. Not for implementing product features, test authorship (→ plan-validators), or forges distinct from github.com.",
    },
    "role-back": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "role-back",
            "role",
            "backend",
            "api",
            "persistence",
            "jobs",
            "patterns",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Specialist role for backend application work: data at rest and in motion, routes, deployments, robustness and application security. Includes patterns for cache/KV, queues, rate limiting, object storage and search. Use when implementing APIs, persistence, jobs or server-side integrations. Not for host hardening (→ local-security), OWASP code audit (→ web-owasp), or dependency SCA (→ project-libraries).",
    },
    "role-clean-code": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "role-clean-code",
            "role",
            "clean-code",
            "refactor",
            "naming",
            "smells",
            "protocols",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Implements Clean Code principles to write expressive, maintainable software and refactor existing code safely in any language. Use when the operator asks for clean code, refactoring, meaningful names, smaller functions, fewer code smells, or cleanup of duplicated logic. Not for architecture-only assessments (→ project-architecture), test-suite audits (→ plan-validators), or security reviews (→ web-owasp).",
    },
    "role-design": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "role-design",
            "role",
            "design",
            "tokens",
            "tailwind",
            "components",
            "visual",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Specialist role for UI/UX and visual systems: intentional visual direction, typography, palette, motion, clean indented CSS, design tokens (DTCG/Style Dictionary), Tailwind v4 and reusable components. Use when designing or redesigning interfaces, building a design system, or polishing interaction. Not for a11y/SEO audits (→ web-compliance) nor frontend application logic (→ role-front).",
    },
    "role-front": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "role-front",
            "role",
            "frontend",
            "state",
            "routing",
            "forms",
            "contracts",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob, Bash, Write",
        "dmi": False,
        "desc": "Specialist role for frontend application work: UI stability, browser compatibility, state coherence across routes, and clear communication contracts between client and server. Use when implementing or fixing frontend features, client state, routing surfaces or interaction flows. Not for visual direction or design tokens (→ role-design), a11y/SEO audits (→ web-compliance), or performance audits (→ web-performance).",
    },
    "web-compliance": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "web-compliance",
            "web",
            "compliance",
            "wcag",
            "gdpr",
            "seo",
            "remediation",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob",
        "dmi": False,
        "desc": "Web compliance audit: accessibility (WCAG 2.2 AA / EN 301 549), legal (GDPR, Consent Mode v2, privacy policy, cookies), SEO on-page/off-page/SEM/analytics. PASS/FAIL/N/A matrix, weighted scoring, web compliance verdict POSITIVE/NEGATIVE/PARTIAL and remediation plan RICE. Use when auditing web compliance, dictating web compliance or remediation plan for SEO/accessibility/legal. Not for performance audits (→ web-performance) nor dependency scanning (→ project-libraries).",
    },
    "web-owasp": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "web-owasp",
            "web",
            "owasp",
            "injection",
            "xss",
            "authz",
            "crypto",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob",
        "dmi": False,
        "desc": "Code security review (OWASP): injection, XSS, authn/authz, cryptography, SSRF, secrets and misconfiguration. Use when performing security review, OWASP or searching for vulnerabilities in this code. Not for dependency CVEs (→ project-libraries) nor web compliance (→ web-compliance).",
    },
    "web-performance": {
        "author": "Soluciones-Alexendros",
        "version": "7.1.1",
        "keywords": [
            "web-performance",
            "web",
            "performance",
            "cwv",
            "lighthouse",
            "caching",
            "rendering",
        ],
        "compat": ["cursor", "pi"],
        "tools": "Read, Grep, Glob",
        "dmi": False,
        "desc": "Web performance audit: Core Web Vitals (LCP, INP, CLS), Lighthouse 12, TTFB/FCP, rendering (SSR/SSG/ISR/islands), caching HTTP/CDN, load optimization and technical frontend diagnosis. Use when performing performance audit, Lighthouse/CWV, load optimization, stability visual, caching or technical frontend diagnosis. Not for compliance audits (→ web-compliance) nor backend load testing.",
    },
}

for md in skills:
    text = md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    fm = yaml.safe_load(parts[1])
    name = fm["name"]

    if name not in targets:
        print(f"SKIP {name}: no target defined")
        continue

    t = targets[name]
    m = fm.get("metadata") or {}

    m["author"] = t["author"]
    m["version"] = t["version"]
    m["keywords"] = t["keywords"]
    fm["metadata"] = m

    fm["description"] = t["desc"]
    fm["compatibility"] = t["compat"]
    fm["allowed-tools"] = t["tools"]
    if t["dmi"]:
        fm["disable-model-invocation"] = True
    elif "disable-model-invocation" in fm:
        del fm["disable-model-invocation"]

    new_fm = yaml.dump(fm, sort_keys=False, allow_unicode=True).strip()
    new_text = f"---\n{new_fm}\n---\n{parts[2]}"
    md.write_text(new_text, encoding="utf-8")
    print(f"UPDATED {name}")

print("Done!")
