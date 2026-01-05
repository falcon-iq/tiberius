# Tailwind CSS Integration in Amista

## Quick Reference for LLM Assistants

**Status**: ✅ Fully configured and ready to use

**Key Files**:
- `vite.renderer.config.mts` - Tailwind plugin configured
- `src/renderer/styles/globals.css` - Contains `@import "tailwindcss";` and custom theme
- All React components in `src/renderer/` can use Tailwind utility classes

**Import Path**:
```tsx
// Use TypeScript path alias (recommended):
import '@styles/globals.css';

// Or relative path:
import './styles/globals.css';
```

**Usage**: Apply utility classes directly in JSX `className` attributes:
```tsx
<button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Click me
</button>
```

**Key Points**:
- Tailwind v4.x with Vite plugin (`@tailwindcss/vite`)
- Renderer process only (React UI components)
- Tree-shaking enabled (only used classes in production)
- Hot reload with Fast Refresh
- No config file required (unless customizing)

---

## Overview

Tailwind CSS is a utility-first CSS framework integrated into the Amista Electron application. This document provides comprehensive information about how Tailwind CSS v4 is configured and should be used within this project.

## What is Tailwind CSS?

**Tailwind CSS** is a utility-first CSS framework that provides low-level utility classes to build custom designs without writing traditional CSS. Instead of predefined components, it offers atomic utility classes like `flex`, `pt-4`, `text-center`, and `rotate-90` that can be composed to build any design directly in your markup.

**Key Philosophy**: Build complex designs from small, reusable utility classes rather than writing custom CSS.

---

## Installation Details

### Packages Installed

The following packages are installed for Tailwind CSS v4 support:

- **`tailwindcss@^4.1.x`** - Core Tailwind CSS framework (v4)
- **`@tailwindcss/vite@^4.1.x`** - Official Vite plugin for Tailwind CSS v4

### Installation Command

```bash
npm install tailwindcss @tailwindcss/vite
```

---

## Configuration

### Current Setup (Already Completed)

This project has Tailwind CSS v4 fully configured. The following setup has already been completed:

1. **Packages Installed**: `tailwindcss@4.1.18`, `@tailwindcss/vite@4.1.18`, and `tw-animate-css` (for animations)
2. **Vite Config Updated**: `vite.renderer.config.mts` includes the Tailwind plugin
3. **CSS Import Added**: `src/renderer/styles/globals.css` imports Tailwind and includes custom theme
4. **Ready to Use**: All React components can use Tailwind utility classes

### Vite Configuration

Tailwind CSS is configured in the **renderer process** Vite config because it's used for styling the UI (React components).

**File**: `vite.renderer.config.mts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    tailwindcss(),  // Tailwind plugin MUST come before React plugin
    react(),
  ],
});
```

**Important**: The Tailwind plugin is placed before the React plugin in the plugins array. This ensures Tailwind processes the CSS before React's Fast Refresh mechanism.

### CSS Import

Tailwind CSS is imported in the main stylesheet:

**File**: `src/renderer/styles/globals.css`

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

/* Custom theme variables and styles below */
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  /* ... more custom properties ... */
}

