# Tiberius Project Context

This file provides essential context for Claude Code when working with the Tiberius repository. For app-specific context, see `apps/*/CLAUDE.md`. For detailed technical docs, see `llm-artifacts/` folder.

---

## Project Overview

**Tiberius** is an Nx monorepo for project management with two main applications:
- **falcon-iq-electron-app** - Desktop application (Electron + React + TypeScript)
- **falcon-iq-rest** - Backend REST API (Java + Spring + Maven)

**Tech Stack:**
- Nx 21.6.4 (monorepo orchestration)
- React 19 + TypeScript 5.9
- TanStack Router (file-based, hash history)
- TanStack Query (data fetching)
- Tailwind CSS v4
- Electron 39.2.7
- better-sqlite3 (SQLite database)
- Java 21 + Spring Boot + Maven

---

## Monorepo Structure

```
tiberius/
├── apps/
│   ├── falcon-iq-electron-app/    # Electron desktop app
│   └── falcon-iq-rest/            # Java REST API
├── libs/
│   ├── shared/                    # Shared libraries (UI components, utils, validations)
│   └── integrations/              # External integrations
├── llm-artifacts/                 # Detailed LLM documentation
└── README-LLM.md                  # Comprehensive LLM guide
```

---

## Essential Commands

**Setup:**
```bash
npm install              # Install dependencies
npm run prepare          # Setup Husky git hooks
```

**Development:**
```bash
nx run falcon-iq-electron-app:dev   # Start Electron app with HMR
nx run falcon-iq-rest:serve         # Start Java REST API
```

**Quality Checks:**
```bash
nx run-many --parallel -t lint test  # Run linting and tests
nx run <project>:<target>            # General Nx command pattern
```

**Commits:**
```bash
npm run commit           # Use Commitizen for conventional commits (REQUIRED)
```

---

## Critical Technical Concepts

### 1. TypeScript Paths Don't Merge
**The Problem:** When a child `tsconfig.json` defines `paths`, it completely overrides the parent's paths (no merging).

**The Solution:** If a project needs custom path mappings, you MUST duplicate all shared library paths from `tsconfig.base.json`:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["../../libs/shared/ui/src/index.ts"],  // Must repeat!
      "@components/*": ["src/components/*"]  // Local paths
    }
  }
}
```

See `llm-artifacts/TYPESCRIPT-PATHS.md` for details.

### 2. Tailwind v4 Uses `@source` Directives
**The Problem:** Tailwind v4 doesn't use `tailwind.config.ts` files. Classes in shared libraries won't generate CSS unless explicitly scanned.

**The Solution:** Use `@source` directives in your app's CSS file (AFTER `@theme` block):

```css
@import "tailwindcss";

@theme inline {
  /* theme config */
}

/* MUST come AFTER @theme */
@source "../../../../../../libs/shared/ui/src";
```

**Important:** Restart dev server after adding `@source` directives.

### 3. Three Environments (Never Abbreviated)
Always use full environment names:
- `development`
- `staging`
- `production`

Never use: `dev`, `stage`, `prod`

### 4. Tests in `tests/` Folders
All test files must be in `tests/` folders:
- ✅ `src/lib/tests/csv.spec.ts`
- ❌ `src/lib/csv.spec.ts`

Tests use relative imports: `import { toCsv } from '../csv'`

### 5. Conventional Commits Required
Use `npm run commit` (Commitizen) for all commits. Git hooks enforce conventional commit format.

---

## Code Organization Standards

**TypeScript projects follow these conventions:**

```
src/
├── lib/
│   ├── types/
│   │   └── index.ts          # Type definitions
│   ├── tests/
│   │   └── myfile.spec.ts    # Test files
│   └── myfile.ts             # Source code
└── index.ts                  # Main exports
```

**Key patterns:**
- Types in `types/` folder
- Tests in `tests/` folder
- Export types from main index: `export type { MyType } from './lib/types'`

---

## Architecture Overview

### Electron App (falcon-iq-electron-app)
**Multi-process architecture:**
- **Main process** (`src/main/`) - Node.js, OS integration, window management, SQLite database
- **Renderer process** (`src/renderer/`) - Chromium, React UI, sandboxed
- **Preload script** (`src/preload/`) - Secure IPC bridge via `window.api`

**Key features:**
- TanStack Router with file-based routes (hash history for `file://` protocol)
- TanStack Query for data fetching and caching
- Tailwind v4 for styling with custom theme
- SQLite database via better-sqlite3
- IPC communication for main ↔ renderer

### REST API (falcon-iq-rest)
- Java 21 + Spring Boot
- Maven build system
- RESTful endpoints

### Shared Libraries
**libs/shared/** - Common UI components, utilities, and validations
**libs/integrations/** - External service integrations

All shared libraries must be:
1. Added to `tsconfig.base.json` paths
2. Duplicated in consuming project's `tsconfig.json` if it has custom paths
3. Scanned by Tailwind using `@source` directive

---

## When to Reference What

| Task | Read This First |
|------|----------------|
| Adding a new shared library | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Shared library not importing | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Tailwind classes not working | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Dark mode issues | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Routing/navigation | `apps/falcon-iq-electron-app/llm-artifacts/ROUTING.md` |
| Styling/theming | `apps/falcon-iq-electron-app/llm-artifacts/TAILWIND.md` |
| UI patterns | `apps/falcon-iq-electron-app/llm-artifacts/LLM-DESIGN-GUIDE.md` |
| Electron app context | `apps/falcon-iq-electron-app/CLAUDE.md` |
| REST API context | `apps/falcon-iq-rest/CLAUDE.md` |
| Shared libraries | `libs/CLAUDE.md` |

---

## Common Gotchas

1. **TypeScript imports broken?** Check if you duplicated shared library paths in project's `tsconfig.json`
2. **Tailwind classes not styling?** Add `@source` directive for the library in app's CSS file, then restart dev server
3. **Tests not running?** Ensure test files are in `tests/` folder, not alongside source files
4. **Commit rejected?** Use `npm run commit` instead of `git commit` for conventional commit format
5. **Electron app navigation issues?** Use TanStack Router's `Link` component, never `<a>` tags

---

## Nx Workspace Patterns

**Run a target:**
```bash
nx run <project>:<target>
```

**Run multiple targets in parallel:**
```bash
nx run-many --parallel -t <target1> <target2>
```

**Common targets:**
- `dev` - Development server
- `build` - Production build
- `test` - Run tests
- `lint` - Run linter
- `package` - Package Electron app

---

## Key Files

- `tsconfig.base.json` - Root TypeScript configuration with shared library paths
- `package.json` - Root scripts and dependencies
- `llm-artifacts/TYPESCRIPT-PATHS.md` - Critical TypeScript and Tailwind configuration patterns
- `apps/falcon-iq-electron-app/CLAUDE.md` - Electron app context
- `apps/falcon-iq-rest/CLAUDE.md` - REST API context
- `libs/CLAUDE.md` - Shared libraries context

---

## Quick Start

1. Read this file for overview
2. For shared library work, read `libs/CLAUDE.md` and `llm-artifacts/TYPESCRIPT-PATHS.md`
3. For Electron app work, read `apps/falcon-iq-electron-app/CLAUDE.md`
4. For REST API work, read `apps/falcon-iq-rest/CLAUDE.md`
5. Reference specific `llm-artifacts/` files for technology-specific details
6. Use `npm run commit` for all commits

---

*For app-specific context, see CLAUDE.md files in apps/ and libs/ directories.*
