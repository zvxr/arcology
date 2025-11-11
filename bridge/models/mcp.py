from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MCPError(BaseModel):
    """MCP error object"""

    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(None, description="Optional error data")


class MCPRequest(BaseModel):
    """MCP JSON-RPC 2.0 request"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Union[str, int] = Field(..., description="Request ID")
    method: str = Field(..., description="Method name")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Method parameters"
    )


class MCPResponse(BaseModel):
    """MCP JSON-RPC 2.0 response"""

    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    id: Union[str, int] = Field(..., description="Request ID")
    result: Optional[Any] = Field(None, description="Result (if successful)")
    error: Optional[MCPError] = Field(None, description="Error (if failed)")

    @classmethod
    def success(cls, result: Any, id_val: Union[str, int] = "1") -> "MCPResponse":
        """Create a successful response"""
        return cls(jsonrpc="2.0", id=id_val, result=result, error=None)

    @classmethod
    def create_error(
        cls,
        message: str,
        id_val: Union[str, int] = "1",
        code: int = -32000,
        data: Optional[Any] = None,
    ) -> "MCPResponse":
        """Create an error response"""
        return cls(
            jsonrpc="2.0",
            id=id_val,
            result=None,
            error=MCPError(code=code, message=message, data=data),
        )


class MCPTool(BaseModel):
    """MCP tool definition"""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="Input schema (JSON Schema)")


class MCPToolsListResult(BaseModel):
    """Result for tools/list method"""

    tools: List[MCPTool] = Field(..., description="List of available tools")


class MCPToolCallArguments(BaseModel):
    """Arguments for tool calls"""

    query: Optional[str] = Field(
        default=None, description="Search query (for search tool)"
    )
    path: Optional[str] = Field(
        default=None, description="File path (for read/write tools)"
    )
    content: Optional[str] = Field(
        default=None, description="File content (for write tool)"
    )
    dir: Optional[str] = Field(
        default=None, description="Directory path (for list.files tool)"
    )


class MCPToolCallParams(BaseModel):
    """Parameters for tools/call method"""

    name: str = Field(..., description="Tool name to call")
    arguments: MCPToolCallArguments = Field(..., description="Tool arguments")
