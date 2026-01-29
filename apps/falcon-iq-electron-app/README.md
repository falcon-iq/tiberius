# Falcon IQ Electron App

Desktop application built with Electron, React, and TypeScript, featuring an embedded Python FastAPI server for backend operations.

---

## Quick Start

### 1. Install Dependencies

```bash
# Install Node.js dependencies (from repo root)
npm install

# Set up Python environment (from this directory)
cd apps/falcon-iq-electron-app
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r src/python/requirements.txt
```

### 2. Run Development Server

```bash
# From repo root
npx nx run falcon-iq-electron-app:dev
```

The app will start with:
- Electron window with React UI
- Python FastAPI server running on http://127.0.0.1:8765
- Hot module reloading for frontend changes

---

## Python Server Setup

The app includes an embedded Python server (FastAPI) that runs as a subprocess alongside the Electron main process.

### Development Environment

**One-time setup:**

```bash
cd apps/falcon-iq-electron-app

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r src/python/requirements.txt
```

**Important:** The `.venv` directory is gitignored and must be created on each development machine.

### Why Use a Virtual Environment?

- **Isolation** - Keeps project dependencies separate from system Python
- **Reproducibility** - Same package versions across all machines
- **No conflicts** - Won't clash with other Python projects
- **No sudo needed** - Installs packages locally

### Verifying Setup

After installation, verify the Python server can start:

```bash
# With .venv activated
python src/python/server.py 8765
```

You should see:
```
Starting on port 8765
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765
```

Test the health endpoint:
```bash
curl http://127.0.0.1:8765/health
# Expected: {"status":"healthy"}
```

Press `Ctrl+C` to stop.

---

## How It Works

### Development Mode

When you run `nx run falcon-iq-electron-app:dev`:

1. **Vite** builds the React frontend with HMR
2. **Electron** starts the main process
3. **Python server** spawns as subprocess using `.venv/bin/python3`
4. **IPC bridge** connects renderer to Python server

**Python executable used:**
- macOS/Linux: `.venv/bin/python3` (from your venv)
- Windows: `.venv\Scripts\python.exe`

**Python script location:**
- `{repo}/apps/falcon-iq-electron-app/src/python/server.py`

### Production Mode (Packaged App)

When you build a distributable (DMG, exe, etc.):

1. **Python runtime** is bundled into the app (no user installation needed)
2. **Dependencies** are pre-installed into bundled runtime during build
3. **Python server** runs from bundled resources

**Python executable used:**
- macOS: `Falcon IQ.app/Contents/Resources/python-runtime/bin/python3`
- Windows: `Falcon IQ.exe/resources/python-runtime/python.exe`

**Python script location:**
- `{app}/Contents/Resources/src/python/server.py`

Users get a self-contained app with everything included.

---

## Architecture

### Multi-Process Model

```
┌─────────────────────────────────────────────────┐
│ Electron App                                    │
│                                                 │
│  ┌──────────────┐         ┌─────────────────┐  │
│  │ Main Process │◄───────►│ Python Server   │  │
│  │ (Node.js)    │   IPC   │ (subprocess)    │  │
│  └──────┬───────┘         └─────────────────┘  │
│         │                                       │
│         │ IPC                                   │
│         │                                       │
│  ┌──────▼───────┐                               │
│  │ Renderer     │                               │
│  │ (React UI)   │                               │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

### Communication Flow

**Renderer → Python:**
```typescript
// React component
const status = await window.api.pythonServer.getStatus();
```

**Preload script:**
```typescript
ipcRenderer.invoke('python:getStatus')
```

**Main process:**
```typescript
ipcMain.handle('python:getStatus', () => getPythonServerStatus())
```

**Python server management:**
- Automatic startup with health checks
- Graceful shutdown on app quit
- State persistence in `.falcon/python-server.json`
- Restart capability via IPC

### Python Server State

The Python server's runtime state (PID, port, startup time) is stored in a JSON file:

**Location:**
- Development: `~/.config/FalconIQ/userData/.falcon/python-server.dev.json`
- Production: `~/.config/FalconIQ/userData/.falcon/python-server.json`

**Why file-based storage?**
- **Singleton data** - Server state is a single object, not relational data
- **Human-readable** - JSON files are easy to inspect for debugging
- **Lightweight** - No database overhead for simple state
- **Atomic writes** - Uses temp file + rename for data safety

**Example state file:**
```json
{
  "pid": 12345,
  "port": 8765,
  "startedAt": "2024-01-15T10:30:00.000Z",
  "pythonExecutable": "/path/to/.venv/bin/python3",
  "serverScriptPath": "/path/to/src/python/server.py"
}
```

**Error handling:**
- Corrupt files are automatically backed up with timestamp
- Missing file treated as first run (server starts cleanly)
- State regenerated on every app startup

**Note:** The `.falcon/` directory is gitignored as it contains machine-specific runtime data.

---

## Common Tasks

### Adding Python Dependencies

```bash
# Activate venv
source .venv/bin/activate

