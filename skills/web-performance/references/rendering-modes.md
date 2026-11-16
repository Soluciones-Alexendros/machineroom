# Rendering Modes

## Overview

SSR, SSG, ISR, Islands — when to use each and performance implications.

## Mode Comparison

| Mode | HTML Generation | TTFB | Caching | Dynamic Data | SEO |
|------|-----------------|------|---------|--------------|-----|
| SSR (Server-Side Rendering) | Per request | Medium | CDN (short) | ✓ Real-time | ✓ |
| SSG (Static Site Generation) | Build time | Fast | CDN (long) | ✗ Build-time only | ✓ |
| ISR (Incremental Static Regeneration) | Build + revalidate | Fast | CDN + revalidate | ✓ Periodic | ✓ |
| Islands (Partial Hydration) | Build + interactive parts | Fast | CDN | ✓ Per island | ✓ |
| CSR (Client-Side Rendering) | Client | Fast (shell) | CDN | ✓ Runtime | ✗ (needs prerender) |

## When to Use Each

| Use Case | Recommended Mode |
|----------|------------------|
| Marketing pages, docs, blogs | SSG |
| E-commerce product pages | ISR (revalidate on stock/price change) |
| Dashboards, user-specific content | SSR |
| Interactive widgets in static page | Islands |
| Highly dynamic apps (real-time) | SSR + WebSockets |

## Implementation Patterns

### Next.js

```tsx
// SSG (default)
export async function generateStaticParams() {
  const posts = await getPosts();
  return posts.map(p => ({ slug: p.slug }));
}

export default async function Page({ params }) {
  const post = await getPost(params.slug);
  return <Article post={post} />;
}

// ISR
export const revalidate = 3600; // seconds
export default async function Page({ params }) { ... }

// SSR (force dynamic)
export const dynamic = 'force-dynamic';
export default async function Page({ params }) { ... }
```

### Astro (Islands by Default)

```astro
---
// Static by default
const posts = await getPosts();
---

{posts.map(post => <Article post={post} />)}

<!-- Interactive island -->
<InteractiveCounter client:load />
<CommentForm client:visible />
```

### Remix (SSR with Loaders)

```tsx
// Always SSR
export const loader = async ({ params }) => {
  const data = await db.query(...);
  return json(data);
};

export default function Page() {
  const data = useLoaderData();
  return <UI data={data} />;
}
```

## Performance Implications

| Metric | SSR | SSG | ISR | Islands |
|--------|-----|-----|-----|---------|
| TTFB | Higher (server work) | Lowest | Low (cached) | Low (static shell) |
| LCP | Depends on server | Best | Best | Good |
| INP | Hydration cost | No hydration | No hydration | Partial hydration |
| CLS | Server renders full | No shift | No shift | Minimal |

## Caching Strategy

```http
# SSG / ISR (cached)
Cache-Control: public, max-age=0, must-revalidate, s-maxage=3600

# SSR (dynamic)
Cache-Control: private, no-cache, no-store, must-revalidate

# Static assets
Cache-Control: public, max-age=31536000, immutable
```

## References

- [Next.js Rendering](https://nextjs.org/docs/app/building-your-application/rendering)
- [Astro Islands](https://docs.astro.build/en/concepts/islands/)
- [Remix Data Loading](https://remix.run/docs/en/main/data/loaders)
- [ISR Explained](https://vercel.com/docs/concepts/next.js/incremental-static-regeneration)