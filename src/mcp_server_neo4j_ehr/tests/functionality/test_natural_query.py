"""Tests for natural language query functionality."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from ...modules.functionality.natural_query import natural_query, format_schema_for_llm
from ...modules.constants import (
    OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_MARKDOWN
)


class TestNaturalQueryFunctionality:
    """Test suite for natural language query functionality."""
    
    @pytest.mark.asyncio
    async def test_natural_query_success(self, mock_db_connection, mock_openai_response):
        """Test successful natural language query conversion and execution."""
        # Mock schema response
        schema = {
            "nodes": [
                {"label": "Patient", "properties": ["subject_id", "gender", "anchor_age"]},
                {"label": "Admission", "properties": ["hadm_id", "admission_type"]}
            ],
            "relationships": [
                {"relationshipType": "HAS_ADMISSION"}
            ]
        }
        mock_db_connection.get_schema.return_value = schema
        
        # Mock Cypher query execution
        mock_db_connection.execute_read.return_value = [
            {"subject_id": "10000032", "count": 3}
        ]
        
        # Mock OpenAI to return a valid Cypher query
        mock_openai_response.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='MATCH (p:Patient {subject_id: "10000032"})-[:HAS_ADMISSION]->(a:Admission) RETURN p.subject_id as subject_id, count(a) as count'
                )
            )]
        )
        
        # Execute test
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_openai_response):
            result = await natural_query(
                mock_db_connection,
                query="How many admissions does patient 10000032 have?",
                limit=10,
                format=OUTPUT_FORMAT_JSON,
                openai_api_key="test-key"
            )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'question' in data
        assert 'cypher_query' in data
        assert 'results' in data
        assert 'count' in data
        assert data['count'] == 1
        assert data['results'][0]['subject_id'] == "10000032"
        assert data['results'][0]['count'] == 3
    
    @pytest.mark.asyncio
    async def test_natural_query_with_cypher_extraction(self, mock_db_connection, mock_openai_response):
        """Test extraction of Cypher from markdown code blocks."""
        # Mock schema
        mock_db_connection.get_schema.return_value = {"nodes": [], "relationships": []}
        mock_db_connection.execute_read.return_value = [{"result": "test"}]
        
        # Mock OpenAI to return Cypher in markdown
        mock_openai_response.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='```cypher\nMATCH (p:Patient) RETURN p LIMIT 10\n```'
                )
            )]
        )
        
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_openai_response):
            result = await natural_query(
                mock_db_connection,
                query="Show me all patients",
                limit=10,
                format=OUTPUT_FORMAT_JSON,
                openai_api_key="test-key"
            )
        
        data = json.loads(result)
        assert data['cypher_query'] == "MATCH (p:Patient) RETURN p LIMIT 10"
    
    @pytest.mark.asyncio
    async def test_natural_query_cypher_error(self, mock_db_connection, mock_openai_response):
        """Test handling of Cypher execution errors."""
        mock_db_connection.get_schema.return_value = {"nodes": [], "relationships": []}
        
        # Mock Cypher execution error
        mock_db_connection.execute_read.side_effect = Exception("Invalid Cypher syntax")
        
        mock_openai_response.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(content='INVALID CYPHER QUERY')
            )]
        )
        
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_openai_response):
            result = await natural_query(
                mock_db_connection,
                query="Test query",
                format=OUTPUT_FORMAT_JSON,
                openai_api_key="test-key"
            )
        
        data = json.loads(result)
        assert 'error' in data
        assert "Failed to execute generated query" in data['error']
        assert data['query'] == "INVALID CYPHER QUERY"
    
    @pytest.mark.asyncio
    async def test_natural_query_openai_error(self, mock_db_connection):
        """Test handling of OpenAI API errors."""
        mock_db_connection.get_schema.return_value = {"nodes": [], "relationships": []}
        
        # Mock OpenAI error
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_client):
            result = await natural_query(
                mock_db_connection,
                query="Test query",
                format=OUTPUT_FORMAT_JSON,
                openai_api_key="test-key"
            )
        
        data = json.loads(result)
        assert 'error' in data
        assert "Failed to process natural language query" in data['error']
    
    @pytest.mark.asyncio
    async def test_natural_query_markdown_format(self, mock_db_connection, mock_openai_response):
        """Test markdown format output."""
        mock_db_connection.get_schema.return_value = {"nodes": [], "relationships": []}
        mock_db_connection.execute_read.return_value = [
            {"patient_id": "10000032", "diagnosis": "Heart failure"},
            {"patient_id": "10000033", "diagnosis": "Pneumonia"}
        ]
        
        mock_openai_response.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis) RETURN p.subject_id as patient_id, d.long_title as diagnosis LIMIT 2'
                )
            )]
        )
        
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_openai_response):
            result = await natural_query(
                mock_db_connection,
                query="Show me patient diagnoses",
                format=OUTPUT_FORMAT_MARKDOWN,
                openai_api_key="test-key"
            )
        
        # Assertions for markdown format
        assert "## Question" in result
        assert "## Generated Cypher Query" in result
        assert "```cypher" in result
        assert "## Results (2 rows)" in result
        assert "| patient_id | diagnosis |" in result
        assert "| 10000032 | Heart failure |" in result
    
    @pytest.mark.asyncio
    async def test_natural_query_table_format(self, mock_db_connection, mock_openai_response):
        """Test table format output."""
        mock_db_connection.get_schema.return_value = {"nodes": [], "relationships": []}
        mock_db_connection.execute_read.return_value = [
            {"name": "Test", "value": 123}
        ]
        
        mock_openai_response.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(content='MATCH (n) RETURN n.name as name, n.value as value LIMIT 1')
            )]
        )
        
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_openai_response):
            result = await natural_query(
                mock_db_connection,
                query="Test query",
                format=OUTPUT_FORMAT_TABLE,
                openai_api_key="test-key"
            )
        
        assert "QUESTION:" in result
        assert "CYPHER QUERY:" in result
        assert "RESULTS (1 rows):" in result
        assert "name" in result
        assert "value" in result
    
    def test_format_schema_for_llm(self):
        """Test schema formatting for LLM context."""
        schema = {
            "nodes": [
                {"label": "Patient", "properties": ["subject_id", "gender"]},
                {"label": "Admission", "properties": ["hadm_id", "admission_type"]}
            ],
            "relationships": [
                {"relationshipType": "HAS_ADMISSION"},
                {"relationshipType": "HAS_DIAGNOSIS"}
            ]
        }
        
        formatted = format_schema_for_llm(schema)
        
        # Assertions
        assert "NODES:" in formatted
        assert "- Patient: subject_id, gender" in formatted
        assert "- Admission: hadm_id, admission_type" in formatted
        assert "RELATIONSHIPS:" in formatted
        assert "- HAS_ADMISSION" in formatted
        assert "KEY RELATIONSHIPS:" in formatted
        assert "(Patient)-[:HAS_ADMISSION]->(Admission)" in formatted
    
    @pytest.mark.asyncio
    async def test_natural_query_empty_results(self, mock_db_connection, mock_openai_response):
        """Test handling of empty query results."""
        mock_db_connection.get_schema.return_value = {"nodes": [], "relationships": []}
        mock_db_connection.execute_read.return_value = []
        
        mock_openai_response.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(content='MATCH (n:NonExistent) RETURN n')
            )]
        )
        
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.natural_query.OpenAI', return_value=mock_openai_response):
            result = await natural_query(
                mock_db_connection,
                query="Find non-existent data",
                format=OUTPUT_FORMAT_MARKDOWN,
                openai_api_key="test-key"
            )
        
        assert "No results found." in result


@pytest.mark.integration
class TestNaturalQueryIntegration:
    """Integration tests with real Neo4j database and OpenAI."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not configured")
    async def test_natural_query_real_integration(self, real_db_connection):
        """Test natural language query with real database and OpenAI."""
        openai_key = os.getenv("OPENAI_API_KEY")
        
        result = await natural_query(
            real_db_connection,
            query="How many patients are in the database?",
            limit=10,
            format=OUTPUT_FORMAT_JSON,
            openai_api_key=openai_key
        )
        
        data = json.loads(result)
        
        # Print the full response for debugging
        print("\n" + "="*80)
        print("NATURAL LANGUAGE QUERY TEST RESULTS")
        print("="*80)
        print(f"Question: {data.get('question', 'N/A')}")
        print(f"\nGenerated Cypher Query:\n{data.get('cypher_query', 'N/A')}")
        print(f"\nResult Count: {data.get('count', 0)}")
        print(f"\nResults: {json.dumps(data.get('results', []), indent=2)}")
        print("="*80 + "\n")
        
        # Basic assertions
        assert 'cypher_query' in data
        assert 'results' in data
        # Verify it generated a query about patients
        assert 'Patient' in data['cypher_query']