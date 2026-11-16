# Lighthouse Guide

## Overview

Lighthouse 12: running, interpreting, and integrating into CI.

## Running Lighthouse

### CLI

```bash
# Basic run
npx lighthouse https://example.com --output html --output-path ./report.html

# CI mode (fail on thresholds)
npx lighthouse https://example.com \
  --budget-path=./budget.json \
  --output=json \
  --output-path=./lighthouse-results.json \
  --chrome-flags="--headless --no-sandbox"

# Multiple URLs
npx lighthouse https://example.com https://example.com/about \
  --output=json --output-path=./results.json
```

### CI Integration (GitHub Actions)

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse
on: [pull_request]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - name: Build
        run: npm run build
      - name: Start preview
        run: npm run preview -- --port 4173 &
      - name: Wait for server
        run: sleep 5
      - name: Run Lighthouse
        run: |
          npx lighthouse http://localhost:4173 \
            --budget-path=./lighthouse-budget.json \
            --output=json \
            --output-path=./lighthouse-results.json \
            --chrome-flags="--headless --no-sandbox"
      - name: Upload report
        uses: actions/upload-artifact@v4
        with: { name: lighthouse-report, path: lighthouse-results.json }
```

### Budget File

```json
// lighthouse-budget.json
{
  "ci": {
    "collect": {
      "numberOfRuns": 3,
      "startServerCommand": "npm run preview -- --port 4173",
      "url": ["http://localhost:4173"]
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "categories:best-practices": ["error", { "minScore": 0.9 }],
        "categories:seo": ["warn", { "minScore": 0.8 }],
        "first-contentful-paint": ["error", { "maxNumericValue": 1800 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "interactive": ["error", { "maxNumericValue": 3000 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["warn", { "maxNumericValue": 200 }]
      }
    }
  }
}
```

## Interpreting Results

### Categories

| Category | Weight | Key Metrics |
|----------|--------|-------------|
| Performance | 100% | LCP, INP, CLS, TBT, FCP, SI |
| Accessibility | 100% | Contrast, labels, ARIA, focus |
| Best Practices | 100% | HTTPS, CSP, cookies, console errors |
| SEO | 100% | Meta tags, structured data, mobile |
| PWA | 100% | Service worker, manifest, offline |

### Performance Metrics Detail

| Metric | Weight | Good | Needs Work | Poor |
|--------|--------|------|------------|------|
| LCP | 25% | < 2.5s | 2.5–4s | > 4s |
| INP (was FID) | 25% | < 200ms | 200–500ms | > 500ms |
| CLS | 25% | < 0.1 | 0.1–0.25 | > 0.25 |
| TBT | 10% | < 200ms | 200–600ms | > 600ms |
| FCP | 10% | < 1.8s | 1.8–3s | > 3s |
| Speed Index | 10% | < 3.4s | 3.4–5.8s | > 5.8s |

## Debugging Workflow

1. **Run Lighthouse** → Get report
2. **Open DevTools Performance** → Record page load
3. **Identify Long Tasks** → Flame chart → Bottom-up view
4. **Check Network** → Waterfall → Blocking resources
5. **Apply Fix** → Re-run Lighthouse → Verify

## Common Fixes by Category

### Performance

| Issue | Fix |
|-------|-----|
| Unused JS | Code split, dynamic import, remove dead code |
| Render-blocking CSS | Inline critical, defer non-critical |
| Large images | WebP/AVIF, responsive images, preload LCP |
| Third-party scripts | Defer, self-host, remove unused |
| Main thread blocking | Web workers, code split, `scheduler.yield()` |

### Accessibility

| Issue | Fix |
|-------|-----|
| Low contrast | Adjust colors to 4.5:1 (AA) |
| Missing labels | `<label for="id">`, `aria-label` |
| No focus visible | `:focus-visible { outline: 2px solid }` |
| ARIA misuse | Use semantic HTML first |

### Best Practices

| Issue | Fix |
|-------|-----|
| No CSP | Add `Content-Security-Policy` header |
| Console errors | Fix JS errors, remove debug logs |
| Insecure cookies | `Secure`, `SameSite=Lax/Strict` |
| Deprecated APIs | Update to modern equivalents |

## References

- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [Lighthouse Scoring](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/)
- [Performance Budgets](https://web.dev/articles/performance-budgets-101)
- [Web Vitals Library](https://github.com/GoogleChrome/web-vitals)