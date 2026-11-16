# Routing Patterns

## Overview

Client-side routing with URL synchronization, navigation guards, and route-level data fetching.

## Patterns

### Route-Level Data Fetching

```tsx
// Loader pattern (Remix/React Router v6.4+)
export const loader = async ({ params }: LoaderArgs) => {
  const [project, members] = await Promise.all([
    api.getProject(params.projectId),
    api.getMembers(params.projectId),
  ]);
  return { project, members };
};

export default function ProjectPage() {
  const { project, members } = useLoaderData<typeof loader>();
  return <ProjectView project={project} members={members} />;
}
```

### Nested Routes with Outlets

```tsx
// Parent route loads shared data
export const loader = async ({ params }) => {
  const org = await api.getOrg(params.orgId);
  return { org };
};

export default function OrgLayout() {
  const { org } = useLoaderData();
  return (
    <div>
      <OrgHeader org={org} />
      <Outlet /> {/* Child routes render here */}
    </div>
  );
}

// Child route
export const loader = async ({ params }) => {
  const project = await api.getProject(params.projectId);
  return { project };
};
```

### Navigation Guards

```tsx
// Before navigation
export const shouldRevalidate = ({ currentParams, nextParams }) => {
  return currentParams.projectId !== nextParams.projectId;
};

// Form dirty check
export const unstable_shouldReload = ({ submission }) => {
  return submission.formData.get('intent') === 'save';
};

// Auth guard (root layout)
export const loader = async ({ request }: LoaderArgs) => {
  const user = await getSession(request);
  if (!user) throw redirect('/login');
  return { user };
};
```

### Parallel vs Sequential Loading

```tsx
// Parallel (default in Remix v2+)
export const loader = async ({ params }) => {
  const [project, members, settings] = await Promise.all([
    api.getProject(params.id),
    api.getMembers(params.id),
    api.getSettings(params.id),
  ]);
  return { project, members, settings };
};

// Sequential (when dependency exists)
export const loader = async ({ params }) => {
  const project = await api.getProject(params.id);
  const members = await api.getMembers(project.id); // depends on project
  return { project, members };
};
```

### Client-Side Transitions

```tsx
<Link to="/projects/123" prefetch="intent" /> // Prefetch on hover
<Link to="/projects/123" prefetch="viewport" /> // Prefetch when visible
<Link to="/projects/123" reloadDocument /> // Full page reload
```

## URL State Synchronization

```typescript
// Filters in URL
const [filters, setFilters] = useSearchParams();

// Generate link with current filters + override
<Link to={`?${new URLSearchParams({...Object.fromEntries(filters), page: '2'})}`}>
  Page 2
</Link>
```

## References

- [React Router v6](https://reactrouter.com/en/main)
- [Remix Routing](https://remix.run/docs/en/main/routing)
- [TanStack Router](https://tanstack.com/router/latest)