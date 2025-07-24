"""Main server implementation for Neo4j EHR MCP Server."""

import logging
from typing import Literal, Optional
from fastmcp.server import FastMCP
from mcp.types import ToolAnnotations
from neo4j import AsyncDriver

from .modules.db_connection import Neo4jConnection
from .modules.constants import *
from .modules.data_types import OutputFormat, NoteType
from .modules.functionality.patient import get_patient
from .modules.functionality.search_notes import search_notes
from .modules.functionality.list_diagnoses import list_diagnoses
from .modules.functionality.list_lab_events import list_lab_events
from .modules.functionality.list_medications import list_medications
from .modules.functionality.list_procedures import list_procedures
from .modules.functionality.natural_query import natural_query
from .modules.functionality.get_schema import get_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mcp_server(neo4j_driver: AsyncDriver, database: str = "neo4j", openai_api_key: Optional[str] = None) -> FastMCP:
    """Create an MCP server instance for EHR queries."""
    
    mcp = FastMCP("mcp-server-neo4j-ehr", dependencies=["neo4j", "pydantic", "openai", "tabulate"], stateless_http=True)
    db_connection = Neo4jConnection(neo4j_driver, database)
    
    @mcp.tool(
        name="ehr_patient",
        annotations=ToolAnnotations(
            title="Get Patient Information",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="Retrieve comprehensive patient information including admissions and clinical data"
        )
    )
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
        return await get_patient(
            db_connection, subject_id, include_admissions, include_diagnoses,
            include_procedures, include_medications, include_lab_events, format
        )
    
    @mcp.tool(
        name="ehr_search_notes",
        annotations=ToolAnnotations(
            title="Search Clinical Notes",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="Search through discharge notes and radiology reports"
        )
    )
    async def ehr_search_notes(
        query: str,
        note_type: NoteType = NOTE_TYPE_ALL,
        limit: int = DEFAULT_NOTE_SEARCH_LIMIT,
        semantic: bool = False,
        patient_id: Optional[str] = None,
        admission_id: Optional[str] = None,
        format: OutputFormat = OUTPUT_FORMAT_JSON
    ) -> str:
        """Search through clinical notes (discharge or radiology)."""
        return await search_notes(
            db_connection, query, note_type, limit, semantic,
            patient_id, admission_id, format, openai_api_key
        )
    
    @mcp.tool(
        name="ehr_list_diagnoses",
        annotations=ToolAnnotations(
            title="List Diagnoses",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="List diagnoses for a patient or admission"
        )
    )
    async def ehr_list_diagnoses(
        patient_id: Optional[str] = None,
        admission_id: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        format: OutputFormat = OUTPUT_FORMAT_JSON
    ) -> str:
        """List diagnoses for a patient or admission."""
        return await list_diagnoses(db_connection, patient_id, admission_id, limit, format)
    
    @mcp.tool(
        name="ehr_list_lab_events",
        annotations=ToolAnnotations(
            title="List Lab Events",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="List laboratory test results for a patient"
        )
    )
    async def ehr_list_lab_events(
        patient_id: str,
        admission_id: Optional[str] = None,
        abnormal_only: bool = False,
        category: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        format: OutputFormat = OUTPUT_FORMAT_JSON
    ) -> str:
        """List lab events for a patient."""
        return await list_lab_events(
            db_connection, patient_id, admission_id, abnormal_only,
            category, limit, format
        )
    
    @mcp.tool(
        name="ehr_list_medications",
        annotations=ToolAnnotations(
            title="List Medications",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="List medications for a patient or admission"
        )
    )
    async def ehr_list_medications(
        patient_id: Optional[str] = None,
        admission_id: Optional[str] = None,
        medication: Optional[str] = None,
        route: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        format: OutputFormat = OUTPUT_FORMAT_JSON
    ) -> str:
        """List medications for a patient or admission."""
        return await list_medications(
            db_connection, patient_id, admission_id, medication,
            route, limit, format
        )
    
    @mcp.tool(
        name="ehr_list_procedures",
        annotations=ToolAnnotations(
            title="List Procedures",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="List procedures for a patient or admission"
        )
    )
    async def ehr_list_procedures(
        patient_id: Optional[str] = None,
        admission_id: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        format: OutputFormat = OUTPUT_FORMAT_JSON
    ) -> str:
        """List procedures for a patient or admission."""
        return await list_procedures(db_connection, patient_id, admission_id, limit, format)
    
    @mcp.tool(
        name="ehr_natural_query",
        annotations=ToolAnnotations(
            title="Natural Language Query",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="Ask questions in natural language about the EHR data"
        )
    )
    async def ehr_natural_query(
        query: str,
        limit: int = DEFAULT_NATURAL_QUERY_LIMIT,
        format: OutputFormat = OUTPUT_FORMAT_MARKDOWN
    ) -> str:
        """Ask a question in natural language."""
        if not openai_api_key:
            return '{"error": "OpenAI API key is required for natural language queries"}'
        return await natural_query(db_connection, query, limit, format, openai_api_key)
    
    @mcp.tool(
        name="ehr_get_schema",
        annotations=ToolAnnotations(
            title="Get Database Schema",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            description="Get the database schema to understand available data"
        )
    )
    async def ehr_get_schema(
        format: OutputFormat = OUTPUT_FORMAT_MARKDOWN
    ) -> str:
        """Get the database schema."""
        return await get_schema(db_connection, format)
    
    return mcp


async def main(
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    neo4j_database: str,
    openai_api_key: Optional[str] = None,
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp/",
) -> None:
    """Main entry point for the server."""
    
    # Import the driver creation function
    from .modules.db_connection import create_neo4j_driver
    
    # Create Neo4j driver
    driver = create_neo4j_driver(neo4j_uri, neo4j_username, neo4j_password)
    
    # Create MCP server
    server = create_mcp_server(driver, neo4j_database, openai_api_key)
    
    # Run the server
    await server.run(transport, host, port, path)
    
    # Clean up
    await driver.close()