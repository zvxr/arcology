# Repository Guidelines

## Project Structure & Module Organization
- Everything revolves around the `docker-compose.yml` which runs local MCP server, Obsidian HTTP server, and reverse proxy via ngrok.
- Basic usage for agents and humans is driven through `Makefile`. Always prefer `make` commands to one-off commands.
- `bridge` is a FastAPI MCP server which provides MCP endpoints and Obsidian proxy.

## Build, Test, and Development Commands
The core workflow is Docker-based
- `make run` will rebuild and ensure the stack is running. It always runs in the background so as to be available to agents.
- `make ngrok-url` — prints the active HTTPS endpoint by querying the ngrok admin API (needs `python3` on the host).

# Configuration & Naming Conventions
Compose files use two-space indentation and kebab-case service names (`mcp-obsidian`, `mcp-notion`). Mirror that naming in container names and optional overlays to avoid drift. Store required variables in `.env` with uppercase snake keys (`OBSIDIAN_*`, `NGROK_AUTHTOKEN`, `NGROK_REGION`, optional `NGROK_DOMAIN`); never commit real secrets to docs or sample commands. If a value must be shared, provide a `.env.example` entry with `CHANGE_ME` tokens and explain sourcing steps. When overriding upstream behavior, keep patches small, documented at the top of each file, and note which upstream version they target.

## Build, Test, and Development Commands
- **CRITICAL**: Review the Makefile - it contains detailed directives for what Agents should run and when.
- **LINTING REQUIREMENT**: All code changes MUST pass linting before being presented for review. Run `make lint`.
- **FORMATTING REQUIREMENT**: Run `make format` after making backend changes to ensure consistent code formatting.
- Run `make test` when making changes to the bridge API server or any docker-compose changes to prevent regressions.
- Add testing as appropriate.

## Coding Style & Naming Conventions
- Target Python 3.12 with four-space indentation and snake_case module names.
- Always place imports at the top of the file. Do not place imports in functions.
- Avoid redundant comments. Most code is self-documenting.
- Avoid `getattr` or dictionary `.get` for attributes that always exist or should exist.
- Always look for opportunities to consolidate code. Use DRY principles.

## Commit & Pull Request Guidelines
- Include summaries of changes.
- Request review only after containerized checks pass.
- **CRITICAL: NEVER commit without user review**: Always present changes for review first
- Confirm or display changes being made in code, but wait for instruction to create git commits.
- Do not `git commit` without first allowing user to review code changes.

## Other Important Guidelines
- **CRITICAL: NEVER edit `.env` or commit it. It should not even be read directly by agents.

## Issue Tracking with bd (beads)

**CRITICAL**: This project uses **bd (beads)** for ALL issue tracking. Never use markdown TODOs or other tracking methods.

### Essential Rules for Agents

- **Always use beads**: Track everything in beads, never create random TODO lists
- **Check ready work first**: `bd ready --json` before starting any work
- **Claim your task**: `bd update <id> --status in_progress --json`
- **Link discovered work**: `bd create "Found issue" -p 1 --deps discovered-from:<parent-id> --json`
- **Complete work**: `bd close <id> --reason "Done" --json`