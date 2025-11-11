# Archology

- Simple project for self-hosting MCP server to expose integrations to AI tools.
- WIP

![Arcology](assets/arcology.jpg)

## Tools
- Cursor AI
- ChatGPT
- Codex

## Integrations
- Obsidian

## Workflow

```
AI Agent >> MCP over HTTPS >> ngrok tunnel >> Archology MCP Bridge >> Obsidian REST API
```


## Structure
- Bridge is a simple FastAPI app.
- Runs locally (requires Docker Desktop).

## Notes
- Custom connectors for native ChatGPT are not fully rolled out to non-enterprise.