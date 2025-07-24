"""Basic tests for the Neo4j EHR MCP Server."""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock
from src.mcp_server_neo4j_ehr.server import create_mcp_server
from src.mcp_server_neo4j_ehr.modules.db_connection import Neo4jConnection


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver."""
    driver = AsyncMock()
    return driver


@pytest.fixture
def mock_db_connection(mock_neo4j_driver):
    """Create a mock database connection."""
    return Neo4jConnection(mock_neo4j_driver)


def test_create_mcp_server(mock_neo4j_driver):
    """Test that MCP server can be created."""
    server = create_mcp_server(mock_neo4j_driver, "neo4j", "test-api-key")
    assert server is not None
    assert server.name == "mcp-server-neo4j-ehr"


@pytest.mark.asyncio
async def test_patient_tool_exists(mock_neo4j_driver):
    """Test that patient tool exists in the server."""
    server = create_mcp_server(mock_neo4j_driver)
    # Check if the tool decorator created the tool
    # FastMCP tool registration happens via decorators
    tools = await server.get_tools()
    assert "ehr_patient" in tools


@pytest.mark.asyncio
async def test_all_tools_exist(mock_neo4j_driver):
    """Test that all expected tools exist."""
    server = create_mcp_server(mock_neo4j_driver)
    
    expected_tools = [
        "ehr_patient",
        "ehr_search_notes",
        "ehr_list_diagnoses",
        "ehr_list_lab_events",
        "ehr_list_medications",
        "ehr_list_procedures",
        "ehr_natural_query",
        "ehr_get_schema"
    ]
    
    # Check if tools are registered via get_tools
    tools = await server.get_tools()
    
    for expected in expected_tools:
        assert expected in tools, f"Tool {expected} not found"