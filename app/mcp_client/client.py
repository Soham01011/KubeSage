import contextlib
import os
from typing import AsyncGenerator, Dict, Any, Optional

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from ..models import TransportType, UserSetting

@contextlib.asynccontextmanager
async def get_mcp_session(settings: UserSetting) -> AsyncGenerator[ClientSession, None]:
    """
    Connects to the MCP Server based on the UserSettings.
    Yields an active ClientSession.
    """
    transport_type = settings.mcp_transport
    
    if transport_type == TransportType.stdio:
        # Resolve the command path from settings or environment
        command = settings.mcp_command or os.getenv("MCP_COMMAND", "../kubesage")
        
        server_params = StdioServerParameters(
            command=command,
            args=[], # Add any args if kubesage takes them
            env=os.environ.copy() # Inherit KUBECONFIG etc
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
                
    elif transport_type == TransportType.sse:
        # Resolve the URL from settings or environment
        url = settings.mcp_url or os.getenv("MCP_URL")
        if not url:
            raise ValueError("mcp_url must be set in settings or MCP_URL env var when using SSE transport")
            
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")

async def get_mcp_tools(session: ClientSession) -> list[Dict[str, Any]]:
    """Helper to fetch and format tools from an MCP session"""
    tools_response = await session.list_tools()
    tools = []
    for tool in tools_response.tools:
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        })
    return tools
