import json
import urllib.parse
from typing import Any, Dict, List, Optional

from bridge.core.config import OBSIDIAN_API_KEY, OBSIDIAN_REST_URL
from bridge.core.logger import get_logger
from bridge.services.http_client import get_http_client

logger = get_logger(__name__)


def _pick(d: Dict[str, Any], *paths: str, default: Any = None) -> Any:
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


class ObsidianClient:
    """Client for interacting with Obsidian REST API"""

    def __init__(self) -> None:
        self.rest_url = OBSIDIAN_REST_URL
        self.api_key = OBSIDIAN_API_KEY

    def _get_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get headers with authorization if API key is configured"""
        headers = extra or {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a GET request to Obsidian REST API"""
        if not self.rest_url:
            raise RuntimeError("Obsidian REST URL not configured.")
        client = get_http_client()
        h = self._get_headers(headers)
        r = await client.get(f"{self.rest_url}{path}", params=params, headers=h)
        return r

    async def _post(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a POST request to Obsidian REST API"""
        if not self.rest_url:
            raise RuntimeError("Obsidian REST URL not configured.")
        client = get_http_client()
        h = {"Content-Type": "application/json", **self._get_headers(headers)}
        r = await client.post(
            f"{self.rest_url}{path}", params=params, json=json_body, headers=h
        )
        return r

    async def _put(
        self,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a PUT request to Obsidian REST API"""
        if not self.rest_url:
            raise RuntimeError("Obsidian REST URL not configured.")
        client = get_http_client()
        h = {"Content-Type": "application/json", **self._get_headers(headers)}
        r = await client.put(f"{self.rest_url}{path}", json=json_body, headers=h)
        return r

    async def search(
        self, query: str, context_length: int = 120
    ) -> List[Dict[str, Any]]:
        """Search Obsidian notes by text query"""
        if not self.rest_url:
            raise RuntimeError("Obsidian REST URL not configured.")
        headers = self._get_headers()
        client = get_http_client()
        params: Dict[str, Any] = {"query": query, "contextLength": str(context_length)}
        r = await client.post(
            f"{self.rest_url}/search/simple/", params=params, headers=headers
        )
        r.raise_for_status()
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
                or item.get("filename")  # Obsidian REST API uses "filename" field
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
            if (
                not snippet
                and isinstance(item.get("matches"), list)
                and item["matches"]
            ):
                m0 = item["matches"][0]
                snippet = m0.get("text") or m0.get("preview") or m0.get("context") or ""

            # final fallbacks so you see *something* useful
            if not path and isinstance(item.get("file"), dict):
                path = item["file"].get("path") or ""

            if not snippet:
                try:
                    snippet = json.dumps(
                        {
                            k: item.get(k)
                            for k in (
                                "path",
                                "file",
                                "filePath",
                                "notePath",
                                "snippet",
                                "preview",
                                "text",
                            )
                            if k in item
                        }
                    )[:240]
                except Exception:
                    snippet = ""

            hits.append(
                {
                    "path": path,
                    "snippet": (snippet or "").strip(),
                    "score": item.get("score"),
                }
            )
        return hits

    async def read(self, path: str) -> str:
        """Read a note by relative path

        Based on obsidian-local-rest-api: https://github.com/coddingtonbear/obsidian-local-rest-api
        The endpoint is GET /vault/{path} where path is URL-encoded
        """
        # URL encode the path for use in URL
        encoded_path = urllib.parse.quote(path, safe="/")

        # Based on obsidian-local-rest-api docs, the endpoint is GET /vault/{path}
        endpoints_to_try = [
            f"/vault/{encoded_path}",  # Primary endpoint per obsidian-local-rest-api
            f"/vault/{path}",  # Try without encoding in case API handles it
            f"/file/{encoded_path}",
            f"/file/{path}",
        ]

        for ep in endpoints_to_try:
            try:
                r = await self._get(ep)

                if r.status_code == 200:
                    ct = r.headers.get("Content-Type", "")
                    if "application/json" in ct:
                        data = r.json()
                        # Try various content field names
                        content = (
                            data.get("content")
                            or data.get("text")
                            or data.get("body")
                            or json.dumps(data, indent=2)
                        )
                        return content
                    # Return text content directly
                    return r.text
                elif r.status_code == 404:
                    # Continue trying other endpoints
                    continue
                else:
                    # Log non-404 errors for debugging
                    logger.warning(
                        f"Unexpected status {r.status_code} from GET {ep}: {r.text[:200]}"
                    )
            except Exception as e:
                logger.debug(f"Error trying GET {ep}: {e}")
                continue

        raise RuntimeError(
            f"Obsidian REST read not found for path '{path}' - tried all endpoints"
        )

    async def write(self, path: str, content: str) -> Dict[str, Any]:
        """Write (create/overwrite) a note at relative path"""
        body = {"path": path, "content": content}
        for method, ep in (
            ("POST", "/file"),
            ("PUT", "/file"),
            ("POST", "/vault/file"),
            ("PUT", "/vault/file"),
            ("POST", "/write"),
            ("PUT", "/write"),
        ):
            try:
                if method == "POST":
                    r = await self._post(ep, json_body=body)
                else:
                    r = await self._put(ep, json_body=body)
                if r.status_code in (200, 201, 204):
                    try:
                        data: Dict[str, Any] = r.json()
                    except Exception:
                        data = {"ok": True}
                    if not isinstance(data, dict):
                        data = {"ok": True}
                    data.setdefault("ok", True)
                    data.setdefault("path", path)
                    return data
            except Exception:
                continue
        raise RuntimeError("Obsidian REST write not found")

    async def list_files(self, dir_path: Optional[str] = None) -> List[str]:
        """List files under a directory (relative). If omitted, may list vault root(s) if supported."""
        params = {"dir": dir_path} if dir_path else {}
        for ep in ("/list", "/files", "/vault/list", "/vault/files"):
            try:
                resp = await self._get(ep, params=params)
                if resp.status_code == 200:
                    json_resp = resp.json()
                    if isinstance(json_resp, list):
                        return [str(x) for x in json_resp]
                    if isinstance(json_resp, dict):
                        items = json_resp.get("files") or json_resp.get("items") or []
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
