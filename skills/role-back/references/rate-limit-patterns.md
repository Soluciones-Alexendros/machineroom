# Rate Limit Patterns

## Overview

Protect public APIs, auth endpoints, webhooks from abuse. Fail closed or degrade gracefully.

## Algorithms

### Fixed Window

```python
# Simple, memory-efficient, but allows bursts at boundaries
async def check_limit(key: str, limit: int, window: int) -> bool:
    now = int(time.time() / window)
    bucket = f"ratelimit:{key}:{now}"
    count = await cache.incr(bucket)
    if count == 1:
        await cache.expire(bucket, window)
    return count <= limit
```

### Sliding Window Log

```python
# Precise, stores timestamps, higher memory
async def check_limit_sliding(key: str, limit: int, window: int) -> bool:
    now = time.time()
    cutoff = now - window
    pipe = cache.pipeline()
    pipe.zremrangebyscore(key, 0, cutoff)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window)
    results = await pipe.execute()
    return results[1] < limit
```

### Token Bucket

```python
# Smooth rate limiting, allows bursts up to capacity
async def check_token_bucket(key: str, rate: float, capacity: int) -> bool:
    now = time.time()
    bucket_key = f"tokenbucket:{key}"
    data = await cache.hmget(bucket_key, "tokens", "last")
    tokens = float(data[0]) if data[0] else capacity
    last = float(data[1]) if data[1] else now

    # Refill
    tokens = min(capacity, tokens + (now - last) * rate)
    allowed = tokens >= 1
    if allowed:
        tokens -= 1

    await cache.hmset(bucket_key, {"tokens": tokens, "last": now})
    await cache.expire(bucket_key, int(capacity / rate) + 1)
    return allowed
```

## Common Configurations

| Endpoint | Algorithm | Limit | Window |
|----------|-----------|-------|--------|
| Auth login | Fixed window | 5 | 15 min |
| API general | Token bucket | 100/s | 1000 burst |
| Webhook receive | Sliding window | 1000 | 1 min |
| Password reset | Fixed window | 3 | 1 hour |

## Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 97
X-RateLimit-Reset: 1699999999
Retry-After: 45
```

## Fail-Closed vs Degrade

| Strategy | When | Implementation |
|----------|------|----------------|
| Fail closed | Auth, payments, admin | Return 429 immediately |
| Degrade gracefully | Search, analytics, non-critical | Return cached/stale data, log warning |

## Providers

- Upstash Redis (built-in rate limit)
- Cloudflare Rate Limiting (edge)
- NGINX limit_req (reverse proxy)
- Envoy rate limit service (gRPC)

## References

- [Rate limiting algorithms](https://konghq.com/blog/engineering/rate-limiting-algorithms/)
- [Upstash rate limiting](https://docs.upstash.com/redis/features/ratelimit)