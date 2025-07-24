# Neo4j MCP Server for EHR GraphRAG

This project provides a Model Context Protocol (MCP) server to interact with a Neo4j graph database containing Electronic Health Record (EHR) data, specifically modeled after the MIMIC-IV dataset. It allows users to query complex medical data using both structured commands and natural language.

## Overview

Querying large, interconnected EHR datasets can be challenging. This MCP server simplifies the process by providing a set of intuitive tools to:
- Retrieve detailed patient records.
- Perform semantic searches on clinical notes like discharge summaries and radiology reports.
- List specific clinical events like diagnoses, lab results, and medications.
- Translate natural language questions into executable Cypher queries against the graph.

This enables powerful GraphRAG (Retrieval-Augmented Generation) workflows where a Large Language Model (LLM) can be grounded with real-time, specific data from the EHR graph.

## Features

- **Natural Language Querying**: Ask complex questions in plain English. The server leverages an LLM that can inspect the graph schema to generate accurate Cypher queries.
- **Structured API**: A robust set of commands for precise data retrieval (e.g., get a specific patient, list diagnoses for an admission).
- **Semantic Search**: Utilizes vector embeddings on clinical notes to find information based on meaning, not just keywords.
- **Schema Awareness**: Includes a tool to fetch the database schema, which is crucial for enabling an LLM to write accurate queries.
- **Flexible Output**: Get results in JSON for programmatic use or in human-readable tables and markdown.

## Prerequisites

- Python 3.9+
- `uv` (or `pip` and `venv`)
- A Neo4j AuraDB or local instance populated with data conforming to the [spec schema](specs/neo4j-mcp-v1.md).
- An OpenAI API key for semantic search and natural language processing.

## Quick Start

1. **Clone and install:**
   ```bash
   git clone https://github.com/your-username/neo4j-mcp.git
   cd neo4j-mcp
   uv pip install -e .
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Neo4j and OpenAI credentials
   ```

3. **Test the connection:**
   ```bash
   uv run python examples/test_connection.py
   ```

4. **Run tests to verify everything works:**
   ```bash
   uv run pytest -k "not integration"  # Unit tests only
   uv run pytest  # All tests (requires database)
   ```

5. **Try natural language queries:**
   ```bash
   uv run python debug_natural_query.py "How many patients are in the database?"
   ```

## Installation

### Using pip

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/neo4j-mcp.git
    cd neo4j-mcp
    ```

2.  **Install the package:**
    ```bash
    pip install -e .
    ```

### Using uv (recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/neo4j-mcp.git
    cd neo4j-mcp
    ```

2.  **Install with uv:**
    ```bash
    uv pip install -e .
    ```

### Configuration

Set up environment variables by creating a `.env` file in the project root:

```env
# Neo4j connection settings
NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your-password"
NEO4J_DATABASE="neo4j"

# OpenAI API key for semantic search and natural language queries
OPENAI_API_KEY="sk-..."
```

## Usage

### Running the Server

**Using stdio transport (default):**
```bash
uv run mcp-server-neo4j-ehr
```

**Using HTTP transport:**
```bash
uv run mcp-server-neo4j-ehr --transport http --port 8000
```

**With custom Neo4j connection:**
```bash
uv run mcp-server-neo4j-ehr --neo4j-uri bolt://localhost:7687 --neo4j-password mypassword
```

### MCP Client Configuration

To use this server with Claude Desktop, add it to your MCP settings:

```json
{
  "mcpServers": {
    "neo4j-ehr": {
      "command": "mcp-server-neo4j-ehr",
      "env": {
        "NEO4J_URI": "neo4j+s://your-instance.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "NEO4J_DATABASE": "neo4j",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Example Use Cases

- **Get a patient's full record:**
  ```
  ehr patient "10000032" --include-diagnoses=True --include-medications=True
  ```

- **Pull a discharge summary to use as context for an LLM:**
  ```
  ehr search-notes "" --patient-id="10000032" --note-type=discharge --format=text
  ```

- **Ask a question in natural language:**
  ```
  ehr natural-query "What was the final diagnosis for patient 10000032's admission on 2124-08-07?"
  ```
  
- **Provide the database schema to an LLM to help it construct queries:**
  ```
  ehr get-schema
  ```

## API Reference

The following commands are available through the MCP server:

```
# Get a comprehensive summary of a patient's record
ehr patient <subject_id> \
    --include-admissions: bool = True \
    --include-diagnoses: bool = False \
    --include-procedures: bool = False \
    --include-medications: bool = False \
    --include-lab-events: bool = False \
    --format: json | table = json

# Search through clinical notes (discharge or radiology)
ehr search-notes <query> \
    --note-type: discharge | radiology | all = all \
    --limit: int = 5 \
    --semantic: bool = False \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --format: json | text | table = json

# List diagnoses for a patient or admission
ehr list-diagnoses \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

# List lab events for a patient
ehr list-lab-events \
    --patient-id: str (required) \
    --admission-id: str (optional) \
    --abnormal-only: bool = False \
    --category: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

# List medications for a patient or admission
ehr list-medications \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --medication: str (optional) \
    --route: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

# List procedures for a patient or admission
ehr list-procedures \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

# Ask a question in natural language
ehr natural-query <query> \
    --limit: int = 10 \
    --format: json | markdown | table = markdown

# Get the database schema
ehr get-schema \
    --format: json | markdown = markdown
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run only unit tests (skip integration tests)
uv run pytest -k "not integration"

# Run only integration tests
uv run pytest -k "integration"

# Run tests with output visible
uv run pytest -v -s

# Run tests with coverage
uv pip install pytest-cov
uv run pytest --cov=src/mcp_server_neo4j_ehr --cov-report=html

# Run specific test file
uv run pytest src/mcp_server_neo4j_ehr/tests/functionality/test_patient.py

# Run natural language query test with debug output
uv run pytest "src/mcp_server_neo4j_ehr/tests/functionality/test_natural_query.py::TestNaturalQueryIntegration" -v -s --log-cli-level=INFO
```

For more details on testing, see the [test documentation](src/mcp_server_neo4j_ehr/tests/README.md).

### Debugging Natural Language Queries

To see what Cypher queries are generated from natural language questions:

```bash
# Interactive mode - enter queries and see results
uv run python debug_natural_query.py

# Command line mode - test a specific query
uv run python debug_natural_query.py "How many patients have heart failure?"
```

This debug script shows:
- The natural language query being processed
- The generated Cypher query from OpenAI
- The query execution results
- Any errors or issues

### Project Structure

```
src/mcp_server_neo4j_ehr/
├── __init__.py
├── __main__.py           # CLI entry point
├── server.py             # Main server implementation
├── modules/
│   ├── constants.py      # Configuration constants
│   ├── data_types.py     # Pydantic models
│   ├── db_connection.py  # Neo4j connection management
│   └── functionality/    # Tool implementations
│       ├── patient.py
│       ├── search_notes.py
│       ├── list_diagnoses.py
│       ├── list_lab_events.py
│       ├── list_medications.py
│       ├── list_procedures.py
│       ├── natural_query.py
│       └── get_schema.py
└── tests/                # Test suite
    ├── README.md         # Test documentation
    ├── conftest.py       # Test fixtures
    └── functionality/    # Module tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.