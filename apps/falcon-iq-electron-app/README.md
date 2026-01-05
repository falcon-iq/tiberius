# Falcon IQ Electron App

A modern Electron application built with React, TypeScript, TanStack Router, and Tailwind CSS.

## Architecture

This Electron app follows the standard three-process architecture:

- **Main Process** (`src/main/`): The Node.js backend that manages windows and system integration
- **Preload Script** (`src/preload/`): Security bridge between main and renderer processes
- **Renderer Process** (`src/renderer/`): The React frontend UI

## Technology Stack

- **Electron 39.2.7**: Desktop application framework
- **React 19**: UI framework
- **TypeScript**: Type-safe development
- **TanStack Router**: Type-safe routing for React
- **Tailwind CSS 4**: Utility-first CSS framework
- **Vite**: Fast build tool and dev server
- **Electron Forge**: Build and packaging toolchain

## Development

### Start the app in development mode

```bash
# Using NX (recommended)
npx nx dev falcon-iq-electron-app

# Or from the app directory
cd apps/falcon-iq-electron-app
npm start
```

The app will launch with hot-reload enabled. Changes to the renderer process will hot-reload automatically. Type `rs` in the terminal to restart the main process.

### Project Structure

```
apps/falcon-iq-electron-app/
├── src/
│   ├── main/           # Electron main process
│   │   └── index.ts    # Main entry point
│   ├── preload/        # Preload scripts
│   │   └── preload.ts
│   └── renderer/       # React frontend
│       ├── app/
│       │   └── App.tsx
│       ├── components/
│       ├── routes/     # TanStack Router routes
│       ├── styles/
│       └── index.tsx
├── forge.config.ts     # Electron Forge configuration
├── vite.main.config.mts
├── vite.preload.config.mts
├── vite.renderer.config.mts
├── index.html
├── package.json
├── project.json        # NX project configuration
└── tsconfig.json
```

### TypeScript Path Aliases

The following path aliases are configured in `tsconfig.json`:

```typescript
import Component from '@components/Component'
import { Route } from '@routes/dashboard'
import styles from '@styles/theme.css'
import { useAuth } from '@hooks/useAuth'
import { ApiService } from '@services/api'
```

## Building & Packaging

### Package the application

```bash
# Using NX
npx nx package falcon-iq-electron-app

# Creates distributable in apps/falcon-iq-electron-app/out
```

### Create platform distributables

```bash
# Using NX
npx nx make falcon-iq-electron-app

# Creates installers for the current platform in apps/falcon-iq-electron-app/out/make
```

Supported platforms:
- **macOS**: ZIP archive (for direct distribution)
- **Windows**: Squirrel installer
- **Linux**: DEB and RPM packages

## Routing

This app uses TanStack Router for type-safe routing. Routes are defined in `src/renderer/routes/`:

- `__root.tsx`: Root layout component
- `index.tsx`: Home page
- `about/index.tsx`: About page
- `settings.tsx`: Settings page

The route tree is automatically generated at `src/renderer/types/routeTree.gen.ts`.

## Styling

Tailwind CSS 4 is integrated via Vite plugin. Global styles are in `src/renderer/styles/globals.css`.

## NX Integration

This project is integrated into the NX monorepo:

### Available NX Commands

```bash
# Start development
npx nx dev falcon-iq-electron-app

# Type checking
npx nx typecheck falcon-iq-electron-app

# Linting
npx nx lint falcon-iq-electron-app

# Package
npx nx package falcon-iq-electron-app

# Make distributables
npx nx make falcon-iq-electron-app
```

### Workspace Dependencies

All dependencies are managed at the workspace root in the main `package.json`. The app's `package.json` only contains metadata and npm scripts for Electron Forge.

## Configuration

### Electron Forge

The `forge.config.ts` file configures:
- Build process (Vite plugin)
- Packaging options
- Platform-specific makers
- Security fuses

### Vite Configuration

Three separate Vite configs:
- `vite.main.config.mts`: Main process bundling
- `vite.preload.config.mts`: Preload script bundling
- `vite.renderer.config.mts`: Renderer process with React, Tailwind, and TanStack Router

## Security

The app includes security best practices:
- Content Security Policy in `index.html`
- Context isolation enabled
- Node integration disabled in renderer
- Security fuses configured in `forge.config.ts`

## Troubleshooting

### Hot reload not working

Type `rs` in the terminal to manually restart the main process.

### Module not found errors

Ensure all dependencies are installed at the workspace root:

```bash
cd /path/to/tiberius
npm install
```

### Build errors

Clear the build cache and try again:

```bash
npx nx reset
npx nx dev falcon-iq-electron-app
```

