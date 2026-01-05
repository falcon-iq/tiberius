# TanStack Router - Implementation Guide

## Quick Facts

- **Router**: TanStack Router with file-based routing
- **History**: Hash history (`#/path` URLs for Electron compatibility)
- **Route location**: `src/renderer/routes/`
- **Generated types**: `src/renderer/types/routeTree.gen.ts` (COMMITTED, not gitignored)

## Packages Installed

```json
"@tanstack/react-router": "^1.144.0"
"@tanstack/router-devtools": "^1.144.0"
"@tanstack/router-plugin": "^1.145.2"
```

## Configuration

### vite.renderer.config.mts
```typescript
import { tanstackRouter } from '@tanstack/router-plugin/vite';

export default defineConfig({
  plugins: [
    tanstackRouter({
      routesDirectory: './src/renderer/routes',
      generatedRouteTree: './src/renderer/types/routeTree.gen.ts',
    }),
    // ... other plugins
  ],
});
```

### tsconfig.json
**Required**: `"strictNullChecks": true` (TanStack Router requirement)

### App.tsx
```typescript
import { createRouter, RouterProvider, createHashHistory } from '@tanstack/react-router';
import { routeTree } from '../types/routeTree.gen';

const hashHistory = createHashHistory();
const router = createRouter({ routeTree, history: hashHistory });

// Type registration
declare module '@tanstack/react-router' {
  interface Register { router: typeof router; }
}

const App = () => <RouterProvider router={router} />;
```

## File Structure

```
src/renderer/
├── routes/
│   ├── __root.tsx          # Root layout with <Outlet />
│   ├── index.tsx           # / route
│   ├── about.tsx           # /about route
│   └── users/$id.tsx       # /users/:id dynamic route
├── types/
│   └── routeTree.gen.ts    # Auto-generated, COMMIT THIS
└── app/
    └── App.tsx             # Router setup
```

## File-Based Routing Patterns

| File Path | URL | Dynamic |
|-----------|-----|---------|
| `index.tsx` | `/` | No |
| `about.tsx` | `/about` | No |
| `users/index.tsx` | `/users` | No |
| `users/$id.tsx` | `/users/:id` | Yes |
| `posts/$postId/comments.tsx` | `/posts/:postId/comments` | Yes |

## Creating Routes

### Basic Route
```tsx
// routes/profile.tsx
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/profile')({
  component: Profile,
});

function Profile() {
  return <div>Profile Page</div>;
}
```

### Dynamic Route
```tsx
// routes/users/$id.tsx
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/users/$id')({
  component: UserDetail,
});

function UserDetail() {
  const { id } = Route.useParams();
  return <div>User: {id}</div>;
}
```

### Root Layout
```tsx
// routes/__root.tsx
import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet /> {/* Child routes render here */}
      <TanStackRouterDevtools /> {/* Dev tools */}
    </>
  ),
});
```

## Navigation

### Link Component
```tsx
import { Link } from '@tanstack/react-router';

<Link to="/about">About</Link>
<Link to="/users/$id" params={{ id: '123' }}>User 123</Link>
```

### Programmatic
```tsx
import { useNavigate } from '@tanstack/react-router';

const navigate = useNavigate();
navigate({ to: '/about' });
navigate({ to: '/users/$id', params: { id: '123' } });
```

## Search Params

```tsx
// Route definition
export const Route = createFileRoute('/search')({
  validateSearch: (search: Record<string, unknown>) => ({
    query: search.query as string,
    page: Number(search.page ?? 1),
  }),
  component: SearchPage,
});

// Component usage
function SearchPage() {
  const { query, page } = Route.useSearch();
  return <div>Query: {query}, Page: {page}</div>;
}
```

## Important Notes

### Hash History
- URLs: `file:///path/index.html#/about`
- Required for Electron (no server needed)
- Works with `file://` protocol

### routeTree.gen.ts
- **DO commit to git** (types needed immediately after clone)
- Auto-regenerates on route file changes
- Never edit manually
- Located in `types/` for organization

### Type Safety
- Full TypeScript support for routes, params, search
- Autocomplete for route paths
- Compile-time route validation

### Dev Tools
- Floating button in dev mode (bottom corner)
- Inspect routes, params, navigation state
- Only appears in development

## Common Patterns

### Nested Routes
```
routes/
├── dashboard/
│   ├── index.tsx       # /dashboard
│   ├── profile.tsx     # /dashboard/profile
│   └── settings.tsx    # /dashboard/settings
```

### Layout with Navigation
```tsx
// routes/__root.tsx
export const Route = createRootRoute({
  component: () => (
    <>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
      </nav>
      <main><Outlet /></main>
    </>
  ),
});
```

### Active Link Styling
```tsx
<Link
  to="/about"
  activeProps={{ className: "font-bold text-primary" }}
>
  About
</Link>
```

## Key Commands

```bash
npm start          # Start dev server (auto-generates routes)
# Routes auto-regenerate on file save
```

## Troubleshooting

**Error: "strictNullChecks must be enabled"**
- Add `"strictNullChecks": true` to `tsconfig.json`

**Routes not found**
- Ensure file is in `src/renderer/routes/`
- Check route file exports `Route` correctly
- Restart dev server if needed

**TypeScript errors on import**
- Verify `routeTree.gen.ts` exists in `src/renderer/types/`
- Run dev server once to generate it
- Commit the file to version control

## Reference

- [TanStack Router Docs](https://tanstack.com/router)
- [File-Based Routing](https://tanstack.com/router/latest/docs/framework/react/guide/file-based-routing)
- [Hash History API](https://tanstack.com/router/latest/docs/framework/react/api/router/createHashHistoryFunction)
