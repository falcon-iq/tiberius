# TypeScript Path Mappings & Tailwind Configuration in Nx Monorepo

## TypeScript Path Mappings

### The Problem

TypeScript's `paths` configuration **does not merge** when using `extends`. When a child `tsconfig.json` defines `paths`, it completely overrides the parent's `paths` rather than merging them.

### The Solution

When a project needs custom path mappings (like `@components/*`, `@utils/*`), you must **explicitly include all shared library paths** from `tsconfig.base.json` in the project's `tsconfig.json`.

#### Example

In `tsconfig.base.json`:

```json
{
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["libs/shared/ui/src/index.ts"]
    }
  }
}
```

In `apps/my-app/tsconfig.json`:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["../../libs/shared/ui/src/index.ts"], // Must repeat!
      "@components/*": ["src/components/*"] // Local paths
    }
  }
}
```

## Tailwind CSS v4 Configuration for Shared Libraries

### The Problem

Tailwind CSS v4 in an Nx monorepo does not automatically scan `libs/**` from an app's CSS entry point. As a result, classnames used inside shared libraries never generate CSS, and the components appear unstyled.

### The Solution

Use the `@source` directive in your app's Tailwind entry CSS file to explicitly tell Tailwind v4 where to find shared library files.

#### Example

In `apps/my-app/src/renderer/styles/globals.css`:

```css
@import "tailwindcss";
@import "tw-animate-css";

/* Scan shared UI library for Tailwind classes */
@source "../../../../../../libs/shared/ui/src";

@custom-variant dark (&:is(.dark *));

/* ... rest of your CSS ... */
```

**Important Notes:**
- The path in `@source` is relative to the CSS file location
- You need to restart the dev server after adding `@source` for changes to take effect
- Tailwind v4 uses `@source` directives instead of the `content` array from v3's `tailwind.config.js`

### DO NOT Use tailwind.config.ts with Tailwind v4

Tailwind CSS v4 does **not** use `tailwind.config.ts` or `tailwind.config.js` files. Instead, all configuration is done via CSS:
- Content scanning: Use `@source` directives
- Theme customization: Use `@theme` blocks
- Custom variants: Use `@custom-variant` directives

If you see a `tailwind.config.ts` file in a Tailwind v4 project, it should be removed.

## Best Practice for New Shared Libraries

When adding a new shared library to the monorepo:

1. **TypeScript Paths**: Add the path mapping to `tsconfig.base.json`
2. **Update Projects**: Update **every project that defines its own `paths`** to include the new library
3. **Tailwind Content**: Update each app's `tailwind.config.ts` to include the new library's source files
4. **Search for Configs**:

   ```bash
   # Find all tsconfig files that need updating
   grep -r '"paths"' apps/*/tsconfig.json libs/*/tsconfig.json

   # Find all Tailwind configs that need updating
   find . -name "tailwind.config.*" -not -path "*/node_modules/*"
   ```

## Why Not Just Remove Local Paths?

Projects like the Electron app need local path mappings for better DX (e.g., `@components/*` instead of `../../../components`). The tradeoff is that we must maintain shared paths in multiple places.

## Alternative: No Local Paths

If a project doesn't define any `paths`, it will inherit all paths from `tsconfig.base.json` automatically. This is simpler but loses the convenience of project-specific path shortcuts.
