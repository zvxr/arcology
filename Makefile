# Environment Variables
# - These are variables for the MCP + ngrok stack.
# - These are loaded from the .env file.
# - Include .env file to make variables available to commands
-include .env
export

MCP_PORT ?= $(shell grep -E '^MCP_PORT=' .env 2>/dev/null | tail -n 1 | cut -d= -f2)
MCP_PORT ?= 3333

.PHONY: help run ngrok-url format lint test checks

# Tool Commands
# - These are commands mostly for debugging and development.
help:
	@echo "make run         # Build & start MCP + ngrok stack in the background"
	@echo "make ngrok-url   # Print the current public ngrok URL"
	@echo "make format      # Format code using ruff (runs in docker container)"
	@echo "make lint        # Lint code using ruff and pyright (runs in docker container)"
	@echo "make test        # Run system tests (runs in docker container)"
	@echo "make checks      # Run format, lint, and test"

ngrok-url:
	@docker compose exec ngrok sh -c 'curl -s http://localhost:4040/api/tunnels' | \
		python3 -c "import json,sys; data=json.load(sys.stdin); print('\n'.join(t.get('public_url','') for t in data.get('tunnels',[]) if t.get('public_url')))"

# Linting / Testing Commands
# - These are commands for linting and testing the code.
# - Agents should run these when making changes to the code.
format:
	@docker compose exec mcp-bridge ruff format /app/bridge
	@docker compose exec mcp-bridge ruff check --fix /app/bridge

lint:
	@docker compose exec mcp-bridge ruff check /app/bridge
	@docker compose exec -e PYTHONWARNINGS=ignore::DeprecationWarning:nodeenv mcp-bridge pyright /app/bridge

test:
	@docker compose exec -e ARCOLOGY_MCP_KEY="$${ARCOLOGY_MCP_KEY}" mcp-bridge pytest /app/bridge/tests/system -vv -s

checks: format lint test

# Run Commands
# - These are commands for running the MCP + ngrok stack.
# - Stack always runs in the background. This can be used to restart the stack, but it should never be stopped manually.
run:
	@docker compose up -d --build
	@echo "Stack is running. Use 'make logs' to tail output or 'make ngrok-url' to fetch the public URL."
