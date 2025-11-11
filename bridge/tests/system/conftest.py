import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the running bridge service"""
    return os.getenv("TEST_BASE_URL", "http://localhost:8787")


@pytest.fixture(scope="session")
def auth_token() -> str:
    """Bearer token for MCP endpoint authentication"""
    token = os.getenv("ARCOLOGY_MCP_KEY")
    if not token:
        raise ValueError(
            "ARCOLOGY_MCP_KEY environment variable is required but not set"
        )
    return token
