import httpx

from bridge.core.config import OBSIDIAN_VERIFY_SSL

_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError(
            "HTTP client not initialized. Call startup_http_client() first."
        )
    return _http_client


async def startup_http_client() -> None:
    global _http_client
    _http_client = httpx.AsyncClient(timeout=25.0, verify=OBSIDIAN_VERIFY_SSL)


async def shutdown_http_client() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
