import pytest

from bridge.models.obsidian import (
    ObsidianQueryResponse,
    ObsidianReadResponse,
    ObsidianSearchHit,
    ObsidianSearchRequest,
    ObsidianSearchResponse,
    ObsidianWriteRequest,
    ObsidianWriteResponse,
)


class TestObsidianSearchHit:
    def test_create_search_hit(self) -> None:
        hit = ObsidianSearchHit(path="test/path.md", snippet="snippet text", score=0.5)
        assert hit.path == "test/path.md"
        assert hit.snippet == "snippet text"
        assert hit.score == 0.5

    def test_create_search_hit_without_score(self) -> None:
        hit = ObsidianSearchHit(path="test/path.md", snippet="snippet text", score=None)
        assert hit.path == "test/path.md"
        assert hit.snippet == "snippet text"
        assert hit.score is None


class TestObsidianSearchRequest:
    def test_create_search_request(self) -> None:
        request = ObsidianSearchRequest(query="test query", context_length=120)
        assert request.query == "test query"
        assert request.context_length == 120

    def test_create_search_request_with_context_length(self) -> None:
        request = ObsidianSearchRequest(query="test query", context_length=200)
        assert request.query == "test query"
        assert request.context_length == 200


class TestObsidianSearchResponse:
    def test_create_search_response(self) -> None:
        hits = [
            ObsidianSearchHit(path="path1.md", snippet="snippet1", score=0.5),
            ObsidianSearchHit(path="path2.md", snippet="snippet2", score=0.3),
        ]
        response = ObsidianSearchResponse(items=hits)
        assert len(response.items) == 2
        assert response.items[0].path == "path1.md"
        assert response.items[1].path == "path2.md"

    def test_create_empty_search_response(self) -> None:
        response = ObsidianSearchResponse(items=[])
        assert len(response.items) == 0


class TestObsidianReadResponse:
    def test_create_read_response(self) -> None:
        response = ObsidianReadResponse(
            path="test/path.md", content="file content here"
        )
        assert response.path == "test/path.md"
        assert response.content == "file content here"


class TestObsidianWriteRequest:
    def test_create_write_request(self) -> None:
        request = ObsidianWriteRequest(path="test/path.md", content="new content")
        assert request.path == "test/path.md"
        assert request.content == "new content"


class TestObsidianWriteResponse:
    def test_create_write_response(self) -> None:
        response = ObsidianWriteResponse(path="test/path.md", ok=True)
        assert response.path == "test/path.md"
        assert response.ok is True

    def test_create_write_response_failed(self) -> None:
        response = ObsidianWriteResponse(path="test/path.md", ok=False)
        assert response.path == "test/path.md"
        assert response.ok is False


class TestObsidianQueryResponse:
    def test_create_query_response(self) -> None:
        results = [
            ObsidianSearchHit(path="path1.md", snippet="snippet1", score=0.5),
            ObsidianSearchHit(path="path2.md", snippet="snippet2", score=0.3),
        ]
        response = ObsidianQueryResponse(query="test", count=2, results=results)
        assert response.query == "test"
        assert response.count == 2
        assert len(response.results) == 2
