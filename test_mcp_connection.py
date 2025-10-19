#!/usr/bin/env python3
"""
Test script to verify MCP task server connection
"""

import asyncio
import requests
from langchain_mcp_adapters.client import MultiServerMCPClient


async def test_mcp_connection():
    """Test MCP task server connection"""
    print("Testing MCP task server connection...")

    # First, check if server is running
    try:
        response = requests.get("http://127.0.0.1:8004/mcp", timeout=5)
        print(f"✅ MCP server is running: {response.status_code}")
    except Exception as e:
        print(f"❌ MCP server is not running: {e}")
        print("Please start the MCP server first by running:")
        print("python AI-Agent-Flask/start_mcp_servers.py")
        return False

    # Test MCP client connection
    try:
        client = MultiServerMCPClient(
            {
                "csv-tools": {
                    "url": "http://127.0.0.1:8004/mcp",
                    "transport": "streamable_http",
                },
            }
        )

        tools = await client.get_tools()
        print(f"✅ Successfully connected to MCP server. Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        return True

    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
