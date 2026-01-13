# Tiberius Monorepo - LLM Assistant Guide

## Purpose

This document serves as the entry point for LLM assistants working with the Tiberius monorepo. It provides an overview of the project structure and references to detailed technical documentation.

---

## Repository Overview

Tiberius is an Nx monorepo containing multiple applications and shared libraries for project management.

**Key Technologies:**
- Nx workspace for monorepo management
- Electron + React + TypeScript for desktop applications
- Java + Spring for backend REST APIs
- Tailwind CSS v4 for styling
- TanStack Router for routing

---

## LLM Artifacts Documentation

The `llm-artifacts/` folder contains detailed technical documentation for LLM assistants:

### Root Level (`llm-artifacts/`)

- **[`TYPESCRIPT-PATHS.md`](llm-artifacts/TYPESCRIPT-PATHS.md)** - TypeScript path mappings and Tailwind CSS v4 configuration in Nx monorepos
  - How TypeScript paths work with `extends`
  - Tailwind v4 `@source` directive for shared libraries
  - Dark mode setup and common pitfalls
  - Critical for understanding shared library imports

### Electron App (`apps/falcon-iq-electron-app/llm-artifacts/`)

- **[`TAILWIND.md`](apps/falcon-iq-electron-app/llm-artifacts/TAILWIND.md)** - Tailwind CSS v4 configuration, theme system, and usage patterns
- **[`ROUTING.md`](apps/falcon-iq-electron-app/llm-artifacts/ROUTING.md)** - TanStack Router setup, file-based routing, and navigation patterns
- **[`LLM-DESIGN-GUIDE.md`](apps/falcon-iq-electron-app/llm-artifacts/LLM-DESIGN-GUIDE.md)** - Design principles and UI patterns

For comprehensive Electron app context, see [`apps/falcon-iq-electron-app/README-LLM.md`](apps/falcon-iq-electron-app/README-LLM.md).

---

## Quick Start for LLM Assistants

### When Working on...

**Shared Libraries (`libs/`):**
1. Read `llm-artifacts/TYPESCRIPT-PATHS.md` first
2. Understand TypeScript path mapping requirements
3. Know that Tailwind v4 requires `@source` directives in consuming apps
4. Remember: paths don't merge from parent tsconfigs

**Electron App (`apps/falcon-iq-electron-app/`):**
1. Read `apps/falcon-iq-electron-app/README-LLM.md` for full context
2. Reference `TAILWIND.md` for styling questions
3. Reference `ROUTING.md` for navigation questions
4. Reference `LLM-DESIGN-GUIDE.md` for UI/UX patterns

**REST API (`apps/falcon-iq-rest/`):**
1. Java + Spring Boot + Maven stack
2. See app-specific README for details

---

## Critical Concepts

### Code Organization Standards

**All TypeScript projects must follow these conventions:**

1. **Tests Folder:** All test files (`*.spec.ts`, `*.test.ts`) must be placed in a `tests/` folder
   - Example: `src/lib/tests/csv.spec.ts` (NOT `src/lib/csv.spec.ts`)
   - Tests use relative imports: `import { toCsv } from '../csv'`
   - The build excludes `src/**/tests/**` to keep compiled output clean

2. **Types Folder:** All TypeScript type definitions should be organized in a `types/` folder
   - Example: `src/lib/types/index.ts`
   - Export types from main index: `export type { MyType } from './lib/types'`
   - Keeps type definitions organized and discoverable

**Example Structure:**
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

### TypeScript Path Mappings
- Paths defined in `tsconfig.base.json` must be repeated in child configs if they define their own paths
- See `llm-artifacts/TYPESCRIPT-PATHS.md` for detailed explanation

### Tailwind CSS v4 in Monorepo
- Use `@source` directive in CSS files, NOT `tailwind.config.ts`
- `@source` must come AFTER `@theme` block
- Restart dev server after adding `@source`
- See `llm-artifacts/TYPESCRIPT-PATHS.md` for examples

### Nx Workspace
- Each project has a `project.json` defining targets
- Use `nx run <project>:<target>` to run commands
- Common targets: `dev`, `build`, `package`, `lint`, `test`

### Shared Libraries
- Located in `libs/` folder
- Must be explicitly configured in consuming apps
- TypeScript paths AND Tailwind scanning required

---

## Project Structure

```
tiberius/
├── apps/
│   ├── falcon-iq-electron-app/    # Electron desktop app
│   │   ├── llm-artifacts/         # App-specific LLM docs
│   │   └── README-LLM.md          # Full app context
│   └── falcon-iq-rest/            # Java REST API
├── libs/
│   └── shared/
│       └── ui/                    # Shared React components
├── llm-artifacts/                 # Monorepo-wide LLM docs
│   └── TYPESCRIPT-PATHS.md        # TypeScript & Tailwind config
├── README.md                      # Human-readable setup guide
└── README-LLM.md                  # This file
```

---

## When to Reference What

| Task | Read This First |
|------|----------------|
| Adding a new shared library | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Shared library not importing | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Tailwind classes not working | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Dark mode issues in modals | `llm-artifacts/TYPESCRIPT-PATHS.md` |
| Routing/navigation | `apps/falcon-iq-electron-app/llm-artifacts/ROUTING.md` |
| Styling/theming | `apps/falcon-iq-electron-app/llm-artifacts/TAILWIND.md` |
| UI patterns | `apps/falcon-iq-electron-app/llm-artifacts/LLM-DESIGN-GUIDE.md` |
| Full Electron context | `apps/falcon-iq-electron-app/README-LLM.md` |

---

## Common Patterns

### Importing from Shared Libraries

```typescript
// In tsconfig.json (if project has custom paths)
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["../../libs/shared/ui/src/index.ts"],  // Required!
      "@components/*": ["src/components/*"]  // Local paths
    }
  }
}
```

### Scanning Shared Libraries with Tailwind v4

```css
/* In app's globals.css - AFTER @theme block */
@import 'tailwindcss';

@theme inline {
  /* theme config */
}

/* Must come AFTER theme */
@source "../../../../../../libs/shared/ui/src";
```

### Using React Portals for Modals

```typescript
import { createPortal } from 'react-dom';

// Render to document.body to escape parent constraints
return createPortal(modalContent, document.body);
```

---

## Metadata

- **Repository:** Tiberius
- **Organization:** Nimrox AI
- **Technologies:** Nx, Electron, React, TypeScript, Java, Spring, Tailwind v4
- **Package Manager:** npm

---

## For LLM Assistants

**Before making changes:**
1. Check if working with shared libraries → read `TYPESCRIPT-PATHS.md`
2. Understand the monorepo structure and Nx conventions
3. Reference app-specific README-LLM.md files
4. Follow established patterns for imports and configuration

**Key principles:**
- Shared libraries require explicit configuration in consuming apps
- TypeScript paths don't merge - must be duplicated
- Tailwind v4 uses `@source` directives, not config files
- Always restart dev server after configuration changes

**Current state:** Modal system with React portals working, dark mode support, shared UI library established.
