# Default port and env loading
MCP_PORT ?= $(shell grep -E '^MCP_PORT=' .env 2>/dev/null | tail -n 1 | cut -d= -f2)
MCP_PORT ?= 3333

.PHONY: help run compose-up compose-down logs ngrok-url

help:
	@echo "make run         # Build & start MCP + ngrok stack in the background"
	@echo "make compose-up  # docker compose up -d --build"
	@echo "make compose-down# Stop all services"
	@echo "make logs        # Tail combined logs"
	@echo "make ngrok-url   # Print the current public ngrok URL"

compose-up:
	@docker compose up -d --build

compose-down:
	@docker compose down

logs:
	@docker compose logs -f

ngrok-url:
	@docker compose exec ngrok sh -c 'curl -s http://localhost:4040/api/tunnels' | \
		python3 -c "import json,sys; data=json.load(sys.stdin); print('\n'.join(t.get('public_url','') for t in data.get('tunnels',[]) if t.get('public_url')))"

run: compose-up
	@echo "Stack is running. Use 'make logs' to tail output or 'make ngrok-url' to fetch the public URL."
