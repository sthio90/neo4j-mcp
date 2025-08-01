#!/usr/bin/env python3
"""
Wrapper script to run the Neo4j EHR MCP server.
This script uses uv to run the server in its proper environment.
"""
import subprocess
import sys
import os
from pathlib import Path

# Change to the Neo4j server directory
server_dir = Path(__file__).parent
os.chdir(server_dir)

# Run the server using uv in the correct environment
try:
    result = subprocess.run([
        "uv", "run", "python", "-m", "mcp_server_neo4j_ehr"
    ], check=False)
    sys.exit(result.returncode)
except FileNotFoundError:
    print("Error: uv not found. Please install uv or use a different approach.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error running server: {e}", file=sys.stderr)
    sys.exit(1)