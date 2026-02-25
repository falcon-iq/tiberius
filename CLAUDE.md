# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For app-specific context, see `apps/*/CLAUDE.md` and `libs/CLAUDE.md`.

## Project Overview

**Tiberius** is an Nx 21.6.4 monorepo with five applications and two shared libraries:

| App | Stack | Purpose |
|---|---|---|
| `falcon-iq-electron-app` | Electron 39 + React 19 + TypeScript + Vite + SQLite | Desktop project management app |
| `falcon-iq-rest` | Java 21 + Jersey 3.1 + Jetty 12 + MongoDB | Backend REST API |
| `falcon-iq-crawler` | Java 21 + Jetty + JSoup + AWS S3 | Multi-threaded web crawler microservice |
| `falcon-iq-analyzer` | Python 3.11 + FastAPI + OpenAI/Ollama + boto3 | LLM-powered website analysis service |
| `falcon-iq-analyzer-web-app` | React 19 + TypeScript + Vite + TanStack | Web frontend for the analyzer |

| Library | Path Alias | Purpose |
|---|---|---|
| `libs/shared/` | `@libs/shared/*` | Utilities, validations, React hooks |
| `libs/integrations/` | `@libs/integrations/github` | GitHub API (Octokit) |

## Essential Commands

```bash
# Setup
npm install                                    # Install deps (triggers electron-rebuild for better-sqlite3)
npm run prepare                                # Setup Husky git hooks

# Development
nx run falcon-iq-electron-app:dev              # Electron app with HMR
nx run falcon-iq-rest:dev                      # REST API (embedded Jetty, port 8080)
nx run falcon-iq-crawler:serve                 # Crawler server (port 8080)
nx run falcon-iq-analyzer:serve                # Analyzer FastAPI (port 8000)
nx run falcon-iq-analyzer-web-app:dev          # Web app + analyzer + crawler in parallel

# Quality
nx run-many --parallel -t lint test            # All projects
nx run <project>:lint                          # Single project
nx run <project>:test                          # Single project
nx run falcon-iq-analyzer:format              # Ruff format check (Python)

# Build
nx run falcon-iq-electron-app:package          # Package Electron app
nx run falcon-iq-rest:build                    # Maven WAR
nx run falcon-iq-rest:build:standalone         # Maven fat JAR (embedded Jetty)
nx run falcon-iq-crawler:build                 # Maven fat JAR
nx run falcon-iq-analyzer:build                # uv sync
nx run falcon-iq-analyzer-web-app:build        # Vite build

# Infrastructure (from infra/ directory)
make setup                                     # First-time: terraform init + tfvars
make plan                                      # Preview infrastructure changes
make deploy                                    # Terraform apply
make build-push                                # Build + push both Docker images to ECR
make build-push-crawler                        # Crawler image only
make build-push-analyzer                       # Analyzer image only
make redeploy                                  # Force new ECS deployment
make status                                    # Check ECS service health
make logs-crawler                              # Tail crawler CloudWatch logs
make logs-analyzer                             # Tail analyzer CloudWatch logs

# Commits (REQUIRED — git hooks enforce conventional commit format)
npm run commit                                 # Commitizen prompt
```

## Architecture

### Inter-Service Communication

```
[Browser] --HTTP--> [Analyzer :8000] --HTTP--> [Crawler :8080] --> [S3 / Local FS]
                         |                           |
                         +---S3 read/write---> [S3 Bucket] <---+

[Electron Renderer] --IPC--> [Electron Main] --HTTP--> [Python Server :8765]
                                   |
                                   +--SQLite (local)
                                   +--HTTP--> [REST API :8080] --> [MongoDB]
```

- **Analyzer <-> Crawler:** HTTP REST. In AWS, crawler is discovered via Cloud Map at `http://crawler.falcon-iq.local:8080`
- **Web App <-> Analyzer:** Vite dev proxy in development; in production, analyzer serves the web app's `dist/` as static files
- **Electron:** Renderer communicates with main process via IPC; main process proxies to embedded Python server on port 8765

### Analyzer Pipeline (6 steps)

Load pages -> Clean HTML -> Classify pages (LLM) -> Extract offerings (LLM) -> Synthesize top 5 (LLM) -> Generate report

### AWS Infrastructure (Terraform in `infra/`)

ECS Fargate cluster in custom VPC (us-east-1). Crawler runs in private subnets (internal only, Cloud Map DNS). Analyzer runs behind a public ALB on port 80. Shared S3 bucket for crawl data and analysis results. OpenAI API key in Secrets Manager.

## Critical Technical Concepts

### TypeScript Paths Don't Merge
When a child `tsconfig.json` defines `paths`, it completely overrides the parent's. You MUST duplicate all shared library paths from `tsconfig.base.json`:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "paths": {
      "@libs/shared/ui": ["../../libs/shared/ui/src/index.ts"],
      "@components/*": ["src/components/*"]
    }
  }
}
```

### Tailwind v4 Uses `@source` Directives
No `tailwind.config.ts`. Add `@source` directives in app CSS (AFTER `@theme` block) to scan shared libraries:

```css
@import "tailwindcss";
@theme inline { /* ... */ }
@source "../../../../../../libs/shared/ui/src";
```

Restart dev server after adding `@source` directives.

### Environment Names — Never Abbreviated
Always: `development`, `staging`, `production`. Never: `dev`, `stage`, `prod`.

### Tests in `tests/` Folders
All test files go in `tests/` subdirectories, not alongside source:
- `src/lib/tests/csv.spec.ts` (correct)
- `src/lib/csv.spec.ts` (wrong)

Tests use relative imports: `import { toCsv } from '../csv'`

### Python Tooling (Analyzer)
- **Package manager:** `uv` (not pip)
- **Linter/formatter:** `ruff` (not black/flake8)
- **Settings:** Pydantic Settings with `WEB_ANALYZER_*` env prefix

## Code Organization

**TypeScript projects:**
```
src/
├── lib/
│   ├── types/index.ts       # Type definitions
│   ├── tests/foo.spec.ts    # Tests
│   └── foo.ts               # Source
└── index.ts                 # Barrel exports
```

**Shared libraries must be:** added to `tsconfig.base.json` paths, duplicated in consuming project's tsconfig if it has custom paths, and scanned by Tailwind via `@source`.

## Common Gotchas

1. **TS imports broken?** Check path duplication in project's `tsconfig.json`
2. **Tailwind classes missing?** Add `@source` directive, restart dev server
3. **Tests not found?** Must be in `tests/` folder
4. **Commit rejected?** Use `npm run commit`, not `git commit`
5. **Electron navigation?** Use TanStack Router `Link`, never `<a>` tags
6. **Analyzer deps?** Use `uv`, not `pip install`
