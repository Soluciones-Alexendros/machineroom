# CWV Deep Dive

## Overview

Core Web Vitals: LCP, INP, CLS. Measuring, debugging, and optimizing each metric.

## LCP (Largest Contentful Paint)

### What It Measures

Time from page start to render of largest content element (image, text block, video poster).

### Good Threshold

< 2.5s (75th percentile)

### Common Causes of Poor LCP

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Slow server response | TTFB > 800ms | CDN, caching, edge functions |
| Render-blocking CSS/JS | Waterfall shows blocking | Inline critical CSS, defer non-critical |
| Large images | LCP element is image | Preload, compress, next-gen formats |
| Client-side rendering | LCP after JS hydration | SSR/SSG, streaming |

### Optimization Checklist

- [ ] Preload LCP image: `<link rel="preload" as="image" href="/hero.webp">`
- [ ] Inline critical CSS, defer rest
- [ ] Use `fetchpriority="high"` on LCP image
- [ ] Reduce TTFB: edge caching, streaming HTML
- [ ] Eliminate render-blocking resources
- [ ] Compress images: WebP/AVIF, responsive sizes

## INP (Interaction to Next Paint)

### What It Measures

Latency of all click/tap/keyboard interactions; reports the 98th percentile.

### Good Threshold

< 200ms (75th percentile)

### Common Causes of Poor INP

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Long tasks (>50ms) | Performance profiler | Code splitting, web workers |
| Expensive event handlers | Flame chart | Debounce, throttle, defer |
| Layout thrashing | Forced sync layout | Batch reads/writes, `requestAnimationFrame` |
| Hydration blocking | TTI >> FCP | Partial hydration, islands |

### Optimization Checklist

- [ ] Break up long tasks: `scheduler.yield()`, `setTimeout(0)`
- [ ] Defer non-critical JS: `defer`, `type=module`, dynamic import
- [ ] Use web workers for heavy computation
- [ ] Avoid forced synchronous layout
- [ ] Virtualize long lists
- [ ] Memoize expensive calculations

## CLS (Cumulative Layout Shift)

### What It Measures

Sum of all unexpected layout shifts during page load.

### Good Threshold

< 0.1 (75th percentile)

### Common Causes of Poor CLS

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Images without dimensions | DevTools shows shift | Add `width`/`height` or `aspect-ratio` |
| Ads/embeds without space | Shift after load | Reserve space with `min-height` |
| Fonts loading (FOUT/FOIT) | Text shifts | `font-display: optional`, preload fonts |
| Dynamic content injection | Content pushes down | Reserve space, `transform` animations |

### Optimization Checklist

- [ ] All images have `width`/`height` or CSS `aspect-ratio`
- [ ] Reserve space for ads/embeds: `min-height`
- [ ] Preload critical fonts: `<link rel="preload" as="font" crossorigin href="/font.woff2">`
- [ ] Use `font-display: optional` or `swap` with size-adjust
- [ ] Animate with `transform`/`opacity` only
- [ ] Avoid inserting content above viewport

## Measurement

### Lab Tools

```bash
# Lighthouse CI
npx lighthouse-ci autorun

# Web Vitals extension (Chrome)
# PageSpeed Insights API
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com"
```

### Field Data (RUM)

```javascript
// web-vitals library
import { onCLS, onINP, onLCP } from 'web-vitals';

onCLS(console.log);
onINP(console.log);
onLCP(console.log);

// Send to analytics
function sendToAnalytics(metric) {
  fetch('/analytics', { method: 'POST', body: JSON.stringify(metric) });
}
```

## References

- [web.dev CWV](https://web.dev/vitals/)
- [Chrome UX Report](https://developer.chrome.com/docs/crux/)
- [Lighthouse Scoring](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/)