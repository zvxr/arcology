from typing import List, Optional

from pydantic import BaseModel, Field


class ObsidianSearchHit(BaseModel):
    """A single search result hit"""

    path: str = Field(..., description="File path")
    snippet: str = Field(..., description="Text snippet/context")
    score: Optional[float] = Field(default=None, description="Relevance score")


class ObsidianSearchRequest(BaseModel):
    """Request for Obsidian search"""

    query: str = Field(..., description="Search query")
    context_length: int = Field(default=120, description="Context length for snippets")


class ObsidianSearchResponse(BaseModel):
    """Response from Obsidian search"""

    items: List[ObsidianSearchHit] = Field(..., description="Search results")


class ObsidianReadResponse(BaseModel):
    """Response from Obsidian read operation"""

    path: str = Field(..., description="File path that was read")
    content: str = Field(..., description="File content")


class ObsidianWriteRequest(BaseModel):
    """Request for Obsidian write operation"""

    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="Content to write")


class ObsidianWriteResponse(BaseModel):
    """Response from Obsidian write operation"""

    ok: bool = Field(True, description="Whether the operation succeeded")
    path: str = Field(..., description="File path that was written")


class ObsidianQueryResponse(BaseModel):
    """Response for /obsidian/query endpoint"""

    query: str = Field(..., description="Search query")
    count: int = Field(..., description="Total number of results")
    results: List[ObsidianSearchHit] = Field(
        ..., description="Search results (limited)"
    )
