#!/bin/bash
# Setup script for Neo4j MCP Server

echo "Setting up Neo4j MCP Server..."

# Install the package in editable mode with all dependencies
echo "Installing dependencies..."
uv pip install -e .

# Install test dependencies
echo "Installing test dependencies..."
uv pip install pytest pytest-asyncio

echo "Setup complete!"
echo ""
echo "To test your connection, run:"
echo "  uv run python examples/test_connection.py"
echo ""
echo "To start the server, run:"
echo "  uv run mcp-server-neo4j-ehr"