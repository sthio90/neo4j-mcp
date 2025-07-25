# Neo4j MCP Server Testing Plan

## Overview

This document outlines comprehensive testing approaches for the Neo4j MCP (Model Context Protocol) server, including the creation of an HTML demo interface for easy interaction and testing.

## Testing Methods

### 1. Direct MCP Protocol Testing

#### Using MCP Inspector
```bash
npx @modelcontextprotocol/inspector python -m mcp_server_neo4j_ehr
```

#### Using MCP CLI
```bash
# Install MCP CLI
npm install -g @modelcontextprotocol/cli

# Connect to server
mcp connect stdio python -m mcp_server_neo4j_ehr
```

### 2. HTTP Mode Testing

The server supports HTTP mode for easier testing with web interfaces:

```python
# run_http_server.py
import asyncio
from mcp_server_neo4j_ehr import create_server

async def main():
    server = await create_server()
    # Configure for HTTP mode with CORS
    await server.run_http(host="localhost", port=8080, cors_origins=["*"])

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. HTML Demo Interface

Create an interactive web interface for testing all MCP tools.

## Demo Interface Specifications

### File Structure
```
demo/
├── index.html          # Main demo interface
├── mcp-client.js      # JavaScript MCP client
├── styles.css         # Styling
└── README.md          # Demo setup instructions
```

### HTML Interface Components

#### 1. Connection Status
- Server URL input
- Connect/Disconnect button
- Connection status indicator
- Available tools display

#### 2. Tool Interfaces

##### Patient Information Tool
```html
<div class="tool-section" id="patient-tool">
    <h3>Patient Information</h3>
    <input type="text" id="patient-id" placeholder="Patient ID (e.g., 10006)">
    <select id="include-options" multiple>
        <option value="demographics">Demographics</option>
        <option value="admissions">Admissions</option>
        <option value="diagnoses">Diagnoses</option>
        <option value="medications">Medications</option>
        <option value="procedures">Procedures</option>
        <option value="lab_events">Lab Events</option>
        <option value="notes">Clinical Notes</option>
    </select>
    <button onclick="getPatientInfo()">Get Patient Info</button>
</div>
```

##### Search Notes Tool
```html
<div class="tool-section" id="search-notes-tool">
    <h3>Search Clinical Notes</h3>
    <input type="text" id="search-query" placeholder="Search term">
    <select id="search-type">
        <option value="text">Text Search</option>
        <option value="semantic">Semantic Search</option>
    </select>
    <input type="number" id="search-limit" placeholder="Limit" value="10">
    <button onclick="searchNotes()">Search</button>
</div>
```

##### Natural Query Tool
```html
<div class="tool-section" id="natural-query-tool">
    <h3>Natural Language Query</h3>
    <textarea id="natural-query" placeholder="Ask a question about the data..."></textarea>
    <button onclick="naturalQuery()">Ask</button>
</div>
```

### JavaScript Client Implementation

```javascript
// mcp-client.js
class MCPClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.requestId = 0;
    }

    async callTool(toolName, args) {
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'tools/call',
                params: {
                    name: toolName,
                    arguments: args
                },
                id: ++this.requestId
            })
        });
        return response.json();
    }

    async getPatientInfo(patientId, includeOptions) {
        return this.callTool('ehr_patient', {
            subject_id: patientId,
            include: includeOptions,
            format: 'json'
        });
    }

    async searchNotes(query, searchType, limit) {
        return this.callTool('ehr_search_notes', {
            query: query,
            search_type: searchType,
            limit: limit,
            format: 'json'
        });
    }

    async naturalQuery(query, limit = 10) {
        return this.callTool('ehr_natural_query', {
            query: query,
            limit: limit,
            format: 'json'
        });
    }
}
```

## Server Configuration for Testing

### Environment Variables
```bash
# .env.test
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=your_openai_key  # Required for natural_query tool
EMBEDDING_MODEL=text-embedding-3-small  # For semantic search
```

### Test Data Requirements
- MIMIC-III or MIMIC-IV data loaded into Neo4j
- Vector embeddings created for semantic search (if using)
- Sample patient IDs for testing:
  - 10006 (patient with multiple admissions)
  - 10013 (patient with diverse medical history)
  - 10019 (patient with lab events)

## Test Scenarios

### 1. Basic Patient Lookup
```javascript
// Test: Get patient demographics
await client.getPatientInfo('10006', ['demographics']);

// Expected: Patient name, DOB, gender, etc.
```

### 2. Comprehensive Patient Data
```javascript
// Test: Get all patient data
await client.getPatientInfo('10006', [
    'demographics', 'admissions', 'diagnoses', 
    'medications', 'procedures', 'lab_events'
]);

// Expected: Complete patient record
```

### 3. Text Search
```javascript
// Test: Search for specific terms
await client.searchNotes('chest pain', 'text', 5);

// Expected: Notes containing "chest pain"
```

### 4. Semantic Search
```javascript
// Test: Semantic similarity search
await client.searchNotes('respiratory distress', 'semantic', 5);

// Expected: Notes semantically related to breathing problems
```

### 5. Natural Language Queries
```javascript
// Test: Complex natural language questions
await client.naturalQuery(
    'Which patients had both diabetes and hypertension?',
    10
);

// Expected: Cypher query generated and results returned
```

## Implementation Steps

1. **Set up Neo4j Database**
   - Install Neo4j
   - Load MIMIC data
   - Create indexes and constraints

2. **Configure MCP Server**
   - Install dependencies: `pip install mcp-server-neo4j-ehr`
   - Set environment variables
   - Test server startup

3. **Create Demo Interface**
   - Create HTML file with tool interfaces
   - Implement JavaScript client
   - Add CSS styling
   - Test CORS configuration

4. **Run Tests**
   - Start server in HTTP mode
   - Open HTML interface
   - Test each tool with sample data
   - Verify error handling

## Error Handling

### Common Issues
1. **Connection Errors**
   - Check Neo4j is running
   - Verify credentials
   - Ensure correct URI format

2. **CORS Issues**
   - Enable CORS in server configuration
   - Check allowed origins

3. **Missing API Key**
   - Natural query requires OpenAI API key
   - Set OPENAI_API_KEY environment variable

4. **Empty Results**
   - Verify data is loaded in Neo4j
   - Check patient IDs exist
   - Review query parameters

## Performance Testing

### Load Testing
```javascript
// Test concurrent requests
async function loadTest() {
    const promises = [];
    for (let i = 0; i < 10; i++) {
        promises.push(client.getPatientInfo('10006', ['demographics']));
    }
    const results = await Promise.all(promises);
    console.log(`Completed ${results.length} requests`);
}
```

### Response Time Monitoring
- Log request/response times
- Monitor Neo4j query performance
- Track LLM response times for natural queries

## Security Considerations

1. **Authentication**
   - Implement API key authentication
   - Use HTTPS in production
   - Secure Neo4j credentials

2. **Input Validation**
   - Sanitize user inputs
   - Validate patient IDs
   - Limit query complexity

3. **Rate Limiting**
   - Implement request throttling
   - Monitor usage patterns
   - Prevent abuse

## Next Steps

1. Implement the HTML demo interface
2. Create automated test suite
3. Add performance benchmarks
4. Document API endpoints
5. Create user guide for non-technical users

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [MIMIC Database](https://mimic.mit.edu/)
- [OpenAI API Reference](https://platform.openai.com/docs)