# Install package
pip install pandas

# Update requirements.txt
pip freeze > src/python/requirements.txt
```

### Adding API Endpoints

Edit `src/python/server.py`:

```python
@app.get("/api/my-endpoint")
def my_endpoint():
    return {"message": "Hello from Python"}
```

Restart the dev server to pick up changes.

### Using Python Server from React

Create a React hook or use directly:

```typescript
import { usePythonServer } from '@/hooks/use-python-server';

function MyComponent() {
  const { status, isLoading } = usePythonServer();

  if (isLoading) return <div>Loading...</div>;

  return <div>Python server: {status.isRunning ? 'Running' : 'Stopped'}</div>;
}
```

### Debugging Python Server

Check logs in Electron DevTools console:

```typescript
// Get server status
await window.api.pythonServer.getStatus()

// Restart if needed
await window.api.pythonServer.restart()
```

Python server logs are captured and displayed in the main process logs.

---

## Tech Stack

- **Electron 39.2.7** - Desktop app framework
- **React 19** - UI library
- **TypeScript 5.9** - Type safety
- **TanStack Router** - File-based routing
- **TanStack Query** - Data fetching
- **Tailwind CSS v4** - Styling
- **better-sqlite3** - Local database
- **Python 3.x** - Backend runtime
- **FastAPI** - Python web framework
- **Uvicorn** - ASGI server

---

## Project Structure

```
apps/falcon-iq-electron-app/
├── src/
│   ├── main/
│   │   ├── index.ts              # Main process entry
│   │   ├── database.ts           # SQLite operations
│   │   ├── python-server.ts      # Python subprocess manager
│   │   ├── python-state.ts       # Python state file management
│   │   └── types/
│   │       └── python-server.ts  # Python types
│   ├── preload/
│   │   └── preload.ts            # IPC bridge
│   ├── renderer/
│   │   ├── index.tsx             # React entry
│   │   ├── routes/               # File-based routes
│   │   ├── components/           # React components
│   │   └── hooks/
│   │       └── use-python-server.ts  # Python status hook
│   └── python/
│       ├── server.py             # FastAPI server
│       └── requirements.txt      # Python dependencies
├── forge.config.ts               # Electron packaging
├── vite.main.config.ts           # Main process build
├── vite.renderer.config.ts       # Renderer build
└── .venv/                        # Python virtual environment (gitignored)

User data directory (gitignored):
└── .falcon/
    └── python-server.json        # Python server runtime state
```

---

## Troubleshooting

### Python server not starting

**Check if venv is set up:**
```bash
ls .venv/bin/python3  # Should exist
```

**Verify packages installed:**
```bash
source .venv/bin/activate
pip list | grep fastapi
```

**Check Python executable path:**
```typescript
// In DevTools console
await window.api.pythonServer.getStatus()
```

### ImportError: No module named 'fastapi'

Your venv isn't activated or packages aren't installed:
```bash
cd apps/falcon-iq-electron-app
source .venv/bin/activate
pip install -r src/python/requirements.txt
```

### Port already in use

Another process is using port 8765:
```bash
# Find process
lsof -i :8765

# Kill it
kill -9 <PID>
```

Or restart the Python server via IPC:
```typescript
await window.api.pythonServer.restart()
```

### Venv activation not working on Windows

Use the correct activation script:
```cmd
.venv\Scripts\activate.bat  # Command Prompt
.venv\Scripts\Activate.ps1  # PowerShell
```

### Python server state is corrupt

If the state file becomes corrupted, it's automatically backed up and the server restarts cleanly. To manually inspect or delete:

**macOS/Linux:**
```bash
# View current state
cat ~/.config/FalconIQ/userData/.falcon/python-server.dev.json

# Delete state (server will restart cleanly)
rm ~/.config/FalconIQ/userData/.falcon/python-server.dev.json
```

**Windows:**
```cmd
# View current state
type %APPDATA%\FalconIQ\userData\.falcon\python-server.dev.json

# Delete state
del %APPDATA%\FalconIQ\userData\.falcon\python-server.dev.json
```

Corrupt files are automatically backed up to `python-server.json.backup-{timestamp}`.

---

## Development Commands

```bash
# Start development server
npx nx run falcon-iq-electron-app:dev

# Build for production
npx nx run falcon-iq-electron-app:build

# Package app (DMG, exe, etc.)
npx nx run falcon-iq-electron-app:package

# Run linter
npx nx run falcon-iq-electron-app:lint

# Run tests
npx nx run falcon-iq-electron-app:test

# Type check
npx nx run falcon-iq-electron-app:typecheck
```

---

## Next Steps

- See `/CLAUDE.md` for monorepo-wide context
- See `CLAUDE.md` in this directory for app-specific development notes
- Check `src/python/server.py` for Python API endpoints
- Review `src/renderer/routes/` for adding new pages

---

## Contributing

This project uses conventional commits. Always use:

```bash
npm run commit
```

Instead of `git commit` to ensure proper commit message formatting.
