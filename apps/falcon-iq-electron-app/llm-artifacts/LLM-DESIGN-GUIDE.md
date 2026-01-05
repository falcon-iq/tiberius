# Amista Design Guide

## Purpose

This guide captures the design philosophy, principles, and standards for Amista. Use it to maintain visual and functional consistency when building new features.

---

## Design Philosophy

### Vision
Amista is a clean, focused desktop application emphasizing **clarity**, **efficiency**, and **thoughtful hierarchy**. The design prioritizes content over chrome, with persistent navigation that stays out of the way.

### Core Principles

**1. Content First**
- Maximize space for primary content
- Minimize UI chrome and decorative elements
- Let content and data breathe

**2. Spatial Consistency**
- Persistent sidebars create predictable spatial zones
- Navigation always on the left, assistant always on the right
- Main content center-stage with consistent boundaries

**3. Progressive Disclosure**
- Show essential information immediately
- Reveal complexity only when needed
- Keep interfaces scannable at a glance

**4. Accessibility by Default**
- Semantic HTML throughout
- Screen reader support via `sr-only` text
- Keyboard navigation for all interactions
- Theme-aware color system supporting light and dark modes

---

## Layout System

### Application Structure

```
┌────────────────────────────────────────┐
│  64px │    Main Work     │   320px    │
│  Nav  │      Area        │   Agent    │
│  Bar  │   (flex-grow)    │  Sidebar   │
└────────────────────────────────────────┘
```

**Left Navigation (64px)**
- Icon-only vertical navigation
- Minimal footprint, maximum content space
- Active state clearly indicated

**Main Work Area (flexible)**
- Always includes fixed header (64px height)
- Scrollable content area below header
- Content constrained to max-width for readability

**Right Agent Sidebar (320px)**
- AI assistant and contextual information
- Fixed width for consistent interaction area
- Scrollable feed with fixed input

### Layout Principles

**Fixed vs. Flexible**
- Headers and footers: Fixed height (64px standard)
- Sidebars: Fixed width for spatial consistency
- Content areas: Flexible with max-width constraints
- Scrolling: Isolated to content areas, never full-page

**Spatial Zones**
- Navigation zone: Action-oriented, icon-driven
- Content zone: Breathing room, optimal line length
- Assistant zone: Supportive, always accessible

**Responsive Behavior**
- Built for desktop (Electron)
- Content areas use max-width for large screens
- Grid layouts respond to available space (`md:`, `lg:` breakpoints)

---

## Typography System

### Type Scale

**Page Titles**: `text-xl` (20px) - Bold, page headers only
**Section Headings**: `text-lg` (18px) - Medium weight
**Body Text**: `text-sm` (14px) - Regular weight, primary content
**Supporting Text**: `text-xs` (12px) - Metadata, labels, captions

### Type Principles

**Hierarchy Through Weight**
- Use font weight to establish hierarchy
- Avoid excessive size variation
- Consistent scale creates visual calm

**Readable Line Length**
- Content constrained to `max-w-7xl` (80rem)
- Narrower content uses `max-w-2xl` for optimal readability
- Never let text span full screen width

**Type Usage**
- One page title per view (h1)
- Section headings for major content divisions
- Body text as default
- Supporting text for metadata, not primary content

---

## Color System

### Philosophy

**Theme-Aware Colors**
Amista uses semantic color tokens that automatically adapt to light/dark themes. Never use hardcoded colors - always use semantic tokens.

### Semantic Palette

**Surfaces**
- `bg-background` - Primary background
- `bg-card` - Elevated surfaces, cards, panels
- `bg-sidebar` - Sidebar backgrounds

**Text**
- `text-foreground` - Primary text (high contrast)
- `text-muted-foreground` - Secondary text (reduced emphasis)
- `text-primary` - Accent text, links, active states

**Borders**
- `border-border` - Standard dividers
- `border-input` - Form field borders

**Interactive**
- `bg-primary` - Primary actions, active states
- `bg-secondary` - Secondary actions
- `bg-destructive` - Destructive actions (delete, remove)

**States**
- `hover:bg-sidebar-accent` - Hover states
- `bg-primary/10` - Subtle highlights (10% opacity)
- `text-sidebar-foreground/60` - Inactive states (60% opacity)

### Color Principles

**Always Semantic**
- Use named tokens (`bg-background`) not raw colors (`bg-gray-100`)
- Tokens automatically adapt to theme
- Maintains contrast ratios in both themes

**Opacity for States**
- Use opacity modifiers for subtle variations
- `/10` for backgrounds, `/60` for text
- Creates visual hierarchy without additional colors

**Contrast Pairs**
- Every background token has a foreground pair
- `bg-card` always with `text-card-foreground`
- Ensures accessible contrast automatically

---

## Spacing & Rhythm

### Spacing Scale

**Padding/Margins**
- `p-4` (16px) - Compact containers, list items
- `p-6` (24px) - Page content, comfortable reading
- `space-y-6` (24px) - Vertical rhythm between sections

