# Contributing to Neo4j EHR MCP Server

Thank you for your interest in contributing to the Neo4j EHR MCP Server! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/neo4j-mcp.git
   cd neo4j-mcp
   ```
3. Install dependencies:
   ```bash
   uv pip install -e .
   ```
4. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Development Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

Before submitting, ensure all tests pass:

```bash
# Run unit tests
uv run pytest -k "not integration"

# Run all tests (requires database)
uv run pytest

# Check code coverage
uv run pytest --cov=src/mcp_server_neo4j_ehr
```

### 4. Test Your Changes

For natural language query changes:
```bash
uv run python debug_natural_query.py
```

### 5. Submit a Pull Request

- Write a clear description of your changes
- Reference any related issues
- Ensure CI tests pass

## Code Style Guidelines

### Python Code

- Follow PEP 8
- Use type hints where appropriate
- Keep functions focused and small
- Document complex logic with comments

### Imports

```python
# Standard library
import json
from typing import Optional, List

# Third-party
from pydantic import BaseModel
import neo4j

# Local
from ..modules.constants import *
from ..modules.data_types import Patient
```

### Error Handling

```python
try:
    results = await db.execute_read(query)
except Exception as e:
    logger.error(f"Query failed: {e}")
    return json.dumps({"error": "Query failed", "details": str(e)})
```

## Testing Guidelines

### Writing Tests

1. **Unit Tests**: Mock external dependencies
   ```python
   @pytest.mark.asyncio
   async def test_feature(mock_db_connection):
       mock_db_connection.execute_read.return_value = [{"data": "test"}]
       result = await your_function(mock_db_connection)
       assert "expected" in result
   ```

2. **Integration Tests**: Use real connections
   ```python
   @pytest.mark.asyncio
   @pytest.mark.integration
   async def test_real_feature(real_db_connection):
       result = await your_function(real_db_connection)
       assert result is not None
   ```

### Test Data

- Use fixtures from `conftest.py`
- Create minimal test data
- Clean up after tests

## Documentation

### Code Documentation

- Add docstrings to all public functions
- Include parameter descriptions
- Document return values

Example:
```python
async def get_patient(
    db: Neo4jConnection,
    subject_id: str,
    include_admissions: bool = True
) -> str:
    """Get comprehensive patient information.
    
    Args:
        db: Database connection
        subject_id: Patient identifier
        include_admissions: Whether to include admission data
        
    Returns:
        JSON string with patient data
    """
```

### Update Documentation

When adding features, update:
- README.md - for user-facing changes
- CHANGELOG.md - for all changes
- Test documentation - for new test cases

## Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat: add patient medication history endpoint
fix: handle Neo4j DateTime serialization
docs: update natural language query examples
test: add integration tests for lab events
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.