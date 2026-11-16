# Caching Strategies

## Overview

HTTP caching, CDN configuration, and browser cache strategies for performance.

## HTTP Cache Headers

### Cache-Control Directives

| Directive | Meaning | Use Case |
|-----------|---------|----------|
| `public` | Cacheable by any cache | Static assets, CDN |
| `private` | Cacheable by browser only | User-specific responses |
| `no-cache` | Must revalidate before use | Dynamic HTML |
| `no-store` | Never cache | Auth pages, sensitive data |
| `max-age=N` | Fresh for N seconds | Static assets, API |
| `s-maxage=N` | CDN max-age (overrides max-age) | CDN-specific TTL |
| `must-revalidate` | Revalidate when stale | Critical accuracy |
| `immutable` | Never changes, no revalidation | Versioned static assets |
| `stale-while-revalidate=N` | Serve stale while revalidating | Resilience |

### Common Patterns

```http
# Versioned static assets (JS, CSS, images, fonts)
Cache-Control: public, max-age=31536000, immutable

# Non-versioned static assets
Cache-Control: public, max-age=86400, stale-while-revalidate=604800

# API responses (cacheable)
Cache-Control: public, max-age=60, stale-while-revalidate=300

# Dynamic HTML (SSR)
Cache-Control: private, no-cache, no-store, must-revalidate

# API (non-cacheable)
Cache-Control: no-store, private
```

## CDN Configuration

### Cache Keys

```yaml
# Include query params that affect response
cache_key:
  - scheme
  - host
  - path
  - query: [format, v]  # version, format params
  - header: [Accept, Accept-Encoding]
  - cookie: []  # Don't cache by cookie
```

### Edge Rules

| Pattern | TTL | Stale-While-Revalidate |
|---------|-----|------------------------|
| `/static/*` | 1 year | 1 week |
| `/assets/*` | 1 year | 1 week |
| `/images/*` | 1 month | 1 week |
| `/api/v1/*` | 1 min | 5 min |
| `/*` (HTML) | 0 (no-store) | N/A |

### Purge Strategies

```bash
# Purge by tag (Fastly, Cloudflare, CloudFront)
curl -X PURGE -H "Fastly-Key: xxx" https://example.com/api/purge/tag/blog-post

# Purge by URL
curl -X PURGE https://example.com/blog/my-post
```

## Browser Cache

### Service Worker (Workbox)

```javascript
// sw.js
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';

// Static assets
registerRoute(
  ({ request }) => request.destination === 'script' || request.destination === 'style',
  new CacheFirst({ cacheName: 'static', plugins: [{ maxEntries: 50 }] })
);

// API
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({ cacheName: 'api', networkTimeoutSeconds: 3 })
);

// HTML (navigation)
registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({ cacheName: 'html', networkTimeoutSeconds: 3 })
);
```

### Cache Storage API

```javascript
// Manual cache management
const cache = await caches.open('my-cache-v1');
await cache.addAll(['/offline.html', '/styles.css']);

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).then((fetchResponse) => {
        const clone = fetchResponse.clone();
        caches.open('my-cache-v1').then((cache) => cache.put(event.request, clone));
        return fetchResponse;
      });
    })
  );
});
```

## Cache Invalidation

| Method | Trigger | Latency |
|--------|---------|---------|
| Tag-based purge | Deploy, content change | < 1s (Fastly/Cloudflare) |
| URL purge | Single asset | < 1s |
| TTL expiry | Time-based | Automatic |
| `stale-while-revalidate` | Background | Transparent |

## References

- [HTTP Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
- [Workbox](https://developer.chrome.com/docs/workbox/)
- [CDN Caching Best Practices](https://web.dev/articles/cache-control)