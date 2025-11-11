import os
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Query
import httpx

app = FastAPI(title="MCP Bridge", version="1.0")

def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


MCP_ENDPOINT_URL = os.getenv("MCP_ENDPOINT_URL", "").rstrip("/")
OBSIDIAN_REST_URL = os.getenv("OBSIDIAN_REST_URL", "").rstrip("/")
OBSIDIAN_API_KEY = os.getenv("OBSIDIAN_API_KEY", "")
OBSIDIAN_VERIFY_SSL = _env_bool("OBSIDIAN_VERIFY_SSL", default=False)
MCP_FIRST = _env_bool("MCP_FIRST", default=True)

# ---------- MCP helpers (JSON-RPC over HTTP) ----------

async def mcp_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not MCP_ENDPOINT_URL:
        raise RuntimeError("MCP endpoint not configured.")
    payload = {"jsonrpc": "2.0", "id": "1", "method": method, "params": params}
    async with httpx.AsyncClient(timeout=20, verify=OBSIDIAN_VERIFY_SSL) as client:
        r = await client.post(MCP_ENDPOINT_URL, json=payload)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        return data.get("result", {})

async def mcp_tool_list() -> List[Dict[str, Any]]:
    # Adjust if your server exposes a different method name
    return (await mcp_call("tools/list", {})).get("tools", [])

async def mcp_search(query: str) -> List[Dict[str, Any]]:
    tools = await mcp_tool_list()
    tool_name = None
    for t in tools:
        if "search" in (t.get("name") or "").lower():
            tool_name = t["name"]
            break
    if not tool_name:
        raise RuntimeError("No MCP search tool found.")
    params = {"name": tool_name, "arguments": {"query": query}}
    result = await mcp_call("tools/call", params)

    hits = result.get("result") or result.get("data") or result
    if isinstance(hits, dict) and "items" in hits:
        hits = hits["items"]
    if not isinstance(hits, list):
        hits = [hits]
    return hits

# ---------- Obsidian Local REST fallback ----------

async def obsidian_search(query: str, context_length: int = 120) -> List[Dict[str, Any]]:
    if not OBSIDIAN_REST_URL:
        raise RuntimeError("Obsidian REST URL not configured.")
    headers = {}
    if OBSIDIAN_API_KEY:
        headers["Authorization"] = f"Bearer {OBSIDIAN_API_KEY}"
    async with httpx.AsyncClient(timeout=20, verify=OBSIDIAN_VERIFY_SSL) as client:
        params = {"query": query, "contextLength": context_length}
        r = await client.post(f"{OBSIDIAN_REST_URL}/search/simple/", params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        hits = []
        iterable = data if isinstance(data, list) else data.get("results", [])
        for item in iterable:
            hits.append({
                "path": item.get("path") or item.get("file") or "",
                "snippet": item.get("snippet") or item.get("preview") or "",
                "score": item.get("score"),
            })
        return hits

# ---------- Unified facade ----------

async def unified_search(query: str) -> List[Dict[str, Any]]:
    last_err = None
    if MCP_FIRST:
        try:
            return await mcp_search(query)
        except Exception as e:
            last_err = e
    try:
        return await obsidian_search(query)
    except Exception as e:
        if last_err:
            raise HTTPException(status_code=502, detail=f"MCP failed: {last_err}; REST failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/query")
async def http_query(q: str = Query(..., description="Search query")):
    results = await unified_search(q)
    short = []
    for h in results[:20]:
        short.append({
            "path": h.get("path") or h.get("id") or "",
            "snippet": (h.get("snippet") or "")[:240],
            "score": h.get("score"),
        })
    return {"query": q, "count": len(results), "results": short}
