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

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/neo4j-mcp.git
    cd neo4j-mcp
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    uv pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root of the project and add your credentials:
    ```env
    # .env
    NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
    NEO4J_USERNAME="neo4j"
    NEO4J_PASSWORD="your-password"
    NEO4J_DATABASE="neo4j"
    OPENAI_API_KEY="sk-..."
    ```

## Usage

Once installed, you can run the MCP server. The server exposes a set of tools that an MCP client (like an LLM) can use.

**Start the server:**
```bash
uv run mcp-server-neo4j-ehr
```

You can then interact with the server through an MCP client using the commands defined in the API.

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

To run the test suite, use the following command:
```bash
uv run pytest
```