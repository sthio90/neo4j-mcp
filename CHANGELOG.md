# Changelog

All notable changes to the Neo4j EHR MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Refactored `ehr_search_notes` tool → `ehr_get_clinical_notes`
  - Removed `query` parameter (no more text-based searching)
  - Removed `semantic` parameter (no more AI-powered semantic search)
  - Simplified to retrieve notes by type, patient ID, or admission ID only
  - Results ordered by `charttime DESC` (most recent first)
  - Improved Claude Desktop integration with clearer parameter usage
- Tool separation: Use `ehr_get_clinical_notes` for simple retrieval, `ehr_natural_query` for content searches

### Added
- Comprehensive test suite with 71 tests covering all functionality
- Unit tests for all 8 MCP tools with mocked dependencies
- Integration tests that verify real Neo4j database interactions
- Test documentation in `tests/README.md` and `src/mcp_server_neo4j_ehr/tests/README.md`
- Debug script (`debug_natural_query.py`) for testing natural language queries interactively
- Enhanced logging in natural language query module to show:
  - Input queries
  - Generated Cypher queries from OpenAI
  - Query execution results
- DateTime conversion handling for Neo4j DateTime objects to Python datetime
- Test fixtures for common data types (patients, admissions, diagnoses, etc.)

### Changed
- Updated all Pydantic models to use `field_serializer` instead of deprecated `json_encoders`
- Fixed FastMCP tool registration tests to use `get_tools()` async method
- Updated integration tests to use actual patient IDs from test database
- Enhanced natural language query tests to display full outputs

### Fixed
- DateTime serialization issues when Neo4j returns DateTime objects
- OpenAI mock patches in tests to use correct import paths
- Test assertions for procedures when no data is found
- Pydantic v2 deprecation warnings

## [0.1.0] - 2024-01-24

### Added
- Initial implementation of Neo4j EHR MCP Server
- FastMCP-based server with 8 EHR query tools:
  - `ehr_patient` - Retrieve patient information
  - `ehr_search_notes` - Search clinical notes
  - `ehr_list_diagnoses` - List patient diagnoses
  - `ehr_list_lab_events` - List laboratory events
  - `ehr_list_medications` - List medications
  - `ehr_list_procedures` - List procedures
  - `ehr_natural_query` - Natural language to Cypher queries
  - `ehr_get_schema` - Get database schema
- Support for multiple output formats (JSON, table, markdown)
- Semantic search capabilities using OpenAI embeddings
- Natural language query processing with GPT-4
- Comprehensive data models for MIMIC-IV style EHR data
- Neo4j async driver integration
- Environment-based configuration
- Project documentation and specifications