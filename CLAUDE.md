# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeerFlow is a full-stack "super agent harness" built on LangGraph and LangChain. It orchestrates sub-agents, memory, and sandboxes to execute complex tasks in isolated environments.

**Tech Stack:**
- Backend: Python 3.12+, LangGraph, FastAPI
- Frontend: Next.js 16 + React 19 + TypeScript + pnpm
- Entry point: nginx on port 2026

## Architecture

```
Browser → Nginx (2026) → Frontend (3000) | LangGraph (2024) | Gateway API (8001)
```

- `/api/langgraph/*` → LangGraph Server — agent interactions, threads, streaming
- `/api/*` (other) → Gateway API — models, MCP, skills, memory, uploads, artifacts
- `/` (non-API) → Frontend — Next.js web interface

The backend split:
- **`packages/harness/deerflow/`** (import: `deerflow.*`) — Publishable agent framework: agents, tools, sandbox, models, MCP, skills, config
- **`app/`** (import: `app.*`) — Unpublished application: FastAPI Gateway, IM channels (Feishu, Slack, Telegram)

**Critical rule**: `deerflow.*` must never import from `app.*`. Enforced by `tests/test_harness_boundary.py`.

## Commands

### Full Application (from repo root)
```bash
make check      # Verify Node 22+, pnpm, uv, nginx
make install    # Install backend (uv sync) + frontend (pnpm install)
make dev        # Start all services with hot-reload (LangGraph, Gateway, Frontend, nginx)
make stop       # Stop all services
make docker-start  # Docker dev environment (mode-aware from config.yaml)
```

### Backend Only (from `backend/`)
```bash
make lint      # ruff check
make format    # ruff check --fix + ruff format
make test      # pytest
```

### Frontend Only (from `frontend/`)
```bash
pnpm lint
pnpm typecheck
BETTER_AUTH_SECRET=local-dev-secret pnpm build
```

### CI Validation Order
1. `cd backend && make lint && make test`
2. `cd frontend && pnpm lint && pnpm typecheck`
3. `BETTER_AUTH_SECRET=... pnpm build` (only if UI/env/auth changes)

## Key Configuration

- `config.yaml` — Main app config (models, tools, sandbox, skills, memory). `$VAR` syntax resolves env vars.
- `extensions_config.json` — MCP servers + skill states
- `.env` — API keys (`OPENAI_API_KEY`, etc.)

Config precedence: explicit path > `DEER_FLOW_CONFIG_PATH` env > `config.yaml` in current dir > `config.yaml` in parent (project root).

## Important Patterns

### Lead Agent (`packages/harness/deerflow/agents/lead_agent/`)
- Entry: `make_lead_agent(config)` registered in `langgraph.json`
- 12 middleware components execute in strict order (ThreadData → Uploads → Sandbox → Guardrail → Summarization → TodoList → Title → Memory → ViewImage → SubagentLimit → Clarification)
- Tools assembled via `get_available_tools()` combining sandbox, built-in, MCP, community, subagent tools

### Sandbox System
- Per-thread isolated execution via `SandboxProvider` pattern
- Virtual paths: `/mnt/user-data/{workspace,uploads,outputs}` → `backend/.deer-flow/threads/{thread_id}/user-data/`
- Tools: `bash`, `ls`, `read_file`, `write_file`, `str_replace`

### Memory System
- Automatic LLM-powered extraction from conversations
- Debounced updates (30s default), fact deduplication, JSON storage at `backend/.deer-flow/memory.json`
- Top 15 facts injected into agent prompts via `<memory>` tags

## Directory Structure

```
deer-flow/
├── config.yaml              # Active config (gitignored)
├── config.example.yaml      # Config template
├── extensions_config.example.json
├── Makefile                # Root orchestration
├── backend/
│   ├── packages/harness/deerflow/  # deerflow-* package (agents, sandbox, tools, models, mcp, skills)
│   ├── app/gateway/               # FastAPI Gateway API (port 8001)
│   ├── app/channels/              # IM integrations (Feishu, Slack, Telegram)
│   ├── langgraph.json             # Graph entry: deerflow.agents:make_lead_agent
│   ├── tests/                     # Backend tests
│   └── docs/                      # Backend documentation
├── frontend/
│   ├── src/app/            # Next.js routes
│   ├── src/components/     # UI components
│   ├── src/core/           # App logic (threads, tools, API, models)
│   └── env.js              # Env validation (BETTER_AUTH_SECRET required for build)
├── skills/                 # Agent skills
│   ├── public/             # Built-in skills
│   └── custom/             # User skills
└── docker/                 # Docker Compose + nginx configs
```

## Known Gotchas

- `make config` aborts if config.yaml exists (intentional guard for first-time setup)
- `BETTER_AUTH_SECRET` is required for frontend production build — set it or use `SKIP_ENV_VALIDATION=1`
- `pnpm check` fails in this repo; use `pnpm lint && pnpm typecheck` instead
- Proxy env vars can silently break frontend network operations
- Docker dev `make docker-start` only starts `provisioner` when sandbox is configured for provisioner/K8s mode

## Reference

- Backend architecture: `backend/CLAUDE.md`
- Configuration: `backend/docs/CONFIGURATION.md`
- Contributing: `CONTRIBUTING.md`
