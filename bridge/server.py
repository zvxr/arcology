from contextlib import asynccontextmanager

from fastapi import FastAPI

from bridge.core.logger import setup_logging
from bridge.routes import health, mcp, obsidian
from bridge.services.http_client import shutdown_http_client, startup_http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    setup_logging()
    await startup_http_client()
    yield
    # Shutdown
    await shutdown_http_client()


app = FastAPI(title="MCP Bridge (arcology)", version="1.0", lifespan=lifespan)

# Include routers
app.include_router(health.router)
app.include_router(obsidian.router)
app.include_router(mcp.router)
