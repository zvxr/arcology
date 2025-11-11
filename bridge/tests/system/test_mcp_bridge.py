import httpx
import pytest


@pytest.mark.asyncio
async def test_health_check(base_url: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_tools(base_url: str, auth_token: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/mcp",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
                "params": {},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert "result" in data
        assert "tools" in data["result"]
        assert isinstance(data["result"]["tools"], list)
        assert len(data["result"]["tools"]) > 0

        # Verify expected tools are present
        tool_names = [tool["name"] for tool in data["result"]["tools"]]
        assert "arcology.search" in tool_names
        assert "arcology.read" in tool_names
        assert "arcology.write" in tool_names
        assert "arcology.list.files" in tool_names


@pytest.mark.asyncio
async def test_search_boros(base_url: str, auth_token: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/mcp",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "arcology.search",
                    "arguments": {"query": "boros"},
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert "result" in data
        assert "items" in data["result"]
        assert isinstance(data["result"]["items"], list)


@pytest.mark.asyncio
async def test_read_first_search_result(base_url: str, auth_token: str) -> None:
    # First, perform the search
    async with httpx.AsyncClient() as client:
        # Search for "boros"
        search_response = await client.post(
            f"{base_url}/mcp",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "arcology.search",
                    "arguments": {"query": "boros"},
                },
            },
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert "result" in search_data
        assert "items" in search_data["result"]

        items = search_data["result"]["items"]
        if not items:
            pytest.skip("No search results found for 'boros'; try a different query")

        # Get the first item's path
        first_path = items[0].get("path")
        if not first_path:
            pytest.skip("First search result has no path")

        # Read the first result
        read_response = await client.post(
            f"{base_url}/mcp",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "arcology.read",
                    "arguments": {"path": first_path},
                },
            },
        )
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data["jsonrpc"] == "2.0"
        assert read_data["id"] == "1"
        assert "result" in read_data
        assert "path" in read_data["result"]
        assert "content" in read_data["result"]
        assert read_data["result"]["path"] == first_path
        assert isinstance(read_data["result"]["content"], str)
        assert len(read_data["result"]["content"]) > 0
