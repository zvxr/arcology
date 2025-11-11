import pytest

from bridge.models.mcp import (
    MCPError,
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPToolCallArguments,
    MCPToolCallParams,
    MCPToolsListResult,
)


class TestMCPError:
    def test_create_error(self) -> None:
        error = MCPError(code=-32000, message="Test error", data=None)
        assert error.code == -32000
        assert error.message == "Test error"
        assert error.data is None

    def test_create_error_with_data(self) -> None:
        error = MCPError(
            code=-32600, message="Invalid Request", data={"field": "value"}
        )
        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data == {"field": "value"}


class TestMCPRequest:
    def test_create_request(self) -> None:
        request = MCPRequest(
            jsonrpc="2.0", id="1", method="tools/list", params={"test": "value"}
        )
        assert request.jsonrpc == "2.0"
        assert request.id == "1"
        assert request.method == "tools/list"
        assert request.params == {"test": "value"}

    def test_create_request_without_params(self) -> None:
        request = MCPRequest(jsonrpc="2.0", id=2, method="ping", params=None)
        assert request.jsonrpc == "2.0"
        assert request.id == 2
        assert request.method == "ping"
        assert request.params is None

    def test_request_serialization(self) -> None:
        request = MCPRequest(jsonrpc="2.0", id="1", method="tools/list", params={})
        data = request.model_dump()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert data["method"] == "tools/list"
        assert data["params"] == {}


class TestMCPResponse:
    def test_create_success_response(self) -> None:
        response = MCPResponse.success(result={"tools": []}, id_val="1")
        assert response.jsonrpc == "2.0"
        assert response.id == "1"
        assert response.result == {"tools": []}
        assert response.error is None

    def test_create_error_response(self) -> None:
        response = MCPResponse.create_error(
            message="Test error", id_val="1", code=-32000
        )
        assert response.jsonrpc == "2.0"
        assert response.id == "1"
        assert response.result is None
        assert response.error is not None
        assert response.error.code == -32000
        assert response.error.message == "Test error"

    def test_error_response_serialization(self) -> None:
        response = MCPResponse.create_error(
            message="Test error", id_val="1", code=-32000
        )
        data = response.model_dump(exclude_none=True)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert "result" not in data or data["result"] is None
        assert "error" in data
        assert data["error"]["code"] == -32000
        assert data["error"]["message"] == "Test error"

    def test_response_serialization(self) -> None:
        response = MCPResponse.success(result={"ok": True}, id_val="1")
        data = response.model_dump(exclude_none=True)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "1"
        assert data["result"] == {"ok": True}
        assert "error" not in data


class TestMCPTool:
    def test_create_tool(self) -> None:
        tool = MCPTool(
            name="test.tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
        )
        assert tool.name == "test.tool"
        assert tool.description == "Test tool"
        assert tool.input_schema == {
            "type": "object",
            "properties": {"query": {"type": "string"}},
        }


class TestMCPToolsListResult:
    def test_create_tools_list_result(self) -> None:
        tools = [
            MCPTool(
                name="test.tool1",
                description="Tool 1",
                input_schema={"type": "object"},
            ),
            MCPTool(
                name="test.tool2",
                description="Tool 2",
                input_schema={"type": "object"},
            ),
        ]
        result = MCPToolsListResult(tools=tools)
        assert len(result.tools) == 2
        assert result.tools[0].name == "test.tool1"
        assert result.tools[1].name == "test.tool2"


class TestMCPToolCallArguments:
    def test_create_search_arguments(self) -> None:
        args = MCPToolCallArguments(
            query="test query", path=None, content=None, dir=None
        )
        assert args.query == "test query"
        assert args.path is None
        assert args.content is None
        assert args.dir is None

    def test_create_read_arguments(self) -> None:
        args = MCPToolCallArguments(
            query=None, path="test/path.md", content=None, dir=None
        )
        assert args.path == "test/path.md"
        assert args.query is None

    def test_create_write_arguments(self) -> None:
        args = MCPToolCallArguments(
            query=None, path="test/path.md", content="file content", dir=None
        )
        assert args.path == "test/path.md"
        assert args.content == "file content"

    def test_create_list_files_arguments(self) -> None:
        args = MCPToolCallArguments(query=None, path=None, content=None, dir="test/dir")
        assert args.dir == "test/dir"
        assert args.path is None


class TestMCPToolCallParams:
    def test_create_tool_call_params(self) -> None:
        args = MCPToolCallArguments(query="test")
        params = MCPToolCallParams(name="test.search", arguments=args)
        assert params.name == "test.search"
        assert params.arguments.query == "test"
