# Test Patterns

## Overview

Common test patterns for unit, integration, and E2E tests.

## Patterns

### AAA (Arrange-Act-Assert)

```python
def test_user_can_login():
    # Arrange
    user = create_user(email="test@example.com", password="secret")
    client = TestClient(app)

    # Act
    response = client.post("/login", json={"email": "test@example.com", "password": "secret"})

    # Assert
    assert response.status_code == 200
    assert "token" in response.json()
```

### Given-When-Then (BDD)

```python
def test_order_completion():
    # Given
    order = create_order(status="pending")
    payment_gateway = MockPaymentGateway()

    # When
    result = complete_order(order.id, payment_gateway)

    # Then
    assert result.status == "completed"
    assert payment_gateway.charged == order.total
    assert order.completed_at is not None
```

### Test Data Builders

```python
class UserBuilder:
    def __init__(self):
        self.data = {"email": "test@example.com", "name": "Test User", "role": "member"}

    def with_email(self, email: str) -> "UserBuilder":
        self.data["email"] = email
        return self

    def as_admin(self) -> "UserBuilder":
        self.data["role"] = "admin"
        return self

    def build(self) -> User:
        return create_user(**self.data)

# Usage
admin = UserBuilder().as_admin().with_email("admin@example.com").build()
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("", False),
    ("a", True),
    ("ab", True),
    ("a" * 101, False),  # max length
])
def test_name_validation(input, expected):
    assert validate_name(input) == expected
```

### Fixtures for Isolation

```python
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def test_user(db_session):
    user = create_user(db_session, email="test@example.com")
    yield user
    db_session.delete(user)
    db_session.commit()
```

### Async Test Patterns

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_service.process(data)
    assert result.status == "done"

# For async generators
async def test_streaming():
    chunks = []
    async for chunk in stream_data():
        chunks.append(chunk)
    assert len(chunks) > 0
```

### Contract Tests (Pact)

```python
# Consumer side
def test_consumer_gets_user():
    with Pact(consumer="web", provider="api") as pact:
        pact.given("user exists")
         .upon_receiving("a request for user")
         .with_request("GET", "/users/123")
         .will_respond_with(200, body=Like(UserSchema))

        client = ApiClient(pact.uri)
        user = client.get_user(123)
        assert user.id == 123
```

## References

- [pytest documentation](https://docs.pytest.org/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Pact Contract Testing](https://docs.pact.io/)
- [Property-based Testing](https://hypothesis.readthedocs.io/)