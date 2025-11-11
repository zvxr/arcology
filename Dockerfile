FROM acuvity/mcp-server-obsidian:latest

COPY patches/mcp_obsidian/tools.py /app/.venv/lib/python3.12/site-packages/mcp_obsidian/tools.py
