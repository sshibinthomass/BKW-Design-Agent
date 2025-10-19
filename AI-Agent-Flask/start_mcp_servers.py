#!/usr/bin/env python3
"""
Start MCP servers for the Flask application
"""

import subprocess
import sys
import time
from pathlib import Path


def start_mcp_servers():
    """Start MCP servers in background"""
    print("Starting MCP servers...")

    # Get the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    tools_dir = project_root / "src" / "langgraphagenticai" / "tools"

    # Start MCP servers
    task_script = tools_dir / "mcp_task_tools.py"

    processes = []

    try:
        # Start task management server
        print(f"Starting task management MCP server: {task_script}")
        task_process = subprocess.Popen(
            [sys.executable, str(task_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append(task_process)

        # Wait a bit for servers to start
        print("Waiting for servers to start...")
        time.sleep(5)

        # Check if servers are running
        import requests

        try:
            requests.get("http://127.0.0.1:8004/mcp", timeout=5)
            print("✅ Task Management MCP server is running")
        except Exception:
            print("❌ Task Management MCP server failed to start")

        print("MCP servers started successfully!")
        print("Press Ctrl+C to stop all servers")

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping MCP servers...")
            for process in processes:
                process.terminate()
            print("MCP servers stopped")

    except Exception as e:
        print(f"Error starting MCP servers: {e}")
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    start_mcp_servers()
