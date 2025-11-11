import os
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse
import httpx

# ----------------- App & Env -----------------

app = FastAPI(title="MCP Bridge (archology)", version="1.0")

def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

# Upstream MCP (optional) + Obsidian REST
MCP_ENDPOINT_URL     = os.getenv("MCP_ENDPOINT_URL", "").rstrip("/")
OBSIDIAN_REST_URL    = os.getenv("OBSIDIAN_REST_URL", "").rstrip("/")
OBSIDIAN_API_KEY     = os.getenv("OBSIDIAN_API_KEY", "")
OBSIDIAN_VERIFY_SSL  = _env_bool("OBSIDIAN_VERIFY_SSL", default=False)
MCP_FIRST            = _env_bool("MCP_FIRST", default=True)

# MCP server settings (this service exposes /mcp)
APP_NAME             = "archology"
ARCHOLOGY_MCP_KEY    = os.getenv("ARCHOLOGY_MCP_KEY", "")
REQUIRE_AUTH         = True  # always on per your request

# ----------------- Shared HTTP helpers -----------------

async def _client():
    # Reuse your OBISIDAN_VERIFY_SSL for all outbound TLS checks
    return httpx.AsyncClient(timeout=25, verify=OBSIDIAN_VERIFY_SSL)

def _pick(d, *paths, default=None):
    """Pick first existing nested key using dotted paths."""
    for p in paths:
        cur = d
        ok = True
        for k in p.split("."):
            if not isinstance(cur, dict) or k not in cur:
                ok = False
                break
            cur = cur[k]
        if ok:
            return cur
    return default

# ----------------- Upstream MCP client (optional) -----------------

async def mcp_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not MCP_ENDPOINT_URL:
        raise RuntimeError("MCP endpoint not configured.")
    payload = {"jsonrpc": "2.0", "id": "1", "method": method, "params": params}
    async with await _client() as client:
        r = await client.post(MCP_ENDPOINT_URL, json=payload)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        return data.get("result", {})

async def mcp_tool_list() -> List[Dict[str, Any]]:
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

# ----------------- Obsidian REST (your shapes kept) -----------------

async def _obsidian_get(path: str, *, params=None, headers=None):
    if not OBSIDIAN_REST_URL:
        raise RuntimeError("Obsidian REST URL not configured.")
    h = headers or {}
    if OBSIDIAN_API_KEY:
        h["Authorization"] = f"Bearer {OBSIDIAN_API_KEY}"
    async with await _client() as c:
        return await c.get(f"{OBSIDIAN_REST_URL}{path}", params=params, headers=h)

async def _obsidian_post(path: str, *, params=None, json_body=None, headers=None):
    if not OBSIDIAN_REST_URL:
        raise RuntimeError("Obsidian REST URL not configured.")
    h = {"Content-Type": "application/json", **(headers or {})}
    if OBSIDIAN_API_KEY:
        h["Authorization"] = f"Bearer {OBSIDIAN_API_KEY}"
    async with await _client() as c:
        return await c.post(f"{OBSIDIAN_REST_URL}{path}", params=params, json=json_body, headers=h)

