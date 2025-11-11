# Repository Guidelines

## Project Structure & Module Organization
This repo is intentionally small: `docker-compose.yml` declares every MCP server, `.env` holds local secrets and tunables, `Dockerfile` extends upstream images, and `patches/` contains overrides such as the custom `mcp_obsidian/tools.py`. Keep docs, port maps, and runbooks in `docs/` so new operators can reason about deployments quickly. The stack currently ships with two services: `mcp-obsidian` (the patched server) and `ngrok` (HTTPS tunnel); both run under `restart: unless-stopped` so they auto-resume after Docker restarts.

## Build, Test, and Development Commands
The core workflow is Docker-based:
- `docker compose config` — sanity-checks YAML + env interpolation.
- `docker compose up -d --build` (or `make run`) — rebuilds patched images, starts both MCP + ngrok, and leaves them in the background.
- `docker compose logs -f` — tails combined logs; add `ngrok` or `mcp-obsidian` to scope.
- `make ngrok-url` — prints the active HTTPS endpoint by querying the ngrok admin API (needs `python3` on the host).
- `docker compose down` — stops containers without removing volumes. Use `--volumes` only when you intentionally want a fresh state.
Document any extra bootstrap (e.g., Obsidian plugin installs) in `docs/SETUP.md` and reference it from PRs.

# Configuration & Naming Conventions
Compose files use two-space indentation and kebab-case service names (`mcp-obsidian`, `mcp-notion`). Mirror that naming in container names and optional overlays to avoid drift. Store required variables in `.env` with uppercase snake keys (`OBSIDIAN_*`, `NGROK_AUTHTOKEN`, `NGROK_REGION`, optional `NGROK_DOMAIN`); never commit real secrets to docs or sample commands. If a value must be shared, provide a `.env.example` entry with `CHANGE_ME` tokens and explain sourcing steps. When overriding upstream behavior, keep patches small, documented at the top of each file, and note which upstream version they target.

## Build, Test, and Development Commands
- **CRITICAL**: Review the Makefile - it contains detailed directives for what Agents should run and when.
- **LINTING REQUIREMENT**: All code changes MUST pass linting before being presented for review:
  - Backend: Run `make backend-lint` (includes ruff + pyright) after making backend changes
  - Frontend: Run `make frontend-lint` after making frontend changes
  - Terraform: Run `make tf-lint` after making infrastructure changes
- **FORMATTING REQUIREMENT**: Run `make format` after making backend changes to ensure consistent code formatting

## Coding Style & Naming Conventions
- Target Python 3.12 with four-space indentation and snake_case module names.
- Keep type hints comprehensive to satisfy strict mypy; use FastAPI `Annotated` inputs.
- Always place imports at the top of the file. Do not place imports in functions.
- Avoid redundant comments. Most code is self-documenting.
- Avoid `getattr` or dictionary `.get` for attributes that always exist or should exist.
- Always look for opportunities to consolidate code. Use DRY principles.
- Run Ruff formatting and checking through the Make targets before pushing.
- Write React components in PascalCase (`components/UserProfile.js`) and hooks in
  camelCase.
- Keep React indentation at two spaces and API clients under `frontend/src/services`.
- Prefer using constants, avoid using raw hex codes for color. Check
  `frontend/app/utils` for already established constants and functions.

## Testing Guidelines
- Keep backend tests in `tests/backend` using `pytest` + `pytest-asyncio`; name files
  `test_*.py` and reuse factories from `tests/factories.py`.
- Keep frontend specs in `frontend/src/__tests__` with React Testing Library DOM
  assertions.
- Cover each new endpoint or UI flow with at least one success and one failure test.
- Avoid anything that would cause a running docker-compose stack to stop.
- Do not make any API calls or database changes when we are pointing to prod.

## Commit & Pull Request Guidelines
- Include summaries of changes.
- Request review only after containerized checks pass.
- **CRITICAL: NEVER commit without user review**: Always present changes for review first
- Confirm or display changes being made in code, but wait for instruction to create git commits.
- Do not `git commit` without first allowing user to review code changes.

## Other Important Guidelines
- Do not edit `.env`. It is dangerous to do so.

## Makefile as Source of Truth
The Makefile contains comprehensive agent directives and should be the primary reference for:
- When to run specific commands (linting, formatting, testing, deployment)
- What commands to run for different types of changes
- Which commands agents should avoid running unsupervised
- Proper sequencing of operations (e.g., format → lint → test → present changes)

**Always consult the Makefile comments before making changes to understand the proper workflow.**

## Issue Tracking with bd (beads)

**CRITICAL**: This project uses **bd (beads)** for ALL issue tracking. Never use markdown TODOs or other tracking methods.

### Essential Rules for Agents

- **Always use beads**: Track everything in beads, never create random TODO lists
- **Check ready work first**: `bd ready --json` before starting any work
- **Claim your task**: `bd update <id> --status in_progress --json`
- **Link discovered work**: `bd create "Found issue" -p 1 --deps discovered-from:<parent-id> --json`
- **Complete work**: `bd close <id> --reason "Done" --json`

### Quick Commands

```bash
# Check available work
bd ready --json

# Create new issue
bd create "Issue title" -t bug|feature|task -p 0-4 --json

# Update issue status
bd update bd-42 --status in_progress --json

# Complete work
bd close bd-42 --reason "Completed" --json
```