"""Main server implementation for Neo4j EHR MCP Server."""

import logging
from typing import Literal, Optional
from fastmcp import FastMCP
from neo4j import AsyncDriver

from .modules.db_connection import Neo4jConnection
from .modules.constants import *
from .modules.data_types import OutputFormat, NoteType
from .modules.functionality.patient import get_patient
from .modules.functionality.get_clinical_notes import get_clinical_notes
from .modules.functionality.list_diagnoses import list_diagnoses
from .modules.functionality.list_lab_events import list_lab_events
from .modules.functionality.list_medications import list_medications
from .modules.functionality.list_procedures import list_procedures
from .modules.functionality.natural_query import natural_query
from .modules.functionality.get_schema import get_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("mcp-server-neo4j-ehr")

# Global variables for database connection and OpenAI key
db_connection: Optional[Neo4jConnection] = None
openai_api_key: Optional[str] = None


@mcp.tool
async def ehr_patient(
    subject_id: str,
    include_admissions: bool = True,
    include_diagnoses: bool = False,
    include_procedures: bool = False,
    include_medications: bool = False,
    include_lab_events: bool = False,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """Get a comprehensive summary of a patient's record."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await get_patient(
        db_connection, subject_id, include_admissions, include_diagnoses,
        include_procedures, include_medications, include_lab_events, format
    )


@mcp.tool
async def ehr_get_clinical_notes(
    note_type: NoteType = NOTE_TYPE_ALL,
    limit: int = DEFAULT_NOTE_SEARCH_LIMIT,
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """Retrieve clinical notes by type (discharge or radiology).
    
    For discharge summaries: Use admission_id to get notes for a specific admission.
    For radiology reports: Use patient_id to get all imaging reports for a patient.
    To get all notes: Specify note_type and patient_id or admission_id.
    
    This tool returns ALL matching notes without filtering by content."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await get_clinical_notes(
        db_connection, note_type, limit,
        patient_id, admission_id, format
    )


@mcp.tool
async def ehr_list_diagnoses(
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List diagnoses for a patient or admission."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await list_diagnoses(db_connection, patient_id, admission_id, limit, format)


@mcp.tool
async def ehr_list_lab_events(
    patient_id: str,
    admission_id: Optional[str] = None,
    abnormal_only: bool = False,
    category: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List lab events for a patient."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await list_lab_events(
        db_connection, patient_id, admission_id, abnormal_only,
        category, limit, format
    )


@mcp.tool
async def ehr_list_medications(
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    medication: Optional[str] = None,
    route: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List medications for a patient or admission."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await list_medications(
        db_connection, patient_id, admission_id, medication,
        route, limit, format
    )


@mcp.tool
async def ehr_list_procedures(
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List procedures for a patient or admission."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await list_procedures(db_connection, patient_id, admission_id, limit, format)


@mcp.tool
async def ehr_natural_query(
    query: str,
    limit: int = DEFAULT_NATURAL_QUERY_LIMIT,
    format: OutputFormat = OUTPUT_FORMAT_MARKDOWN
) -> str:
    """Ask a question in natural language."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    if not openai_api_key:
        return '{"error": "OpenAI API key is required for natural language queries"}'
    return await natural_query(db_connection, query, limit, format, openai_api_key)


@mcp.tool
async def ehr_get_schema(
    format: OutputFormat = OUTPUT_FORMAT_MARKDOWN
) -> str:
    """Get the database schema."""
    if not db_connection:
        return '{"error": "Database connection not initialized"}'
    return await get_schema(db_connection, format)


def main(
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    neo4j_database: str,
    openai_api_key_param: Optional[str] = None,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
) -> None:
    """Main entry point for the server."""
    global db_connection, openai_api_key
    
    # Import the driver creation function
    from .modules.db_connection import create_neo4j_driver
    
    # Create Neo4j driver
    driver = create_neo4j_driver(neo4j_uri, neo4j_username, neo4j_password)
    
    # Initialize global variables
    db_connection = Neo4jConnection(driver, neo4j_database)
    openai_api_key = openai_api_key_param
    
    # Run the server with correct parameters
    if transport == "stdio":
        mcp.run()
    elif transport == "http":
        mcp.run(transport="http", host=host, port=port, path=path)
    elif transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    else:
        raise ValueError(f"Unsupported transport: {transport}")