# Your existing search (kept exactly, uses /search/simple/)
async def obsidian_search(query: str, context_length: int = 120) -> List[Dict[str, Any]]:
    if not OBSIDIAN_REST_URL:
        raise RuntimeError("Obsidian REST URL not configured.")
    headers = {}
    if OBSIDIAN_API_KEY:
        headers["Authorization"] = f"Bearer {OBSIDIAN_API_KEY}"
    async with await _client() as client:
        params = {"query": query, "contextLength": context_length}
        r = await client.post(f"{OBSIDIAN_REST_URL}/search/simple/", params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        data = r.json()

        # --- patched normalization so path/snippet are populated ---
        hits: List[Dict[str, Any]] = []

        # Primary iterable from your current API
        iterable = data if isinstance(data, list) else data.get("results", [])

        # Also try a few common wrappers many Obsidian REST plugins use
        if not iterable and isinstance(data, dict):
            for k in ("items", "files", "data", "result"):
                v = data.get(k)
                if isinstance(v, list):
                    iterable = v
                    break

        for item in iterable:
            # Try many path locations your plugin might use
            path = (
                item.get("path")
                or item.get("file")
                or item.get("filePath")
                or item.get("notePath")
                or (item.get("fileData", {}) or {}).get("path")
                or (item.get("document", {}) or {}).get("path")
                or item.get("id")
                or ""
            )

            # Best-effort snippet candidates
            snippet = (
                item.get("snippet")
                or item.get("preview")
                or item.get("context")
                or item.get("text")
                or ""
            )

            # Many plugins return matches: [{"text"/"preview"/"context", ...}, ...]
            if not snippet and isinstance(item.get("matches"), list) and item["matches"]:
                m0 = item["matches"][0]
                snippet = m0.get("text") or m0.get("preview") or m0.get("context") or ""

            # final fallbacks so you see *something* useful
            if not path and isinstance(item.get("file"), dict):
                path = item["file"].get("path") or ""

            if not snippet:
                try:
                    snippet = json.dumps(
                        {k: item.get(k) for k in ("path","file","filePath","notePath","snippet","preview","text") if k in item}
                    )[:240]
                except Exception:
                    snippet = ""

            hits.append({
                "path": path,
                "snippet": (snippet or "").strip(),
                "score": item.get("score"),
            })
        return hits

# Add read/write/list with common fallbacks (relative path style)
async def obsidian_read(path: str) -> str:
    # Try common endpoints; prefer text body when available
    for ep in ("/file", "/vault/file", "/read", "/vault/read"):
        try:
            r = await _obsidian_get(ep, params={"path": path})
            if r.status_code == 200:
                ct = r.headers.get("Content-Type", "")
                if "application/json" in ct:
                    data = r.json()
                    return data.get("content") or json.dumps(data, indent=2)
                return r.text
        except Exception:
            continue
    raise RuntimeError("Obsidian REST read not found")

async def obsidian_write(path: str, content: str) -> Dict[str, Any]:
    body = {"path": path, "content": content}
    for method, ep in (("POST", "/file"), ("PUT", "/file"),
                       ("POST", "/vault/file"), ("PUT", "/vault/file"),
                       ("POST", "/write"), ("PUT", "/write")):
        try:
            if method == "POST":
                r = await _obsidian_post(ep, json_body=body)
            else:
                async with await _client() as c:
                    h = {"Content-Type": "application/json"}
                    if OBSIDIAN_API_KEY:
                        h["Authorization"] = f"Bearer {OBSIDIAN_API_KEY}"
                    r = await c.put(f"{OBSIDIAN_REST_URL}{ep}", json=body, headers=h)
            if r.status_code in (200, 201, 204):
                try:
                    data = r.json()
                except Exception:
                    data = {"ok": True}
                data.setdefault("ok", True)
                data.setdefault("path", path)
                return data
        except Exception:
            continue
    raise RuntimeError("Obsidian REST write not found")

async def obsidian_list_files(dir_path: Optional[str]) -> List[str]:
    params = {"dir": dir_path} if dir_path else {}
    for ep in ("/list", "/files", "/vault/list", "/vault/files"):
        try:
            r = await _obsidian_get(ep, params=params)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return [str(x) for x in data]
                if isinstance(data, dict):
                    items = data.get("files") or data.get("items") or []
                    out: List[str] = []
                    for it in items:
                        p = _pick(it, "path", "file.path", "id")
                        if p:
                            out.append(p)
                    if out:
                        return out
        except Exception:
            continue
    return []

# ----------------- Unified facade (kept) -----------------

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

# ----------------- Bearer auth for /mcp -----------------

def bearer_auth(req: Request):
    if not REQUIRE_AUTH:
        return
    if not ARCHOLOGY_MCP_KEY:
        raise HTTPException(500, "Server missing ARCHOLOGY_MCP_KEY")
    auth = req.headers.get("authorization")
    if not auth:
        raise HTTPException(401, "Missing Authorization header")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(401, "Malformed Authorization header")
    if parts[1].strip() != ARCHOLOGY_MCP_KEY:
        raise HTTPException(403, "Invalid bearer token")

# ----------------- MCP Protocol (/mcp) -----------------

def _tool(name: str, description: str, input_schema: Dict[str, Any]) -> Dict[str, Any]:
    return {"name": f"{APP_NAME}.{name}", "description": description, "input_schema": input_schema}

TOOLS = [
    _tool("search", "Search Obsidian notes by text query.", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }),
    _tool("read", "Read a note by relative path (e.g., 'Magic/Boros.md').", {
        "type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]
    }),
    _tool("write", "Write (create/overwrite) a note at relative path.", {
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"]
    }),
    _tool("list.files", "List files under a directory (relative). If omitted, may list vault root(s) if supported.", {
        "type": "object", "properties": {"dir": {"type": "string"}}, "required": []
    }),
]

def _mcp_ok(result: Any, *, id_val="1"):
    return {"jsonrpc": "2.0", "id": id_val, "result": result}

def _mcp_err(message: str, *, id_val="1", code: int = -32000):
    return {"jsonrpc": "2.0", "id": id_val, "error": {"code": code, "message": message}}

@app.post("/mcp")
async def mcp(req: Request, _auth=Depends(bearer_auth)):
    body = await req.json()
    method = body.get("method")
    params = body.get("params", {}) or {}
    id_val = body.get("id", "1")

    try:
        if method == "tools/list":
            return JSONResponse(_mcp_ok({"tools": TOOLS}, id_val=id_val))

        if method == "tools/call":
            name = params.get("name") or ""
            args = params.get("arguments") or {}

            # archology.search
            if name == f"{APP_NAME}.search":
                q = args.get("query") or ""
                results = await obsidian_search(q)
                return JSONResponse(_mcp_ok({"items": results}, id_val=id_val))

            # archology.read
            if name == f"{APP_NAME}.read":
                path = args.get("path") or ""
                content = await obsidian_read(path)
                return JSONResponse(_mcp_ok({"path": path, "content": content}, id_val=id_val))

            # archology.write
            if name == f"{APP_NAME}.write":
                path = args.get("path") or ""
                content = args.get("content") or ""
                res = await obsidian_write(path, content)
                return JSONResponse(_mcp_ok(res, id_val=id_val))

            # archology.list.files
            if name == f"{APP_NAME}.list.files":
                dir_arg = args.get("dir")
                files = await obsidian_list_files(dir_arg)
                return JSONResponse(_mcp_ok({"files": files}, id_val=id_val))

            return JSONResponse(_mcp_err(f"Unknown tool: {name}", id_val=id_val), status_code=400)

        if method in ("ping", "mcp.ping"):
            return JSONResponse(_mcp_ok({"ok": True}, id_val=id_val))

        return JSONResponse(_mcp_err(f"Unknown method: {method}", id_val=id_val), status_code=400)

    except HTTPException as he:
        return JSONResponse(_mcp_err(he.detail, id_val=id_val), status_code=he.status_code)
    except Exception as e:
        return JSONResponse(_mcp_err(str(e), id_val=id_val), status_code=500)
