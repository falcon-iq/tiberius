# Falcon IQ Electron App Context

Essential context for working with the Falcon IQ Electron desktop application. For monorepo-wide context, see `/CLAUDE.md`. For detailed technical docs, see `llm-artifacts/` folder.

---

## Tech Stack

- **Electron 39.2.7** (Chromium 142, Node.js 22.21.1)
- **React 19** with TypeScript 5.9
- **TanStack Router** (file-based, hash history)
- **TanStack Query** (data fetching, caching)
- **Tailwind CSS v4** (utility-first styling)
- **better-sqlite3** (local SQLite database)
- **Vite 5.4.21** (bundling, HMR)

---

## Project Structure

```
falcon-iq-electron-app/
├── src/
│   ├── main/
│   │   ├── index.ts           # Main process (Node.js backend)
│   │   └── database.ts        # SQLite database operations
│   ├── preload/
│   │   └── preload.ts         # IPC bridge (window.api)
│   └── renderer/
│       ├── index.tsx          # React entry point
│       ├── app/App.tsx        # Router configuration
│       ├── routes/            # File-based routes
│       │   ├── __root.tsx     # Root layout with <Outlet />
│       │   └── index.tsx      # Home route (/)
│       ├── components/        # Reusable components
│       └── styles/
│           └── globals.css    # Tailwind + theme config
├── llm-artifacts/             # Detailed technical docs
│   ├── TAILWIND.md           # Styling patterns
│   ├── ROUTING.md            # Navigation patterns
│   └── LLM-DESIGN-GUIDE.md   # UI/UX principles
└── forge.config.ts           # Electron packaging config
```

---

## Essential Commands

**Development:**
```bash
nx run falcon-iq-electron-app:dev    # Start with HMR
```

**Build & Package:**
```bash
nx run falcon-iq-electron-app:build    # Build for production
nx run falcon-iq-electron-app:package  # Create distributable
```

**Quality Checks:**
```bash
nx run falcon-iq-electron-app:lint     # Run ESLint
nx run falcon-iq-electron-app:test     # Run tests
```

---

## Electron Architecture

### Multi-Process Model

**Main Process** (`src/main/index.ts`)
- Node.js environment
- Window management
- OS integration
- SQLite database operations
- IPC handler registration

**Renderer Process** (`src/renderer/`)
- Chromium environment
- React UI (sandboxed)
- NO Node.js access
- Uses `window.api` for IPC

**Preload Script** (`src/preload/preload.ts`)
- Secure IPC bridge
- Exposes `window.api` to renderer
- Uses `contextBridge` for security

### Security

- Context isolation enabled
- No Node.js integration in renderer
- All system operations via IPC
- Fuses configured (ASAR integrity, cookie encryption)

---

## Routing with TanStack Router

### File-Based Routes

Files in `src/renderer/routes/` auto-generate routes:
- `index.tsx` → `/`
- `about.tsx` → `/about`
- `users/$id.tsx` → `/users/:id`
- `__root.tsx` → Root layout (required)

### Hash History (Required for Electron)

```typescript
// src/renderer/app/App.tsx
import { createHashHistory } from '@tanstack/react-router';

const hashHistory = createHashHistory();  // URLs: #/path
const router = createRouter({ routeTree, history: hashHistory });
```

**Why hash history?** `file://` protocol requires `#/path` format.

### Creating a Route

```tsx
// src/renderer/routes/settings.tsx
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/settings')({
  component: Settings,
});

function Settings() {
  return <div>Settings Page</div>;
}
```

### Navigation

```tsx
import { Link } from '@tanstack/react-router';

// ✅ Correct
<Link to="/about">About</Link>

// ❌ Never use <a> tags
<a href="#/about">About</a>
```

**See `llm-artifacts/ROUTING.md` for detailed patterns.**

---

## Styling with Tailwind v4

### Theme Configuration

All theme config is in `src/renderer/styles/globals.css` (NO `tailwind.config.ts`):

```css
@import "tailwindcss";
@import "tw-animate-css";

/* Theme defined in CSS */
@theme inline {
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.15 0 0);
  --color-primary: oklch(0.45 0.18 264);
}

/* Dark mode variant */
@custom-variant dark (&:is(.dark *));
```

### Scanning Shared Libraries

If using shared UI libraries, add `@source` directive AFTER `@theme`:

