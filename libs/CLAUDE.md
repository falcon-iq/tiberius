# Shared Libraries Context

Essential context for working with shared libraries in the Tiberius monorepo. For monorepo-wide context, see `/CLAUDE.md`.

---

## Library Structure

```
libs/
├── shared/                    # Shared UI, utils, validations
│   ├── src/
│   │   ├── lib/
│   │   │   ├── types/        # Type definitions
│   │   │   ├── tests/        # Test files
│   │   │   └── *.ts          # Source code
│   │   └── index.ts          # Public exports
│   ├── project.json          # Nx configuration
│   ├── tsconfig.json         # TypeScript config
│   └── jest.config.js        # Test config
└── integrations/             # External service integrations
    └── ...
```

---

## Creating a New Shared Library

### 1. Generate Library with Nx

```bash
nx generate @nx/js:library my-lib --directory=libs/shared/my-lib
```

### 2. Add TypeScript Path to Root Config

**Edit `tsconfig.base.json`:**
```json
{
  "compilerOptions": {
    "paths": {
      "@libs/shared/my-lib": ["libs/shared/my-lib/src/index.ts"]
    }
  }
}
```

### 3. Update Consuming Projects

**CRITICAL:** If a consuming project defines its own `paths` in `tsconfig.json`, you MUST duplicate the new path:

```json
// apps/falcon-iq-electron-app/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "paths": {
      "@libs/shared/my-lib": ["../../libs/shared/my-lib/src/index.ts"],  // Add this!
      "@components/*": ["src/components/*"]  // Existing local paths
    }
  }
}
```

**Why?** TypeScript paths don't merge when using `extends`.

**See `/llm-artifacts/TYPESCRIPT-PATHS.md` for details.**

### 4. Add Tailwind Scanning (If Library Has Styles)

**If the library contains React components with Tailwind classes**, add `@source` directive to consuming app's CSS:

```css
/* apps/falcon-iq-electron-app/src/renderer/styles/globals.css */
@import "tailwindcss";

@theme inline {
  /* theme config */
}

/* MUST come AFTER @theme */
@source "../../../../../../libs/shared/my-lib/src";
```

**Important:** Restart dev server after adding `@source`.

---

## Using Shared Libraries

### Importing

```typescript
// In any app or library
import { MyComponent } from '@libs/shared/my-lib';
```

### Exporting from Libraries

**Always export from `index.ts`:**

```typescript
// libs/shared/my-lib/src/index.ts
export * from './lib/my-component';
export type { MyType } from './lib/types';
```

---

## Code Organization Standards

### File Structure

```
src/
├── lib/
│   ├── types/
│   │   └── index.ts          # Type definitions
│   ├── tests/
│   │   └── myfile.spec.ts    # Test files (MUST be in tests/ folder)
│   └── myfile.ts             # Source code
└── index.ts                  # Public exports
```

### Conventions

1. **Tests in `tests/` folder** - Required by build configuration
   - ✅ `src/lib/tests/csv.spec.ts`
   - ❌ `src/lib/csv.spec.ts`

2. **Types in `types/` folder** - Keeps type definitions organized
   - Export from main index: `export type { MyType } from './lib/types'`

3. **Use relative imports in tests:**
   ```typescript
   // src/lib/tests/csv.spec.ts
   import { toCsv } from '../csv';  // Relative to test file
   ```

---

## Checklist: Adding a New Shared Library

- [ ] Generate library with Nx
- [ ] Add path to `tsconfig.base.json`
- [ ] Update ALL consuming projects that define custom `paths`
- [ ] Add `@source` directive to consuming apps (if library has Tailwind styles)
- [ ] Restart dev servers
- [ ] Test imports work in consuming projects
- [ ] Verify Tailwind classes render (if applicable)

---

## Finding Projects That Need Updates

### Find all projects with custom TypeScript paths:

```bash
grep -r '"paths"' apps/*/tsconfig.json libs/*/tsconfig.json
```

### Find all Tailwind CSS entry files:

```bash
find . -name "globals.css" -o -name "styles.css" -not -path "*/node_modules/*"
```

---

## Common Issues

### TypeScript import errors

