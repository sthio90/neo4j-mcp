# Neo4j EHR MCP Server Tests

This directory contains the test suite for the Neo4j EHR MCP Server. The tests are organized to validate both individual functionality modules and the overall server integration.

## Test Structure

```
tests/
├── README.md                    # This file
├── conftest.py                 # Shared test fixtures and configuration
└── functionality/              # Tests for individual functionality modules
    ├── test_get_schema.py      # Schema retrieval tests
    ├── test_list_diagnoses.py  # Diagnosis listing tests
    ├── test_list_lab_events.py # Lab event listing tests
    ├── test_list_medications.py # Medication listing tests
    ├── test_list_procedures.py  # Procedure listing tests
    ├── test_natural_query.py    # Natural language query tests
    ├── test_patient.py         # Patient information retrieval tests
    └── test_search_notes.py    # Clinical note search tests
```

## Test Categories

### 1. Unit Tests
- Mock all external dependencies (Neo4j, OpenAI)
- Test business logic and data transformations
- Fast execution, no network calls
- Run frequently during development

### 2. Integration Tests
- Use real Neo4j database connection
- Use real OpenAI API (for natural language tests)
- Marked with `@pytest.mark.integration`
- Require environment variables to be set

## Running Tests

### Run All Tests
```bash
# Using uv (recommended)
uv run pytest

# Using standard pytest
pytest
```

### Run Only Unit Tests
```bash
# Skip integration tests that require database/API connections
uv run pytest -k "not integration"
```

### Run Only Integration Tests
```bash
# Requires Neo4j database and OpenAI API key
uv run pytest -k "integration"
```

### Run Specific Test Files
```bash
# Test a specific module
uv run pytest src/mcp_server_neo4j_ehr/tests/functionality/test_patient.py

# Test a specific test class
uv run pytest src/mcp_server_neo4j_ehr/tests/functionality/test_patient.py::TestPatientFunctionality

# Test a specific test method
uv run pytest src/mcp_server_neo4j_ehr/tests/functionality/test_patient.py::TestPatientFunctionality::test_get_patient_basic
```

### Run Tests with Output
```bash
# Show print statements and logs
uv run pytest -v -s

# Show only INFO level logs and above
uv run pytest -v -s --log-cli-level=INFO

# Show all debug logs
uv run pytest -v -s --log-cli-level=DEBUG
```

### Run Tests with Coverage
```bash
# Install coverage tool
uv pip install pytest-cov

# Run with coverage report
uv run pytest --cov=src/mcp_server_neo4j_ehr

# Generate HTML coverage report
uv run pytest --cov=src/mcp_server_neo4j_ehr --cov-report=html
```

## Environment Setup

### For Unit Tests
No special setup required - all dependencies are mocked.

### For Integration Tests
Create a `.env` file in the project root with:

```env
# Neo4j connection
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# OpenAI API (for natural language query tests)
OPENAI_API_KEY=sk-...
```

## Test Fixtures (conftest.py)

Common fixtures available to all tests:

- `mock_db_connection`: Mock Neo4j connection for unit tests
- `real_db_connection`: Real Neo4j connection for integration tests (skips if not configured)
- `sample_patient`: Sample patient data
- `sample_admission`: Sample admission data
- `sample_diagnosis`: Sample diagnosis data
- `sample_lab_event`: Sample lab event data
- `sample_medication`: Sample medication data
- `sample_procedure`: Sample procedure data
- `sample_discharge_note`: Sample discharge note
- `mock_openai_response`: Mock OpenAI API responses

## What Each Test Module Covers

### test_patient.py
- Retrieving patient information with various include options
- Handling missing patients
- Output formatting (JSON, table)
- Integration with real patient data

### test_search_notes.py
- Text-based search in clinical notes
- Semantic search using embeddings
- Filtering by note type and patient/admission
- Different output formats

### test_list_*.py modules
- Listing clinical data (diagnoses, lab events, medications, procedures)
- Filtering by patient, admission, and other criteria
- Pagination and limiting results
- Table formatting

### test_natural_query.py
- Converting natural language to Cypher queries
- OpenAI integration
- Error handling for invalid queries
- Different output formats

### test_get_schema.py
- Retrieving database schema information
- Formatting schema as JSON or Markdown
- Handling empty collections

## Debugging Test Failures

### View Natural Language Query Outputs
```bash
# See what Cypher queries are generated
uv run pytest "src/mcp_server_neo4j_ehr/tests/functionality/test_natural_query.py::TestNaturalQueryIntegration" -v -s --log-cli-level=INFO
```

### Use the Debug Script
```bash
# Interactive query testing
uv run python debug_natural_query.py

# Test specific query
uv run python debug_natural_query.py "How many patients are in the database?"
```

### Common Issues

1. **DateTime Serialization Errors**
   - Neo4j returns DateTime objects that need conversion
   - Fixed by converting to Python datetime before Pydantic serialization

2. **Patient Not Found in Integration Tests**
   - Integration tests use patient ID "10461137"
   - Ensure this patient exists in your test database

3. **OpenAI API Key Issues**
   - Set `OPENAI_API_KEY` environment variable
   - Check API key validity and rate limits

4. **Neo4j Connection Failures**
   - Verify Neo4j credentials in `.env`
   - Check network connectivity to Neo4j instance
   - Ensure database exists and is accessible

## Writing New Tests

### Unit Test Template
```python
@pytest.mark.asyncio
async def test_new_functionality(mock_db_connection):
    """Test description."""
    # Arrange
    mock_db_connection.execute_read.return_value = [{"result": "data"}]
    
    # Act
    result = await your_function(mock_db_connection, param="value")
    
    # Assert
    assert "expected" in result
```

### Integration Test Template
```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_functionality(real_db_connection):
    """Test with real database."""
    # Will skip if database not configured
    result = await your_function(real_db_connection, param="value")
    assert result is not None
```

## Best Practices

1. **Keep tests focused** - Each test should verify one specific behavior
2. **Use descriptive names** - Test names should clearly indicate what they test
3. **Mock external dependencies** - Unit tests should not require database or API access
4. **Test edge cases** - Include tests for error conditions and empty results
5. **Maintain test data** - Keep sample data in fixtures up-to-date with schema changes

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- Unit tests run on every commit (no external dependencies)
- Integration tests run on deployment branches (require secrets)
- Coverage reports help maintain code quality