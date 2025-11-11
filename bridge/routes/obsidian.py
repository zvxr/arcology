from fastapi import APIRouter, HTTPException, Query

from bridge.core.config import MCP_FIRST
from bridge.services.mcp_client import MCPClient
from bridge.services.obsidian_client import ObsidianClient

router = APIRouter()


async def unified_search(query: str) -> list[dict]:
    """Unified search that tries MCP first (if configured) then falls back to Obsidian REST"""
    last_err = None
    if MCP_FIRST:
        try:
            mcp_client = MCPClient()
            return await mcp_client.search(query)
        except Exception as e:
            last_err = e
    try:
        obsidian_client = ObsidianClient()
        return await obsidian_client.search(query)
    except Exception as e:
        if last_err:
            raise HTTPException(
                status_code=502, detail=f"MCP failed: {last_err}; REST failed: {e}"
            )
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/obsidian/query")
async def query(q: str = Query(..., description="Search query")) -> dict:
    """Query Obsidian notes"""
    results = await unified_search(q)
    short = []
    for h in results[:20]:
        short.append(
            {
                "path": h.get("path") or h.get("id") or "",
                "snippet": (h.get("snippet") or "")[:240],
                "score": h.get("score"),
            }
        )
    return {"query": q, "count": len(results), "results": short}
