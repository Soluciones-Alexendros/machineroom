# Cache Patterns

## Overview

Redis-compatible cache/KV patterns for sessions, hot reads, feature flags.

## Patterns

### Session Cache

```python
# Key: session:{id}, TTL: 24h
# Stampede protection: SETNX + recompute
async def get_session(session_id: str) -> Session:
    key = f"session:{session_id}"
    data = await cache.get(key)
    if data:
        return Session.parse_raw(data)
    # Stampede: only one recomputes
    lock = await cache.set(f"lock:{key}", "1", nx=True, ex=10)
    if lock:
        data = await compute_session(session_id)
        await cache.set(key, data.json(), ex=86400)
        await cache.delete(f"lock:{key}")
        return data
    # Wait for other to complete
    await asyncio.sleep(0.1)
    return await get_session(session_id)
```

### Hot Read Cache

```python
# Key: resource:{type}:{id}, TTL: 5m–1h
# Invalidate on write
async def get_resource(resource_id: str) -> Resource:
    key = f"resource:widget:{resource_id}"
    cached = await cache.get(key)
    if cached:
        return Resource.parse_raw(cached)
    data = await db.fetch(resource_id)
    await cache.set(key, data.json(), ex=300)
    return data

async def update_resource(resource_id: str, patch: Patch) -> Resource:
    data = await db.update(resource_id, patch)
    await cache.delete(f"resource:widget:{resource_id}")  # Invalidate
    return data
```

### Feature Flags

```python
# Key: flag:{name}, TTL: 1h (short for quick rollout)
# Boolean or JSON config
async def is_enabled(flag: str, default: bool = False) -> bool:
    key = f"flag:{flag}"
    val = await cache.get(key)
    if val is None:
        return default
    return val.lower() == "true"
```

## TTL Guidelines

| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| Sessions | 24h | On logout / security event |
| Hot reads | 5m–1h | On write to source |
| Feature flags | 1h | On flag change |
| Computed aggregates | 15m–1h | On source change |
| Rate limit counters | Window size | Auto-expiry |

## Providers

- Upstash Redis (HTTP/REST, serverless)
- Redis Cloud / ElastiCache (TCP, persistent)
- Dragonfly (Redis-compatible, multi-threaded)
- Valkey (Redis fork, Linux Foundation)

## References

- [Upstash Redis docs](https://docs.upstash.com/redis)
- [Redis cache patterns](https://redis.io/docs/manual/patterns/)
- [Thundering herd problem](https://en.wikipedia.org/wiki/Thundering_herd_problem)