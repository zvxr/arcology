from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from bridge.core.auth import verify_bearer_token
from bridge.core.config import APP_NAME
from bridge.services.obsidian_client import ObsidianClient

router = APIRouter()


def _tool(name: str, description: str, input_schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": f"{APP_NAME}.{name}",
        "description": description,
        "input_schema": input_schema,
    }


TOOLS = [
    _tool(
        "search",
        "Search Obsidian notes by text query.",
        {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
    _tool(
        "read",
        "Read a note by relative path (e.g., 'Magic/Boros.md').",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    ),
    _tool(
        "write",
        "Write (create/overwrite) a note at relative path.",
        {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    ),
    _tool(
        "list.files",
        "List files under a directory (relative). If omitted, may list vault root(s) if supported.",
        {"type": "object", "properties": {"dir": {"type": "string"}}, "required": []},
    ),
]


def _mcp_ok(result: Any, *, id_val: str = "1") -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_val, "result": result}


def _mcp_err(message: str, *, id_val: str = "1", code: int = -32000) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_val, "error": {"code": code, "message": message}}


@router.post("/mcp")
async def mcp(req: Request, _auth: None = Depends(verify_bearer_token)) -> JSONResponse:
    """MCP protocol endpoint"""
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

            obsidian_client = ObsidianClient()

            # arcology.search
            if name == f"{APP_NAME}.search":
                q = args.get("query") or ""
                results = await obsidian_client.search(q)
                return JSONResponse(_mcp_ok({"items": results}, id_val=id_val))

            # arcology.read
            if name == f"{APP_NAME}.read":
                path = args.get("path") or ""
                content = await obsidian_client.read(path)
                return JSONResponse(
                    _mcp_ok({"path": path, "content": content}, id_val=id_val)
                )

            # arcology.write
            if name == f"{APP_NAME}.write":
                path = args.get("path") or ""
                content = args.get("content") or ""
                res = await obsidian_client.write(path, content)
                return JSONResponse(_mcp_ok(res, id_val=id_val))

            # arcology.list.files
            if name == f"{APP_NAME}.list.files":
                dir_arg = args.get("dir")
                files = await obsidian_client.list_files(dir_arg)
                return JSONResponse(_mcp_ok({"files": files}, id_val=id_val))

            return JSONResponse(
                _mcp_err(f"Unknown tool: {name}", id_val=id_val), status_code=400
            )

        if method in ("ping", "mcp.ping"):
            return JSONResponse(_mcp_ok({"ok": True}, id_val=id_val))

        return JSONResponse(
            _mcp_err(f"Unknown method: {method}", id_val=id_val), status_code=400
        )

    except HTTPException as he:
        return JSONResponse(
            _mcp_err(he.detail, id_val=id_val), status_code=he.status_code
        )
    except Exception as e:
        return JSONResponse(_mcp_err(str(e), id_val=id_val), status_code=500)
