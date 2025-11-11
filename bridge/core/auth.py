from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from bridge.core.config import ARCOLOGY_MCP_KEY

security = HTTPBearer()


def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> None:
    if not ARCOLOGY_MCP_KEY:
        raise HTTPException(status_code=500, detail="Server missing ARCOLOGY_MCP_KEY")
    if credentials.credentials != ARCOLOGY_MCP_KEY:
        raise HTTPException(status_code=403, detail="Invalid bearer token")
