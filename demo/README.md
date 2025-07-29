# Neo4j MCP Server Demo

An interactive web interface for testing and exploring the Neo4j MCP (Model Context Protocol) server capabilities.

## Overview

This demo provides a user-friendly HTML interface to interact with all the Neo4j MCP server tools without needing to set up a full MCP client. It's perfect for:

- Testing the server functionality
- Exploring the available tools
- Demonstrating capabilities to stakeholders
- Debugging and development

## Prerequisites

1. **Neo4j Database**
   - Neo4j instance running with MIMIC-III or MIMIC-IV data loaded
   - Proper indexes and constraints configured

2. **Python Environment**
   - Python 3.8 or higher
   - Neo4j MCP server installed (`pip install mcp-server-neo4j-ehr` or `pip install -e .` from project root)
   - MCP library installed (`pip install mcp`)

3. **Environment Configuration**
   Create a `.env` file in the project root with:
   ```bash
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=neo4j
   
   # Optional - Required for natural language queries
   OPENAI_API_KEY=your_openai_api_key
   
   # Optional - For semantic search
   EMBEDDING_MODEL=text-embedding-3-small
   ```

## Quick Start

### Option 1: Using uv (Recommended)

**Start the MCP Server in stdio mode (default):**
```bash
uv run mcp-server-neo4j-ehr --neo4j-password your_password
```

**Start the MCP Server in HTTP mode:**
```bash
uv run mcp-server-neo4j-ehr \
  --neo4j-password your_password \
  --transport http \
  --host 127.0.0.1 \
  --port 8080
```

**With all options:**
```bash
uv run mcp-server-neo4j-ehr \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-username neo4j \
  --neo4j-password your_password \
  --neo4j-database neo4j \
  --openai-api-key your_openai_key \
  --transport http \
  --host 127.0.0.1 \
  --port 8080
```

### Option 2: Using Python Module

**Start the MCP Server in stdio mode:**
```bash
python -m mcp_server_neo4j_ehr \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-username neo4j \
  --neo4j-password your_password \
  --transport stdio
```

**Start the MCP Server in HTTP mode:**
```bash
python -m mcp_server_neo4j_ehr \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-username neo4j \
  --neo4j-password your_password \
  --transport http \
  --host 127.0.0.1 \
  --port 8080
```

### Option 3: Legacy HTTP Server Script (if available)
```bash
cd demo
python run_http_server.py
```

## Testing with MCP Inspector

Once your server is running, you can test it with the MCP Inspector:

**For stdio transport:**
```bash
npx @modelcontextprotocol/inspector python -m mcp_server_neo4j_ehr \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-username neo4j \
  --neo4j-password your_password \
  --transport stdio
```

**For HTTP transport:**
```bash
# First start your server with HTTP transport, then:
npx @modelcontextprotocol/inspector http://127.0.0.1:8080/mcp/
```

## Using the Web Demo

1. **Start the Server in HTTP Mode** (see commands above)

2. **Open the Demo Interface**
   - Open `demo/index.html` in your web browser
   - Or serve it with a local web server:
     ```bash
     python -m http.server 8000
     # Then open http://localhost:8000/index.html
     ```

3. **Connect to the Server**
   - Click the "Connect" button in the interface
   - The status indicator should turn green when connected

## Command Line Options

See all available options:
```bash
uv run mcp-server-neo4j-ehr --help
```

Available options include:
- `--neo4j-uri`: Neo4j connection URI (default: bolt://localhost:7687)
- `--neo4j-username`: Neo4j username (default: neo4j)
- `--neo4j-password`: Neo4j password (required)
- `--neo4j-database`: Neo4j database name (default: neo4j)
- `--openai-api-key`: OpenAI API key for natural language queries
- `--transport`: Transport type (stdio, http, sse) (default: stdio)
- `--host`: Host for HTTP/SSE transport (default: 127.0.0.1)
- `--port`: Port for HTTP/SSE transport (default: 8000)
- `--path`: Path for HTTP transport (default: /mcp/)

## Testing the Demo

Run the test suite to verify everything is working:
```bash
cd demo
python test_demo.py
```

Check what data is in your database:
```bash
cd demo
python check_data.py
```

## Using the Demo

### Available Tools

1. **Patient Information**
   - Get comprehensive patient data
   - Select which information to include (demographics, admissions, diagnoses, etc.)
   - Sample patient IDs from your database: 10461137, 11578849, 12017557, 14037695

2. **Search Clinical Notes**
   - Text search: Find notes containing specific terms
   - Semantic search: Find notes semantically similar to your query
   - Filter by patient or admission

3. **List Diagnoses**
   - View all diagnoses or filter by patient/admission
   - See ICD-9 codes and descriptions

4. **List Medications**
   - Browse prescribed medications
   - Filter by patient or admission

5. **List Procedures**
   - View medical procedures performed
   - Filter by patient or admission

6. **List Lab Events**
   - See laboratory test results
   - Filter by patient or admission

7. **Natural Language Query**
   - Ask questions in plain English
   - Requires OpenAI API key
   - Examples:
     - "Which patients had both diabetes and hypertension?"
     - "Show me the most common diagnoses"
     - "Find patients with abnormal lab values"

8. **Database Schema**
   - View the complete Neo4j database schema
   - Understand node types and relationships

### Output Formats

Each tool supports three output formats:
- **JSON**: Raw data format, ideal for developers
- **Table**: Formatted tables (when applicable)
- **Markdown**: Human-readable formatted text

## Testing Scenarios

### Basic Patient Lookup
1. Enter patient ID: `10461137`
2. Check "Demographics" only
3. Click "Get Patient Info"

### Comprehensive Patient Record
1. Enter patient ID: `10461137`
2. Check all include options
3. Set format to "Markdown"
4. Click "Get Patient Info"

### Text Search Example
1. Go to "Search Notes" tab
2. Enter query: "chest pain"
3. Set search type to "Text Search"
4. Click "Search Notes"

### Natural Language Query Example
1. Go to "Natural Query" tab
2. Enter: "Which patients had pneumonia?"
3. Click "Ask Question"

## Troubleshooting

### Connection Issues
- Ensure the MCP server is running (`python run_http_server.py`)
- Check the server URL (default: `http://localhost:8080`)
- Look for error messages in the server console

### No Results
- Verify Neo4j is running and accessible
- Check that MIMIC data is loaded
- Confirm patient IDs exist in the database
- Review server logs for query errors

### Natural Query Not Working
- Ensure `OPENAI_API_KEY` is set in environment
- Check for API key validity
- Monitor usage limits

### CORS Errors
- Make sure you're using the HTTP server script provided
- Don't open the HTML file directly with `file://` protocol
- Use a local web server if needed

## Development

### Project Structure
```
demo/
├── index.html          # Main interface
├── mcp-client.js      # JavaScript MCP client
├── styles.css         # Styling
├── run_http_server.py # HTTP server script
└── README.md          # This file
```

### Extending the Demo

To add new features:
1. Add UI elements in `index.html`
2. Implement client functions in `mcp-client.js`
3. Style with `styles.css`

### Debugging

Enable browser developer console to see:
- Network requests to the MCP server
- Response data and errors
- JavaScript console logs

## Security Notes

- This demo is for development/testing only
- CORS is enabled for all origins (*)
- Don't expose to public internet without proper security
- Sanitize inputs in production environments

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [MIMIC Database](https://mimic.mit.edu/)
- [Project Repository](https://github.com/your-repo/neo4j-mcp)