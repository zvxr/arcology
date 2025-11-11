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

## Configuration & Naming Conventions
Compose files use two-space indentation and kebab-case service names (`mcp-obsidian`, `mcp-notion`). Mirror that naming in container names and optional overlays to avoid drift. Store required variables in `.env` with uppercase snake keys (`OBSIDIAN_*`, `NGROK_AUTHTOKEN`, `NGROK_REGION`, optional `NGROK_DOMAIN`); never commit real secrets to docs or sample commands. If a value must be shared, provide a `.env.example` entry with `CHANGE_ME` tokens and explain sourcing steps. When overriding upstream behavior, keep patches small, documented at the top of each file, and note which upstream version they target.

## Validation Guidelines
Before pushing, run `docker compose up` locally and hit the exposed MCP port (default `localhost:3333`) with a simple curl or MCP client to confirm the handshake works. Add lightweight smoke scripts under `scripts/` if automated checks grow beyond a one-liner. Record any manual verification steps—Obsidian vault paths, mock API responses, healthcheck expectations—in PR descriptions.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat(compose): add notion connector`). Group discrete services or config changes into their own commits to ease rollbacks. Every PR should include: summary of added/changed services, required env additions, local verification commands, and screenshots/log excerpts if UI-level validation was necessary. Call out breaking port changes or new external dependencies in both the PR body and commit messages.
