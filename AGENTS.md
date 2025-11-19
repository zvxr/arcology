# Repository Guidelines

## Project Structure & Module Organization
`docker-compose.yml` orchestrates `mcp-bridge`, the Obsidian proxy, and ngrok; treat it as canonical for ports, env, and container names. Application code lives in `bridge/` (FastAPI server, models, routes, services) and relies on resources in `assets/` plus overlay patches in `patches/`. Tests live in `bridge/tests`; wire any new routers through `bridge/server.py`.

## Build, Test, and Development Commands
Always use the Makefile: `make run` rebuilds and restarts the stack in the background, while `make ngrok-url` prints the public HTTPS tunnel exposed by the ngrok container. Linting and formatting stay containerized: `make format` (Ruff format + autofix), `make lint` (Ruff + Pyright), `make test` (pytest system suite), and `make checks` for the full trio before requesting review.

## Coding Style & Naming Conventions
Target Python 3.12 with four-space indentation, explicit module-level imports, and snake_case identifiers; reserve PascalCase for Pydantic models and kebab-case for Compose services. Compose files stay two-space indented, and service names should match their containers. Environment keys use uppercase snake_case (`OBSIDIAN_VAULT`, `NGROK_REGION`, `NGROK_AUTHTOKEN`) and must be documented via `.env.example` placeholders such as `CHANGE_ME`.

## Testing Guidelines
Pytest backs every change. The authoritative suite lives in `bridge/tests/system` and executes through `make test`, which runs inside the `mcp-bridge` container to match CI. Name tests after behavior (`test_proxy_handles_expired_tokens`) and expand coverage whenever routes, services, or compose wiring change.

## Commit & Pull Request Guidelines
Structure commit summaries around the user-facing outcome plus primary modules touched. Never open a PR or hand work to review until `make checks` passes, and avoid git commits until reviewers approve the diff. Reference the relevant bead ID in PR descriptions and call out any manual rollout steps (e.g., rerunning `make run`).

## Issue Tracking with Beads
All work starts with `bd ready --json`, gets claimed via `bd update <id> --status in_progress --json`, and finishes with `bd close <id> --reason "Done" --json`. Log discovered follow-ups using `bd create "Found issue" -p <priority> --deps discovered-from:<parent-id>` instead of ad-hoc TODOs so the board stays authoritative.

## Security & Configuration Tips
Never edit or commit `.env`; source it locally so Compose can inject `OBSIDIAN_*` and ngrok credentials. When overriding upstream Obsidian or MCP assets, store the diff under `patches/` with a short header explaining the upstream version and intent, and mention the patch whenever you touch related code.