**Problem:** `Cannot find module '@libs/shared/my-lib'`

**Solutions:**
1. Check path is in `tsconfig.base.json`
2. If consuming project has custom `paths`, duplicate the path there
3. Restart TypeScript server in IDE

### Tailwind classes not styling

**Problem:** Components from shared library render but have no styles

**Solutions:**
1. Add `@source` directive to consuming app's CSS (AFTER `@theme` block)
2. Restart dev server
3. Verify path in `@source` is correct (relative to CSS file)

### Tests not found

**Problem:** Jest can't find test files

**Solution:** Ensure tests are in `tests/` folder, not alongside source files

---

## Critical Concepts

### 1. TypeScript Paths Don't Merge

When a child `tsconfig.json` defines `paths`, it completely overrides parent paths.

**Always duplicate shared library paths in projects with custom paths.**

### 2. Tailwind v4 Requires Explicit Scanning

Tailwind v4 doesn't use `tailwind.config.ts`. Libraries must be scanned with `@source` directive.

**Always add `@source` after `@theme` block and restart dev server.**

### 3. Tests Folder Convention

Build excludes `src/**/tests/**` to keep compiled output clean.

**Always put tests in `tests/` folder.**

---

## Examples

### Creating a UI Component Library

```bash
# 1. Generate library
nx generate @nx/js:library ui --directory=libs/shared/ui

# 2. Create component
# libs/shared/ui/src/lib/Button.tsx
export function Button({ children }: { children: React.ReactNode }) {
  return (
    <button className="bg-primary text-white px-4 py-2 rounded">
      {children}
    </button>
  );
}

# 3. Export from index
# libs/shared/ui/src/index.ts
export * from './lib/Button';

# 4. Update tsconfig.base.json
{
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["libs/shared/ui/src/index.ts"]
    }
  }
}

# 5. Update consuming app's tsconfig.json (if it has custom paths)
# apps/falcon-iq-electron-app/tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["../../libs/shared/ui/src/index.ts"],
      "@components/*": ["src/components/*"]
    }
  }
}

# 6. Update consuming app's CSS
# apps/falcon-iq-electron-app/src/renderer/styles/globals.css
@theme inline { /* ... */ }
@source "../../../../../../libs/shared/ui/src";

# 7. Restart dev server
nx run falcon-iq-electron-app:dev

# 8. Use in app
import { Button } from '@libs/shared/ui';
<Button>Click me</Button>
```

### Creating a Utility Library (No Styles)

```bash
# 1. Generate library
nx generate @nx/js:library utils --directory=libs/shared/utils

# 2. Create utility
# libs/shared/utils/src/lib/format.ts
export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

# 3. Export from index
# libs/shared/utils/src/index.ts
export * from './lib/format';

# 4. Update tsconfig.base.json
{
  "compilerOptions": {
    "paths": {
      "@libs/shared/utils": ["libs/shared/utils/src/index.ts"]
    }
  }
}

# 5. Update consuming projects with custom paths
# (Same as UI library example)

# 6. No Tailwind scanning needed (no styles)

# 7. Use in app
import { formatDate } from '@libs/shared/utils';
console.log(formatDate(new Date()));
```

---

## Testing Shared Libraries

```bash
# Run tests for specific library
nx run shared:test

# Run tests for all libraries
nx run-many --target=test --projects=libs/*

# Run lint for specific library
nx run shared:lint
```

---

## Quick Reference

| Task | Action |
|------|--------|
| Create library | `nx generate @nx/js:library <name> --directory=libs/shared/<name>` |
| Add TypeScript path | Update `tsconfig.base.json` paths |
| Update consuming projects | Duplicate path in projects with custom paths |
| Add Tailwind scanning | Add `@source` in app's CSS (after `@theme`) |
| Run library tests | `nx run <library>:test` |
| Find projects with custom paths | `grep -r '"paths"' apps/*/tsconfig.json libs/*/tsconfig.json` |

---

*For detailed TypeScript paths and Tailwind configuration, see `/llm-artifacts/TYPESCRIPT-PATHS.md`. For monorepo context, see `/CLAUDE.md`.*