```css
@theme inline {
  /* ... */
}

/* MUST come AFTER @theme */
@source "../../../../../../libs/shared/ui/src";
```

**Important:** Restart dev server after adding `@source`.

### Usage

```tsx
<div className="bg-background text-foreground p-4">
  <h1 className="text-2xl font-bold text-primary">Title</h1>
</div>
```

**See `llm-artifacts/TAILWIND.md` for theme system and patterns.**

---

## IPC Communication

### Pattern

**1. Main Process** (handles requests):
```typescript
// src/main/index.ts
ipcMain.handle('db:getUsers', () => getUsers());
ipcMain.handle('db:addUser', (_event, name: string) => addUser(name));
```

**2. Preload Script** (exposes API):
```typescript
// src/preload/preload.ts
contextBridge.exposeInMainWorld('api', {
  getUsers: () => ipcRenderer.invoke('db:getUsers'),
  addUser: (name: string) => ipcRenderer.invoke('db:addUser', name),
});
```

**3. Renderer** (uses API):
```typescript
// src/renderer/components/UserList.tsx
const users = await window.api.getUsers();
await window.api.addUser('John');
```

**Never expose Node.js APIs directly to renderer!**

---

## TypeScript Configuration

### Path Aliases

**If this project defines custom paths**, you MUST duplicate shared library paths from `tsconfig.base.json`:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["../../libs/shared/ui/src/index.ts"],  // Must repeat!
      "@styles/*": ["src/renderer/styles/*"]  // Local paths
    }
  }
}
```

**Why?** TypeScript paths don't merge with `extends`.

**See `/llm-artifacts/TYPESCRIPT-PATHS.md` for details.**

---

## Data Fetching with TanStack Query

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Query
const { data, isLoading } = useQuery({
  queryKey: ['users'],
  queryFn: () => window.api.getUsers(),
});

// Mutation with cache invalidation
const queryClient = useQueryClient();
const mutation = useMutation({
  mutationFn: (name: string) => window.api.addUser(name),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['users'] });
  },
});
```

---

## Common Patterns

### Modal with Portal

```tsx
import { createPortal } from 'react-dom';

function Modal({ children }: { children: React.ReactNode }) {
  return createPortal(
    <div className="fixed inset-0 bg-black/50">
      <div className="bg-background p-4">{children}</div>
    </div>,
    document.body  // Escape parent constraints
  );
}
```

### Dark Mode Support

```tsx
// Add/remove .dark class on <html>
document.documentElement.classList.toggle('dark');

// Tailwind classes work automatically
<div className="bg-background dark:bg-gray-900">
```

---

## Development Notes

### Hot Reload

- **Renderer changes** → Auto-reload via HMR
- **Main process changes** → Restart dev server
- **Route changes** → Auto-regenerate types
- **Tailwind changes** → Auto-compile

### Build Output

- `.vite/` - Build output (gitignored)
- `out/` - Packaged apps (gitignored)

**If build errors occur:** `rm -rf .vite && nx run falcon-iq-electron-app:dev`

### Route Types

`src/renderer/types/routeTree.gen.ts` is auto-generated and committed to git for immediate type availability.

---

## Critical Gotchas

1. **Must use hash history** - `file://` protocol requires `#/path` URLs
2. **Never use `<a>` tags** - Always use TanStack Router's `Link` component
3. **Main process changes need restart** - HMR only works for renderer
4. **Tailwind v4 uses CSS config** - No `tailwind.config.ts` file
5. **Shared library styles need `@source`** - And dev server restart
6. **IPC is the only bridge** - Never access Node.js APIs from renderer
7. **TypeScript paths don't merge** - Duplicate shared library paths if using custom paths

---

## File Organization Conventions

Follow monorepo standards (see `/CLAUDE.md`):
- Tests in `tests/` folder
- Types in `types/` folder
- Tests use relative imports

---

## Quick Reference

| Task | Read This |
|------|-----------|
| Routing patterns | `llm-artifacts/ROUTING.md` |
| Styling/theming | `llm-artifacts/TAILWIND.md` |
| UI patterns | `llm-artifacts/LLM-DESIGN-GUIDE.md` |
| TypeScript paths | `/llm-artifacts/TYPESCRIPT-PATHS.md` |
| Monorepo context | `/CLAUDE.md` |

---

*Current state: Infrastructure complete with IPC, SQLite, TanStack Router/Query, ready for feature development.*