@theme inline {
  --font-sans: 'Geist', 'Geist Fallback';
  --font-mono: 'Geist Mono', 'Geist Mono Fallback';
  --color-background: var(--background);
  /* ... theme mappings ... */
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

**Note**: 
- The `@import "tailwindcss";` directive imports all of Tailwind's utility classes
- The `@import "tw-animate-css";` adds animation utilities
- The `@custom-variant` defines custom dark mode variant support
- The `@theme` block maps custom CSS variables to Tailwind's theme system
- This replaces the older `@tailwind` directives from Tailwind v3

---

## Tailwind CSS v4 vs v3: Key Differences

If you're familiar with Tailwind v3, here are the major changes in v4:

### 1. **New Import Syntax**

**v3 (Old)**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**v4 (New)**:
```css
@import "tailwindcss";
```

### 2. **Native Vite Plugin**

v4 introduces a native Vite plugin (`@tailwindcss/vite`) that's optimized for performance and better integrates with Vite's build pipeline.

### 3. **No Configuration File Required**

Tailwind v4 works out-of-the-box without a `tailwind.config.js` file for most use cases. Configuration can be done through CSS custom properties or by creating a config file only when needed.

### 4. **CSS-First Configuration** (Optional)

You can configure Tailwind directly in CSS using custom properties:

```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --font-display: "Inter", sans-serif;
}
```

---

## Usage in React Components

### Basic Example

```tsx
// src/renderer/components/Button.tsx
const Button = ({ children }: { children: React.ReactNode }) => {
  return (
    <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
      {children}
    </button>
  );
};

export default Button;
```

### Common Utility Patterns

#### Layout & Spacing
```tsx
<div className="flex items-center justify-between p-4 m-2">
  <span>Left</span>
  <span>Right</span>
</div>
```

#### Typography
```tsx
<h1 className="text-3xl font-bold text-gray-900">
  Heading
</h1>
<p className="text-base text-gray-600 leading-relaxed">
  Paragraph text
</p>
```

#### Responsive Design
```tsx
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Full width on mobile, half on medium, third on large screens */}
</div>
```

#### Dark Mode (if enabled)
```tsx
<div className="bg-white dark:bg-gray-800 text-black dark:text-white">
  Content
</div>
```

---

## Integration with Electron

### Process-Specific Considerations

**Renderer Process Only**: Tailwind CSS is used exclusively in the **renderer process** (React UI). It has no relevance to the main process or preload scripts.

**File Organization**:
```
src/
├── renderer/
│   ├── index.tsx         # Imports @styles/globals.css (via path alias)
│   ├── styles/
│   │   └── globals.css   # Contains @import "tailwindcss" and custom theme
│   ├── App.tsx           # Can use Tailwind classes
│   └── components/       # All React components can use Tailwind
│       └── Button.tsx
```

**Note**: The project uses TypeScript path aliases (e.g., `@styles/*`) for cleaner imports. See README-LLM.md section 4a for details.

### Styling Electron-Specific Elements

When styling Electron windows or OS-specific elements, combine Tailwind utilities with custom CSS as needed:

```css
/* src/renderer/styles/globals.css */
@import "tailwindcss";
@import "tw-animate-css";

/* Custom styles for Electron window drag region */
.titlebar {
  -webkit-app-region: drag;
}

.titlebar button {
  -webkit-app-region: no-drag;
}
```

Then use in React:
```tsx
<div className="titlebar flex items-center h-8 bg-gray-200">
  <span className="ml-2">Amista</span>
  <button className="ml-auto mr-2">Close</button>
</div>
```

---

## Development Workflow

### Hot Module Replacement (HMR)

Tailwind CSS v4 with Vite provides **instant feedback** during development:

1. Make changes to Tailwind classes in React components
2. Save the file
3. Changes appear immediately without full page reload
4. Component state is preserved

### Build Process

**Development**:
```bash
npm start  # Vite compiles Tailwind on-demand
```

**Production**:
```bash
npm run package  # Tailwind is optimized and tree-shaken
```

**What Happens**:
- Vite plugin scans all files for Tailwind classes
- Only used utility classes are included in final CSS
- Unused classes are automatically removed (tree-shaking)
- Result: Small, optimized CSS bundles

---

## Custom Theme & Design System

### Overview

This project includes a comprehensive design system with:
- **Custom color palette** using OKLCH color space (better perceptual uniformity)
- **Dark mode support** with `.dark` class variant
- **Semantic color tokens** for consistent theming
- **Animation utilities** via `tw-animate-css`
- **Custom radius values** for rounded corners

### Semantic Color Tokens

The `globals.css` file defines semantic color tokens that automatically adapt to light/dark mode:

**Available Tokens**:
- `background` / `foreground` - Base background and text colors
- `card` / `card-foreground` - Card backgrounds and text
- `popover` / `popover-foreground` - Popover/dropdown colors
- `primary` / `primary-foreground` - Primary action colors
- `secondary` / `secondary-foreground` - Secondary actions
- `muted` / `muted-foreground` - Muted/disabled states
- `accent` / `accent-foreground` - Accent highlights
- `destructive` / `destructive-foreground` - Error/delete actions
- `border` - Border colors
- `input` - Input field borders
- `ring` - Focus ring colors
- `sidebar-*` - Sidebar-specific colors (for future use)
- `chart-1` through `chart-5` - Data visualization colors

**Usage in Components**:
```tsx
<div className="bg-background text-foreground">
  <h1 className="text-primary">Title</h1>
  <p className="text-muted-foreground">Subtitle</p>
  <button className="bg-primary text-primary-foreground">Click</button>
  <span className="text-destructive">Error message</span>
</div>
```

### Dark Mode

Dark mode is implemented using a custom variant that checks for the `.dark` class:

```css
@custom-variant dark (&:is(.dark *));
```

**Enabling Dark Mode**:
```tsx
// Toggle dark mode by adding/removing 'dark' class on root element
document.documentElement.classList.add('dark');    // Enable
document.documentElement.classList.remove('dark'); // Disable
```

**Dark Mode in Components**:
The semantic tokens automatically switch - no need for `dark:` prefix on semantic colors:
```tsx
// This automatically adapts to dark mode
<div className="bg-background text-foreground">
  Content
</div>

// For non-semantic colors, use dark: prefix
<div className="bg-white dark:bg-gray-900">
  Content
</div>
```

### Animation Utilities

The `tw-animate-css` package provides ready-to-use animation classes:

**Examples**:
```tsx
<div className="animate-fade-in">Fades in</div>
<div className="animate-slide-up">Slides up</div>
<div className="animate-bounce">Bounces</div>
```

**Documentation**: See [tw-animate-css documentation](https://www.npmjs.com/package/tw-animate-css) for all available animations.

### Border Radius

Custom radius values are defined and can be used:

```tsx
<div className="rounded-sm">Small radius</div>   {/* --radius-sm */}
<div className="rounded-md">Medium radius</div>  {/* --radius-md */}
<div className="rounded-lg">Large radius</div>   {/* --radius-lg */}
<div className="rounded-xl">XL radius</div>      {/* --radius-xl */}
```

### Typography

Custom fonts are configured:
- **Sans Serif**: Geist (with fallback)
- **Monospace**: Geist Mono (with fallback)

**Usage**:
```tsx
<p className="font-sans">Regular text</p>
<code className="font-mono">Code block</code>
```

**Note**: Ensure Geist fonts are installed/loaded in your project for full effect.

---

## Customization

### Adding Custom Styles

You have several options for customization:

#### Option 1: Extend with Custom CSS
```css
/* src/renderer/styles/globals.css */
@import "tailwindcss";
@import "tw-animate-css";

.custom-button {
  @apply bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded;
}
```

#### Option 2: Use Arbitrary Values
```tsx
<div className="top-[117px] left-[344px]">
  Custom positioning
</div>
```

#### Option 3: CSS Variables (Recommended for Themes)
```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --font-brand: "Inter", sans-serif;
}
```

Then use:
```tsx
<button className="bg-primary text-white">Button</button>
```

### Creating a Configuration File (Optional)

If you need extensive customization, create a `tailwind.config.ts`:

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

export default {
  theme: {
    extend: {
      colors: {
        brand: {
          light: '#3b82f6',
          dark: '#1e40af',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
} satisfies Config;
```

---

## Best Practices for This Project

### 1. **Component Organization**

Create reusable styled components:

```tsx
// src/renderer/components/Card.tsx
const Card = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {children}
    </div>
  );
};
```

### 2. **Consistent Spacing**

Use Tailwind's spacing scale (0, 1, 2, 4, 6, 8, etc.) for consistency:

```tsx
<div className="p-4 m-2 space-y-4">
  {/* padding: 1rem, margin: 0.5rem, vertical spacing: 1rem */}
</div>
```

### 3. **Responsive Design**

Design mobile-first, then add responsive classes:

```tsx
<div className="text-sm md:text-base lg:text-lg">
  {/* Small on mobile, base on tablet, large on desktop */}
</div>
```

### 4. **Component Variants**

Use props to control styling:

```tsx
const Button = ({ variant = 'primary' }: { variant?: 'primary' | 'secondary' }) => {
  const baseClasses = "font-bold py-2 px-4 rounded";
  const variantClasses = {
    primary: "bg-blue-500 hover:bg-blue-700 text-white",
    secondary: "bg-gray-200 hover:bg-gray-300 text-gray-800",
  };
  
  return (
    <button className={`${baseClasses} ${variantClasses[variant]}`}>
      Click me
    </button>
  );
};
```

### 5. **Maintain Custom CSS Separation**

Keep Electron-specific or truly custom styles in separate CSS, don't mix everything with Tailwind:

```css
/* src/renderer/styles/electron-specific.css */
.window-controls {
  -webkit-app-region: drag;
}
```

---

## Performance Considerations

### Tree-Shaking

Tailwind v4 with Vite automatically removes unused CSS. Only classes you actually use in your components are included in the production build.

### JIT (Just-In-Time) Compilation

Tailwind v4 uses JIT by default:
- Generates styles on-demand during development
- Faster build times
- Smaller development bundle size
- Supports arbitrary values without configuration

### Production Build

The production build is highly optimized:
- Unused CSS removed
- CSS minified
- Critical CSS can be inlined
- Typical final CSS size: 5-10 KB (depends on usage)

---

## TypeScript Support

### Class Name IntelliSense

For VS Code, install the **Tailwind CSS IntelliSense** extension:

1. Open VS Code Extensions
2. Search "Tailwind CSS IntelliSense"
3. Install the official extension

**Benefits**:
- Autocomplete for class names
- Hover previews showing CSS
- Syntax highlighting
- Error detection for invalid classes

### Type-Safe Class Names (Optional)

For extra type safety, consider using `clsx` or `classnames`:

```bash
npm install clsx
```

```tsx
import clsx from 'clsx';

const Button = ({ isPrimary }: { isPrimary: boolean }) => {
  return (
    <button className={clsx(
      'font-bold py-2 px-4 rounded',
      isPrimary ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'
    )}>
      Click me
    </button>
  );
};
```

---

## Troubleshooting

### Issue: Styles Not Appearing

**Solution**:
1. Ensure `@import "tailwindcss";` is at the top of `styles/globals.css`
2. Verify `styles/globals.css` is imported in `index.tsx` (using `@styles/globals.css` or `./styles/globals.css`)
3. Check that `tailwindcss()` plugin is in `vite.renderer.config.mts`
4. Clear Vite cache: `rm -rf .vite && npm start`

### Issue: IntelliSense Not Working

**Solution**:
1. Install Tailwind CSS IntelliSense extension
2. Restart VS Code
3. Ensure you have a `tailwind.config.ts` file (create empty one if needed)

### Issue: Custom Classes Not Working

**Solution**:
- Tailwind v4 scans files for classes; dynamic class names won't work
- ❌ Bad: `className={`text-${color}-500`}`
- ✅ Good: `className={color === 'blue' ? 'text-blue-500' : 'text-red-500'}`

### Issue: Build Errors After Installation

**Solution**:
1. Clear build cache: `rm -rf .vite`
2. Reinstall dependencies: `npm install`
3. Restart dev server: `npm start`

---

## Additional Resources

### Official Documentation
- **Tailwind CSS v4 Docs**: https://tailwindcss.com/docs
- **Vite Plugin**: https://tailwindcss.com/docs/installation/vite
- **Utility Classes**: https://tailwindcss.com/docs/utility-first

### Learning Resources
- **Interactive Playground**: https://play.tailwindcss.com/
- **Component Examples**: https://tailwindui.com/components (official, some paid)
- **Free Components**: https://www.hyperui.dev/, https://daisyui.com/

### VS Code Extension
- **Tailwind CSS IntelliSense**: Essential for autocomplete and previews

---

## Summary for LLM Assistants

**Tailwind CSS v4** is configured in the Amista Electron application using:
- **Vite Plugin**: `@tailwindcss/vite` in `vite.renderer.config.mts`
- **CSS Import**: `@import "tailwindcss";` in `src/renderer/styles/globals.css`
- **Import Method**: Use `@styles/globals.css` (TypeScript path alias) or relative path
- **Usage**: Utility classes directly in React component JSX/TSX files
- **Scope**: Renderer process only (React UI components)
- **Performance**: Tree-shaking and JIT compilation for optimal bundle size

**When assisting with this project**:
- Import styles using path alias: `import '@styles/globals.css'`
- Use Tailwind utility classes for styling React components
- Prefer utility classes over custom CSS for most styling needs
- Remember responsive prefixes (`md:`, `lg:`, etc.) for responsive design
- Use semantic color tokens like `bg-primary`, `text-foreground` (defined in `globals.css`)
- Keep Electron-specific styles (like `-webkit-app-region`) in custom CSS
- Use the `@apply` directive for reusable custom component styles
- Dynamic class names must be complete strings (no template literals with variables)

**The project is ready for Tailwind-based styling** - all configuration is complete and you can start using utility classes in any React component immediately.

---

## Appendix: Setup Instructions (For Reference)

This section documents how Tailwind CSS v4 was set up in this project. This is for reference only - **the setup is already complete**.

### Step 1: Install Packages

```bash
npm install tailwindcss @tailwindcss/vite tw-animate-css
```

This installs:
- `tailwindcss` - The core framework
- `@tailwindcss/vite` - The official Vite plugin for v4
- `tw-animate-css` - Animation utilities for Tailwind

### Step 2: Configure Vite

Update `vite.renderer.config.mts` to include the Tailwind plugin:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    tailwindcss(),  // Add before React plugin
    react(),
  ],
});
```

**Important**: Place `tailwindcss()` before `react()` in the plugins array.

### Step 3: Import Tailwind in CSS

Create `src/renderer/styles/globals.css` and add:

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

/* Add your custom theme variables */
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  /* ... more custom properties ... */
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  /* ... theme mappings ... */
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### Step 4: Import CSS in Entry Point

Update `src/renderer/index.tsx` to import the globals CSS using path alias:

```tsx
// Using TypeScript path alias (recommended)
import '@styles/globals.css';

// Or using relative path
// import './styles/globals.css';

import { createRoot } from 'react-dom/client';
import App from './App';

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(<App />);
```

**Note**: The project uses `@styles/*` path alias configured in `tsconfig.json` for cleaner imports.

### Step 5: Use in React Components

Start using Tailwind utility classes in your React components:

```tsx
// src/renderer/App.tsx
const App = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <h1 className="text-4xl font-bold text-blue-600">
        Hello Tailwind!
      </h1>
    </div>
  );
};
```

### Step 6: Verify Installation

Run the development server:

```bash
npm start
```

If Tailwind classes are applied correctly, the setup is complete.

### Troubleshooting Setup Issues

If styles don't appear:
1. Verify `@import "tailwindcss";` is at the top of `styles/globals.css`
2. Check `styles/globals.css` is imported in `index.tsx` (using `@styles/globals.css`)
3. Confirm Tailwind plugin is in `vite.renderer.config.mts`
4. Clear cache: `rm -rf .vite && npm start`

