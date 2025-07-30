  MCP Inspector Setup Guide for Neo4j MCP Server

  Prerequisites Confirmed

  - ✅ Node.js v24.4.1 installed (exceeds required v22.7.5)
  - ✅ Neo4j credentials configured in .env file
  - ✅ OpenAI API key configured for natural language queries
  - ✅ Project uses uv for package management

  Quick Start Commands

  1. Basic Launch

  npx @modelcontextprotocol/inspector uv run mcp-server-neo4j-ehr

  2. With Explicit Environment Variables

  npx @modelcontextprotocol/inspector \
    -e NEO4J_URI=neo4j+s://59e8b04a.databases.neo4j.io \
    -e NEO4J_USERNAME=neo4j \
    -e NEO4J_PASSWORD=password \
    -e NEO4J_DATABASE=neo4j \
    -e
  OPENAI_API_KEY=secret key \
    uv run mcp-server-neo4j-ehr

  3. Using Python Module Directly

  npx @modelcontextprotocol/inspector uv run python -m mcp_server_neo4j_ehr

  What to Expect

  1. MCP Inspector starts on http://localhost:6274
  2. Session token displayed in terminal
  3. Browser opens automatically with token pre-filled
  4. UI shows 8 available Neo4j tools

  Available Tools to Test

  - ehr_get_schema - View database structure
  - ehr_patient - Get patient records (example: subject_id "10000032")
  - ehr_search_notes - Search clinical notes
  - ehr_list_diagnoses - List patient diagnoses
  - ehr_list_lab_events - List lab results
  - ehr_list_medications - List medications
  - ehr_list_procedures - List medical procedures
  - ehr_natural_query - Natural language queries

  Troubleshooting

  - Ensure you're in /Users/samuelthio/projects/neo4j-mcp directory
  - The .env file is automatically loaded by python-dotenv
  - Verify Neo4j instance is accessible
  - Default transport mode is stdio (standard input/output)

  CLI Mode Testing

  For automated testing without UI:
  # List all tools
  npx @modelcontextprotocol/inspector --cli uv run mcp-server-neo4j-ehr --method tools/list

  # Get database schema
  npx @modelcontextprotocol/inspector --cli uv run mcp-server-neo4j-ehr --method tools/call --tool-name ehr_get_schema

  # Query a patient
  npx @modelcontextprotocol/inspector --cli uv run mcp-server-neo4j-ehr --method tools/call --tool-name ehr_patient --tool-arg subject_id=10000032