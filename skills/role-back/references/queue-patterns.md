# Queue Patterns

## Overview

Async work, cron, fan-out using queue/bus patterns. At-least-once delivery; handlers must be idempotent.

## Patterns

### Fire-and-Forget Job

```python
# Enqueue
await queue.enqueue("email:send", {"to": "user@example.com", "template": "welcome"})

# Handler (idempotent by design)
async def handle_email_send(payload: dict):
    await email.send(payload["to"], payload["template"])
```

### Scheduled/Cron Job

```python
# Enqueue with delay
await queue.enqueue_in(timedelta(hours=24), "cleanup:expired", {"days": 30})

# Or use cron trigger
queue.cron("0 2 * * *", "cleanup:expired", {"days": 30})
```

### Fan-Out / Broadcast

```python
# Single event → multiple handlers
await queue.publish("user:created", {"user_id": "123", "email": "..."})

# Handlers registered separately:
# - email:welcome
# - analytics:track
# - billing:provision
```

### Delayed Retry with Backoff

```python
# Handler with retry
async def handle_with_retry(payload: dict, attempt: int = 1):
    try:
        await do_work(payload)
    except TransientError as e:
        if attempt < 3:
            delay = 2 ** attempt * 60  # 2m, 4m, 8m
            await queue.enqueue_in(timedelta(seconds=delay), "work:retry", {**payload, "attempt": attempt + 1})
        else:
            await dead_letter(payload, e)
```

## Idempotency Keys

```python
# Client provides key; server deduplicates
async def create_order(idempotency_key: str, order: OrderCreate) -> Order:
    existing = await cache.get(f"idempotent:{idempotency_key}")
    if existing:
        return Order.parse_raw(existing)
    order = await db.create(order)
    await cache.set(f"idempotent:{idempotency_key}", order.json(), ex=86400)
    return order
```

## Queue Providers

| Provider | Protocol | Features |
|----------|----------|----------|
| Upstash QStash | HTTP/REST | Serverless, scheduling, retries |
| Redis Streams | Redis protocol | Consumer groups, blocking |
| RabbitMQ | AMQP | Complex routing, DLX |
| SQS | AWS API | Managed, FIFO, DLQ |
| Kafka | Kafka protocol | High throughput, replay |

## References

- [Upstash QStash](https://docs.upstash.com/qstash)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/)