"""Base agent class with MCP client setup"""
import os
from typing import Any, Optional


class BaseAgent:
    """Base class for all agents with MCP client support"""

    def __init__(self, mcp_server_url: str = "http://mcp-server:8001"):
        """
        Initialize base agent with MCP server connection.

        Args:
            mcp_server_url: URL of the MCP server
        """
        self.mcp_server_url = mcp_server_url
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

    async def call_mcp_tool(self, tool_name: str, **kwargs) -> Optional[Any]:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool result or None if error
        """
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.mcp_server_url}/tools/{tool_name}",
                    json=kwargs,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            return None

    def get_claude_client(self):
        """Get Anthropic Claude client"""
        try:
            from anthropic import Anthropic

            return Anthropic(api_key=self.anthropic_api_key)
        except Exception as e:
            print(f"Error initializing Claude client: {e}")
            return None
