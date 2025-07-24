# Server Tests

This directory contains high-level tests for the MCP server creation and tool registration.

## Test Files

- `test_server.py` - Tests the FastMCP server initialization and tool registration

## Running These Tests

```bash
# Run server tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v
```

## What's Tested

1. **Server Creation** - Verifies the MCP server can be created with proper configuration
2. **Tool Registration** - Ensures all 8 EHR tools are properly registered:
   - `ehr_patient` - Patient information retrieval
   - `ehr_search_notes` - Clinical note search
   - `ehr_list_diagnoses` - Diagnosis listing
   - `ehr_list_lab_events` - Lab event listing
   - `ehr_list_medications` - Medication listing
   - `ehr_list_procedures` - Procedure listing
   - `ehr_natural_query` - Natural language queries
   - `ehr_get_schema` - Schema information

## Note

For detailed functionality tests, see `src/mcp_server_neo4j_ehr/tests/README.md`