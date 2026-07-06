"""Global holder for the MCP ClientSession (set during app lifespan)."""

from mcp import ClientSession

mcp_session: ClientSession | None = None