**Gaps**
- `gap-2` (8px) - Tight groups (icon + text)
- `gap-4` (16px) - Related elements
- `gap-6` (24px) - Distinct sections

### Spacing Principles

**Consistent Rhythm**
- Use `space-y-6` for vertical stacking
- Creates predictable visual rhythm
- Maintains breathing room without waste

**Constrained Width**
- Content areas use padding: `px-6` (horizontal 24px)
- Combined with `max-w-7xl` for optimal reading
- Prevents content from spanning too wide

**Intentional Density**
- Comfortable padding around interactive elements
- More space between distinct sections
- Tighter spacing for related items

---

## Components & Patterns

### Page Structure

**Every page must include:**

1. **Fixed Header** (64px height)
   - Page title
   - Optional actions/controls
   - Bottom border for separation

2. **Scrollable Content** (flexible height)
   - `overflow-y-auto` for vertical scroll
   - Max-width container for readability
   - Consistent spacing between sections

### Cards & Containers

**Visual Elevation**
- Use `bg-card` for elevated surfaces
- Border with `border-border` for subtle definition
- `rounded-lg` for consistent corner radius

**Content Padding**
- `p-6` for comfortable internal spacing
- Maintains breathing room around content

### Interactive Elements

**Navigation Items**
- Icon-only with tooltip (`title` attribute)
- Active state via highlight background
- Inactive: muted color with hover state
- Use `Link` for navigation, `button` for actions

**Buttons**
- Primary: `bg-primary text-primary-foreground`
- Secondary: `bg-secondary text-secondary-foreground`
- Destructive: `bg-destructive text-destructive-foreground`
- Include hover states with opacity shift

**Form Inputs**
- Border with `border-input`
- Background: `bg-background`
- Placeholder: `text-muted-foreground`
- No background color by default (transparent)

---

## Theme Management

### Implementation

**Light/Dark Toggle**
- Add/remove `.dark` class on `<html>` element
- CSS variables automatically switch
- Theme state managed at root layout level

**When Dark Prefix Is Needed**
- Only for non-semantic colors
- Semantic tokens don't need `dark:` prefix
- Example: `bg-white dark:bg-gray-900` (if needed)

### Theme Principles

**Automatic Adaptation**
- Use semantic tokens everywhere
- Theme change affects entire app instantly
- No per-component theme logic needed

---

## Navigation Philosophy

### Routing
- Use TanStack Router's `Link` component exclusively
- Never use `<a>` tags or `window.location`
- Leverage `activeProps` for active state styling
- All navigation is client-side (SPA behavior)

### Navigation Hierarchy
- Primary navigation: Icon sidebar (always visible)
- Page title: Fixed header (current context)
- Breadcrumbs: If deep hierarchy needed (future)

---

## Accessibility Standards

### Semantic HTML
- Use proper elements: `<main>`, `<nav>`, `<header>`, `<aside>`
- Proper heading hierarchy (one h1 per page)
- Form elements properly labeled

### Screen Readers
- `sr-only` text for icon-only buttons
- Descriptive link text
- Proper ARIA labels where needed

### Keyboard Navigation
- All interactive elements keyboard accessible
- Focus states visible
- Logical tab order

---

## File Naming & Organization

### Conventions
- Components: `kebab-case.tsx` (`navigation-side-bar.tsx`)
- Component names: `PascalCase` (`NavigationSidebar`)
- Variables: `camelCase` (`toggleTheme`)
- Boolean variables: `is`, `has`, `should` prefix

### Import Aliases
Use TypeScript path aliases for cleaner imports:
- `@components/*` - Components
- `@routes/*` - Routes  
- `@styles/*` - Styles
- `@hooks/*` - Hooks
- `@generatedtypes/*` - Generated types

---

## Key Design Rules

### Do
✅ Use semantic color tokens exclusively
✅ Maintain consistent spacing scale
✅ Include fixed header on every page
✅ Use `Link` for all navigation
✅ Define TypeScript interfaces for props
✅ Use proper semantic HTML
✅ Include `sr-only` text for accessibility

### Don't
❌ Use hardcoded colors (`bg-gray-100`)
❌ Use `<a>` tags for internal navigation
❌ Use `<button>` for navigation actions
❌ Create pages without fixed headers
❌ Use inline styles
❌ Skip TypeScript types (`any`)
❌ Forget accessibility considerations

---

## Quick Reference

**Page Template:**
- Fixed header (64px, page title)
- Scrollable content with max-width
- Consistent spacing (`space-y-6`)

**Color Usage:**
- Backgrounds: `bg-background`, `bg-card`
- Text: `text-foreground`, `text-muted-foreground`
- Borders: `border-border`

**Spacing:**
- Content padding: `p-6`
- Vertical spacing: `space-y-6`
- Horizontal spacing: `px-6`

**Typography:**
- Page title: `text-xl font-semibold`
- Body text: `text-sm`
- Supporting text: `text-xs text-muted-foreground`

---

**Last Updated**: January 4, 2026 | **Version**: 1.0

