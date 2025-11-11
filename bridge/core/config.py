import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Upstream MCP + Obsidian REST
MCP_ENDPOINT_URL: str = os.getenv("MCP_ENDPOINT_URL", "").rstrip("/")
OBSIDIAN_REST_URL: str = os.getenv("OBSIDIAN_REST_URL", "").rstrip("/")
OBSIDIAN_API_KEY: str = os.getenv("OBSIDIAN_API_KEY", "")
OBSIDIAN_VERIFY_SSL: bool = _env_bool("OBSIDIAN_VERIFY_SSL", default=False)
MCP_FIRST: bool = _env_bool("MCP_FIRST", default=True)

# MCP server settings
APP_NAME: str = "arcology"
ARCOLOGY_MCP_KEY: str = os.getenv("ARCOLOGY_MCP_KEY", "")
