# API Contracts

## Overview

Type-safe communication between client and server. Define request/response shapes at the boundary.

## Patterns

### Shared Types (TypeScript)

```typescript
// packages/shared/types.ts
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'member' | 'viewer';
  createdAt: string; // ISO 8601
}

export interface CreateUserRequest {
  email: string;
  name: string;
  password: string;
}

export interface CreateUserResponse {
  user: User;
  token: string;
}

export interface ApiError {
  status: number;
  message: string;
  fieldErrors?: Record<string, string>;
  code?: string;
}
```

### Client SDK Generation

```bash
# OpenAPI → TypeScript client
npx @hey-api/openapi-ts -i ./openapi.json -o ./src/api/client

# Or use orval
npx orval --config orval.config.ts
```

```typescript
// Generated client usage
import { createUser } from '@/api/client';

const { data } = await createUser({ email: 'x@y.com', name: 'X', password: 'secret' });
// data is fully typed as CreateUserResponse
```

### Request/Response Validation (Server)

```python
# FastAPI with Pydantic
from pydantic import BaseModel, EmailStr
from typing import Optional


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)


class CreateUserResponse(BaseModel):
    user: User
    token: str


@app.post("/users", response_model=CreateUserResponse)
async def create_user(request: CreateUserRequest):
    user = await service.create_user(request)
    return CreateUserResponse(user=user, token=generate_token(user.id))
```

### Contract Testing

```typescript
// Pact consumer test
import { Pact } from '@pact-foundation/pact';

const provider = new Pact({
  consumer: 'web-app',
  provider: 'api-service',
  port: 1234,
});

describe('User API', () => {
  beforeAll(() => provider.setup());
  afterAll(() => provider.finalize());

  it('creates a user', async () => {
    await provider.addInteraction({
      state: 'user does not exist',
      uponReceiving: 'a request to create user',
      withRequest: {
        method: 'POST',
        path: '/users',
        body: { email: 'x@y.com', name: 'X', password: 'secret' },
        headers: { 'Content-Type': 'application/json' },
      },
      willRespondWith: {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
        body: like({ user: like(User), token: like('string') }),
      },
    });

    const client = new ApiClient('http://localhost:1234');
    const result = await client.createUser({ email: 'x@y.com', name: 'X', password: 'secret' });
    expect(result.user.email).toBe('x@y.com');
  });
});
```

### Versioning Strategy

| Strategy | When | Example |
|----------|------|---------|
| URL path | Breaking changes | `/api/v1/users` → `/api/v2/users` |
| Header | Optional features | `Accept: application/vnd.api+json;version=2` |
| Query param | Experiments | `?version=beta` |

### Deprecation

```http
# Response headers
Deprecation: true
Sunset: Sat, 01 Jan 2025 00:00:00 GMT
Link: <https://api.example.com/v2/users>; rel="successor-version"
```

## References

- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Pact Contract Testing](https://docs.pact.io/)
- [API Versioning Best Practices](https://cloud.google.com/apis/design/versioning)