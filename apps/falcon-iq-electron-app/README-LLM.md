# Amista - Technical Context for LLM Assistants

## Purpose

Context for LLM agents working with the Amista Electron application across sessions.

## Additional Context Files

For specific technology implementations:
- **`llm-artifacts/TAILWIND.md`** - Tailwind CSS v4 configuration, theme, and usage patterns
- **`llm-artifacts/ROUTING.md`** - TanStack Router setup, file-based routing, and navigation patterns

---

## Tech Stack

**Runtime:**
- Electron 39.2.7 (Chromium 142, Node.js 22.21.1)
- React 19.x with TypeScript
- TanStack Router (file-based, hash history)
- Tailwind CSS v4
- better-sqlite3 (local database)

**Build Tools:**
- Electron Forge 7.10.2 (packaging, distribution)
- Vite 5.4.21 (bundling, HMR)
- TypeScript 4.5.4

**Key Packages:**
- `@tanstack/react-router` - Routing with file-based routes
- `@tanstack/router-plugin` - Vite plugin for route generation
- `@vitejs/plugin-react` - React Fast Refresh
- `tailwindcss@^4.1.x` - Styling
- `vite-tsconfig-paths` - Path alias support
- `better-sqlite3` - SQLite database

---

## Project Structure

```
amista/
├── src/
│   ├── main/
│   │   ├── index.ts           # Main process (Node.js backend)
│   │   └── database.ts        # SQLite database operations
│   ├── preload/
│   │   └── preload.ts         # IPC bridge (exposes window.api)
│   └── renderer/
│       ├── index.tsx          # React entry point
│       ├── app/
│       │   └── App.tsx        # Router configuration
│       ├── routes/            # File-based routes (auto-discovered)
│       │   ├── __root.tsx     # Root layout with <Outlet />
│       │   ├── index.tsx      # Home (/)
│       │   ├── about.tsx      # /about
│       │   └── settings.tsx   # /settings
│       ├── types/
│       │   └── routeTree.gen.ts  # Auto-generated (COMMITTED)
│       ├── components/        # Reusable components
│       └── styles/
│           └── globals.css    # Tailwind + custom theme
├── llm-artifacts/             # Tech-specific docs
├── index.html                 # App shell
├── package.json
├── tsconfig.json
├── forge.config.ts            # Packaging config
└── vite.*.config.mts          # Build configs (3 files)
```

---

## Key Configuration

### Electron Architecture

**Multi-process:**
- **Main process** (`src/main/index.ts`) - Node.js, OS integration, window management, database operations
- **Renderer process** (`src/renderer/`) - Chromium, React UI, sandboxed
- **Preload script** (`src/preload/preload.ts`) - Secure IPC bridge via `window.api`

**Security:**
- Context isolation enabled
- No Node.js integration in renderer
- Fuses configured (ASAR integrity, cookie encryption, etc.)

### TypeScript (`tsconfig.json`)

**Critical settings:**
```json
{
  "compilerOptions": {
    "jsx": "react-jsx",              // Automatic JSX runtime
    "moduleResolution": "bundler",   // Required for Vite + ESM
    "strictNullChecks": true,        // Required by TanStack Router
    "baseUrl": ".",
    "paths": {
      "@styles/*": ["src/renderer/styles/*"]
    }
  }
}
```

**Path aliases:** Use `@styles/*` instead of relative imports (supported by `vite-tsconfig-paths` plugin).

### Routing (`src/renderer/app/App.tsx`)

```typescript
import { createRouter, RouterProvider, createHashHistory } from '@tanstack/react-router';
import { routeTree } from '../types/routeTree.gen';

const hashHistory = createHashHistory();  // Required for Electron
const router = createRouter({ routeTree, history: hashHistory });
```

**Hash history:** URLs use `#/path` format for `file://` protocol compatibility.

**Route generation:** Files in `src/renderer/routes/` auto-generate routes:
- `index.tsx` → `/`
- `about.tsx` → `/about`
- `users/$id.tsx` → `/users/:id`

**Generated types:** `src/renderer/types/routeTree.gen.ts` (committed to git for immediate type availability).

### Vite Configuration (`vite.renderer.config.mts`)

```typescript
import { tanstackRouter } from '@tanstack/router-plugin/vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [
    tailwindcss(),           // Tailwind v4
    tanstackRouter({         // Route generation
      routesDirectory: './src/renderer/routes',
      generatedRouteTree: './src/renderer/types/routeTree.gen.ts',
    }),
    react(),                 // Fast Refresh
    tsconfigPaths(),        // Path aliases
  ],
});
```

### Package.json

**Entry point:** `"main": ".vite/build/index.js"` (matches `src/main/index.ts` → `index.js` output)

**Scripts:**
- `npm start` - Development with HMR
- `npm run package` - Create distributable
- `npm run make` - Platform-specific installers

