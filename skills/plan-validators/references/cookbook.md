# Test Cookbook

## Overview

Ready-to-use test recipes for common scenarios.

## Recipes

### 1. Database Transaction Rollback

```python
@pytest.fixture
def db():
    conn = get_connection()
    conn.begin()
    yield conn
    conn.rollback()
```

### 2. Time Travel (freezegun)

```python
from freezegun import freeze_time

@freeze_time("2024-01-15 12:00:00")
def test_expiry():
    token = create_token(expires_in=3600)
    assert token.expires_at == datetime(2024, 1, 15, 13, 0, 0)
```

### 3. Mock External API

```python
import responses

@responses.activate
def test_external_call():
    responses.add(responses.GET, "https://api.example.com/user/1",
                  json={"id": 1, "name": "Test"}, status=200)

    result = client.get_user(1)
    assert result.name == "Test"
```

### 4. Test File Upload

```python
def test_upload(client, tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("hello")

    with open(file, "rb") as f:
        response = client.post("/upload", files={"file": f})

    assert response.status_code == 201
```

### 5. Test WebSocket

```python
@pytest.mark.asyncio
async def test_websocket():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        await ws.send(json.dumps({"type": "ping"}))
        response = await ws.recv()
        assert json.loads(response)["type"] == "pong"
```

### 6. Test Background Job

```python
def test_background_job_enqueued():
    with patch("app.queue.enqueue") as mock_enqueue:
        response = client.post("/trigger-job", json={"data": "x"})
        assert response.status_code == 202
        mock_enqueue.assert_called_once_with("process_data", {"data": "x"})
```

### 7. Test Rate Limiting

```python
def test_rate_limit():
    for i in range(5):
        response = client.get("/api/resource")
        assert response.status_code == 200

    response = client.get("/api/resource")
    assert response.status_code == 429
    assert "Retry-After" in response.headers
```

### 8. Test Cache Behavior

```python
def test_cache_hit():
    # First call - miss
    result1 = service.get_data("key")
    assert result1.source == "db"

    # Second call - hit
    result2 = service.get_data("key")
    assert result2.source == "cache"
    assert result1.data == result2.data
```

### 9. Test Async Retry

```python
@pytest.mark.asyncio
async def test_retry_on_transient_failure():
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError()
        return "success"

    result = await retry(flaky, max_attempts=3, base_delay=0.01)
    assert result == "success"
    assert call_count == 3
```

### 10. Test Idempotency

```python
def test_idempotent_operation():
    key = "idem-123"

    # First call
    result1 = service.process(key, data={"x": 1})
    assert result1.id == "result-1"

    # Duplicate call with same key
    result2 = service.process(key, data={"x": 1})
    assert result2.id == "result-1"  # Same result
    assert service.call_count == 1   # Only executed once
```

## Quick Reference: Assertions

| Scenario | Assertion |
|----------|-----------|
| Exception raised | `with pytest.raises(ValueError): func()` |
| Async exception | `with pytest.raises(ValueError): await func()` |
| Floating point | `assert abs(a - b) < 0.001` |
| List contains | `assert item in items` |
| Dict subset | `assert expected.items() <= actual.items()` |
| Call count | `mock.assert_called_once()` |
| Call args | `mock.assert_called_with(arg1, arg2)` |
| Any call | `mock.assert_any_call(arg1)` |

## References

- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [responses library](https://github.com/getsentry/responses)
- [freezegun](https://github.com/spulec/freezegun)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)