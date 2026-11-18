# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Astro static site in `site/`. The visual world is the pinned commit of
alexendros.dev recorded in `site/portal.pin`. The canonical build is the `site`
job in CI. Preview uploads that output directory. Production is a separate
authorization.

## Users

Any public visitor. The repository Soluciones-Alexendros/machineroom is public.
No account and no credential.

## Product Purpose

Explain machineroom, show its default wiring, and give one install path plus
the public docs. Success means a visitor can read the product, open the install
guide, and follow a phase to a skill and its source without a private checkout.

## Positioning

The site is generated from the live repository. Skill text, phase order, tool
policy, dependencies and published docs come from the source files at build
time. It is not a second copy of the product.

## Operating Context

Visitors arrive on the public web. Operators install through the rendered
`docs/harness-setup.md`. Cursor and Pi are separate first steps in that guide.

## Capabilities and Constraints

- One install guide. The homepage links to it and to the default wiring. It
  does not repeat commands.
- Published docs are the explicit rows in `site/manifest.yaml`.
- No form and no analytics.
- Theme preference, once the preview confirms the script, is `localStorage` on
  this origin, key `theme`, values `alexlight` or `alexdark`.
- Production domain machineroom.alexendros.dev waits for a later authorization.

## Brand Commitments

The name is Machineroom. The visual world is alexendros.dev at the pinned
commit. Do not invent a second visual system. Interface language is Spanish.
Skill descriptions and English documents stay English.

## Evidence on Hand

Live sources: `README.md`, `skills/*/SKILL.md`, `tools/execution/registry.yaml`,
`tools/workspace-router/project_load.py`, `templates/harness/project.yaml`,
`package.json`, `tools/pyproject.toml`, and the docs named in the manifest.
Do not invent customers, benchmarks, or pricing.

## Product Principles

- The repository is the source of the page.
- One public install path.
- A declared policy is not an observed execution.
- Say what the site stores only after checking it.
- Ship the built directory, not a second build on the host.

## Accessibility & Inclusion

The pages work without JavaScript. Text and controls meet the contrast of the
pinned theme in both light and dark. The fixed header does not cover anchors.
