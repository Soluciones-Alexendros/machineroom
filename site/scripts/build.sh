#!/usr/bin/env bash
# One build: pin, catalog, static pages, search index, then the output checks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

bash site/scripts/sync-portal.sh
uv run --project tools python3 tools/site_catalog/generate.py

cd site
npm ci
npx astro build
npx pagefind --site dist --glob "{docs,skills}/**/*.html"
cp vercel.json dist/vercel.json

cd "$ROOT"
uv run --project tools python3 tools/site_catalog/check_dist.py
