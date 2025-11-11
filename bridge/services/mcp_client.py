from typing import Any, Dict, List

from bridge.core.config import MCP_ENDPOINT_URL
from bridge.core.logger import get_logger
from bridge.services.http_client import get_http_client

logger = get_logger(__name__)


class MCPClient:
    """Client for interacting with upstream MCP server"""

    def __init__(self) -> None:
        self.endpoint_url = MCP_ENDPOINT_URL

    async def call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an MCP JSON-RPC call"""
        if not self.endpoint_url:
            raise RuntimeError("MCP endpoint not configured.")
        payload = {"jsonrpc": "2.0", "id": "1", "method": method, "params": params}
        client = get_http_client()
        resp = await client.post(self.endpoint_url, json=payload)
        resp.raise_for_status()
        json_resp = resp.json()
        if "error" in json_resp:
            logger.error(f"MCP error hitting {self.endpoint_url}: {json_resp}")
            raise RuntimeError(f"MCP error: {json_resp['error']}")
        return json_resp.get("result", {})

    async def tool_list(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        return (await self.call("tools/list", {})).get("tools", [])

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search using the MCP server's search tool"""
        tools = await self.tool_list()
        tool_name = None
        for t in tools:
            if "search" in (t.get("name") or "").lower():
                tool_name = t["name"]
                break
        if not tool_name:
            raise RuntimeError("No MCP search tool found.")
        params = {"name": tool_name, "arguments": {"query": query}}
        result = await self.call("tools/call", params)

        hits = result.get("result") or result.get("data") or result
        if isinstance(hits, dict) and "items" in hits:
            hits = hits["items"]
        if not isinstance(hits, list):
            hits = [hits]
        return hits