**Platform support:** Windows (Squirrel), macOS (ZIP), Linux (DEB, RPM)

---

## Implementation Status

**✅ Completed:**
- Electron + React + TypeScript + Vite setup
- TanStack Router with file-based routes + hash history
- Tailwind CSS v4 with custom theme
- TypeScript path aliases
- Security hardening (Fuses)
- Example routes (/, /about, /settings)
- Multi-platform distribution ready
- IPC communication layer (preload bridge + handlers)
- SQLite database (better-sqlite3) with CRUD operations

**❌ Not Implemented:**
- Native menus
- Auto-updates
- Testing infrastructure

---

## Project Conventions

### Routing
- Use `Link` from `@tanstack/react-router` (never `<a>` tags)
- Create routes by adding files to `src/renderer/routes/`
- Routes auto-generate on file save
- Hash history for Electron compatibility

### Styling
- Use Tailwind utility classes
- Custom theme in `globals.css`
- Design tokens: `background`, `foreground`, `primary`, etc.
- Dark mode supported (`.dark` class)

### File Organization
- Main process: `src/main/`
- Renderer: `src/renderer/`
- Routes: `src/renderer/routes/`
- Components: `src/renderer/components/`
- Types: `src/renderer/types/`

### Imports
- Use path aliases: `@styles/globals.css`
- Avoid relative imports for shared resources
- `vite-tsconfig-paths` plugin handles resolution

### IPC
- Database operations via `window.api` (getGithubUsers, addGithubUser, deleteGithubUser)
- Never expose Node.js APIs directly to renderer
- Use preload script + `contextBridge` pattern
- Main process handles all system operations

---

## Important Notes

### Electron-Specific
- **Process separation:** Main (Node.js) vs Renderer (Chromium)
- **Hash history required:** `file://` protocol needs `#/path` URLs
- **Hot reload:** Renderer auto-updates, main process needs restart
- **DevTools:** Auto-open in dev (line 30 in `main/index.ts`)

### Build System
- `.mts` extension for Vite configs (ESM modules)
- `.vite/` directory contains build output (gitignored)
- `out/` directory contains packaged apps (gitignored)
- Clear `.vite/` if "Cannot find module" errors occur

### TypeScript
- `strictNullChecks` required by TanStack Router
- `moduleResolution: "bundler"` required for Vite
- Auto-generated route tree must be committed

### Development
- Main process changes: Restart dev server
- Renderer changes: Auto-reload via HMR
- Route changes: Auto-regenerate types
- Tailwind changes: Auto-compile via Vite plugin

---

## Quick Reference

### Creating a Route

```tsx
// src/renderer/routes/profile.tsx
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/profile')({
  component: Profile,
});

function Profile() {
  return <div>Profile Page</div>;
}
```

### Navigation

```tsx
import { Link } from '@tanstack/react-router';

<Link to="/about">About</Link>
```

### Styling

```tsx
<div className="bg-background text-foreground p-4">
  <h1 className="text-2xl font-bold text-primary">Title</h1>
</div>
```

### IPC Pattern (Example: GitHub Users)

```typescript
// main/index.ts
ipcMain.handle('db:getGithubUsers', () => getGithubUsers());
ipcMain.handle('db:addGithubUser', (_event, username: string) => addGithubUser(username));

// preload/preload.ts
contextBridge.exposeInMainWorld('api', {
  getGithubUsers: () => ipcRenderer.invoke('db:getGithubUsers'),
  addGithubUser: (username: string) => ipcRenderer.invoke('db:addGithubUser', username),
});

// renderer component
const users = await window.api.getGithubUsers();
await window.api.addGithubUser('octocat');
```

---

## Common Issues

**"strictNullChecks must be enabled"**
→ TanStack Router requirement, already set in `tsconfig.json`

**Route not found**
→ Ensure file is in `src/renderer/routes/` and exports `Route`

**Cannot find module after restructuring**
→ `rm -rf .vite && npm start`

**Deprecated TanStackRouterVite**
→ Use `tanstackRouter` from `@tanstack/router-plugin/vite`

**Types not available**
→ Run `npm start` once to generate, file is committed

---

## Metadata

- **Name:** Amista
- **Version:** 1.0.0
- **Author:** Barry Steyn (bsteyn@linkedin.com)
- **License:** MIT

---

## For LLM Assistants

**Key principles:**
- Respect Electron process boundaries
- Use IPC for main ↔ renderer communication
- Never suggest Node.js APIs in renderer code
- Use TanStack Router `Link` for navigation
- Use Tailwind classes for styling
- Use path aliases for imports
- Maintain TypeScript type safety
- Consider cross-platform compatibility

**Refer to:**
- `llm-artifacts/ROUTING.md` for routing details
- `llm-artifacts/TAILWIND.md` for styling details

**Current state:** Infrastructure complete with IPC + SQLite, ready for UI development.
