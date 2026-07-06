"""Nebula API main entrypoint."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.api import chat
from app.core import mcp_manager
from app.core.config import get_logger, settings
from app.core.database import init_db

logger = get_logger(__name__)

if not settings.GOOGLE_MAPS_API_KEY:
    logger.warning(
        "GOOGLE_MAPS_API_KEY is missing from .env — Maps MCP may fail to start."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP server lifecycle during application startup and shutdown."""
    maps_key = settings.GOOGLE_MAPS_API_KEY

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-google-maps"],
        env={**os.environ, "GOOGLE_MAPS_API_KEY": maps_key},
    )

    logger.info("Starting Google Maps MCP server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                mcp_manager.mcp_session = session
                logger.info("MCP session stored in mcp_manager.")

                from app.chains.agents import initialize_world_agent

                initialize_world_agent()

                yield
    except Exception:
        logger.exception("MCP server startup failed")
        raise


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

init_db()

app.include_router(chat.router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to the Nebula API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
