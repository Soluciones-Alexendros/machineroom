# State Management

## Overview

Client state patterns: derived state over duplicated stores, one write path per concern.

## Patterns

### Single Source of Truth

```typescript
// ❌ Bad: duplicated store
const userStore = createStore({ user: null });
const profileStore = createStore({ profile: null });

// ✅ Good: derived state
const userStore = createStore({ user: null });
const profile = derived(userStore, ($u) => $u.user?.profile);
```

### Server State Synchronization

```typescript
// React Query / TanStack Query pattern
const { data: user } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => api.getUser(userId),
  staleTime: 5 * 60 * 1000,
});

// Mutations invalidate related queries
const mutation = useMutation({
  mutationFn: api.updateUser,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['user', userId] });
    queryClient.invalidateQueries({ queryKey: ['users'] }); // list
  },
});
```

### Optimistic Updates

```typescript
const mutation = useMutation({
  mutationFn: api.toggleLike,
  onMutate: async (newLike) => {
    await queryClient.cancelQueries({ queryKey: ['posts'] });
    const previous = queryClient.getQueryData(['posts']);
    queryClient.setQueryData(['posts'], (old) =>
      old.map(p => p.id === newLike.postId ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 } : p)
    );
    return { previous };
  },
  onError: (err, vars, context) => {
    queryClient.setQueryData(['posts'], context.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['posts'] });
  },
});
```

### URL as State

```typescript
// Sync filters/sort/pagination to URL
const [filters, setFilters] = useSearchParams();

const handleFilterChange = (key: string, value: string) => {
  const next = new URLSearchParams(filters);
  if (value) next.set(key, value);
  else next.delete(key);
  setFilters(next); // Triggers re-render, refetch via queryKey
};

// Query key includes URL params
const { data } = useQuery({
  queryKey: ['items', filters.toString()],
  queryFn: () => api.listItems(Object.fromEntries(filters)),
});
```

## Empty / Loading / Error States

```tsx
function UserList() {
  const { data, isLoading, isError, error } = useQuery({ queryKey: ['users'], queryFn: fetchUsers });

  if (isLoading) return <Skeleton count={5} />;
  if (isError) return <ErrorMessage error={error} onRetry={() => refetch()} />;
  if (!data?.length) return <EmptyState message="No users found" action={<Button onClick={createUser}>Add User</Button>} />;

  return <UserTable users={data} />;
}
```

## References

- [TanStack Query](https://tanstack.com/query/latest)
- [React Server Components](https://react.dev/learn/server-components)
- [State Management in React](https://react.dev/learn/managing-state)