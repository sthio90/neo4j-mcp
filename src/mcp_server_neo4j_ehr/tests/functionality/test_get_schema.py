"""Tests for get schema functionality."""

import json
import pytest

from ...modules.functionality.get_schema import get_schema, format_schema_as_markdown
from ...modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_MARKDOWN


class TestGetSchemaFunctionality:
    """Test suite for get schema functionality."""
    
    @pytest.mark.asyncio
    async def test_get_schema_json_format(self, mock_db_connection):
        """Test getting schema in JSON format."""
        # Mock schema response
        mock_schema = {
            "nodes": [
                {"label": "Patient", "properties": ["subject_id", "gender", "anchor_age"]},
                {"label": "Admission", "properties": ["hadm_id", "admission_type", "admittime"]},
                {"label": "Diagnosis", "properties": ["icd_code", "long_title"]}
            ],
            "relationships": [
                {"relationshipType": "HAS_ADMISSION"},
                {"relationshipType": "HAS_DIAGNOSIS"}
            ],
            "constraints": [
                {"name": "patient_subject_id_unique", "type": "UNIQUE"},
            ],
            "indexes": [
                {"name": "patient_subject_id_index", "state": "ONLINE"},
            ]
        }
        mock_db_connection.get_schema.return_value = mock_schema
        
        # Call function
        result = await get_schema(mock_db_connection, format=OUTPUT_FORMAT_JSON)
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'nodes' in data
        assert 'relationships' in data
        assert 'known_relationships' in data
        assert len(data['nodes']) == 3
        assert len(data['relationships']) == 2
        
        # Check known relationships were added
        assert len(data['known_relationships']) == 7  # All predefined relationships
        known_rel = data['known_relationships'][0]
        assert 'from' in known_rel
        assert 'to' in known_rel
        assert 'type' in known_rel
        assert 'description' in known_rel
    
    @pytest.mark.asyncio
    async def test_get_schema_markdown_format(self, mock_db_connection):
        """Test getting schema in markdown format."""
        # Mock schema response
        mock_schema = {
            "nodes": [
                {"label": "Patient", "properties": ["subject_id", "gender"]},
                {"label": "Admission", "properties": ["hadm_id", "admission_type"]}
            ],
            "relationships": [
                {"relationshipType": "HAS_ADMISSION"}
            ],
            "constraints": [
                {"name": "constraint_1"}
            ],
            "indexes": [
                {"name": "index_1", "state": "ONLINE"}
            ]
        }
        mock_db_connection.get_schema.return_value = mock_schema
        
        # Call function
        result = await get_schema(mock_db_connection, format=OUTPUT_FORMAT_MARKDOWN)
        
        # Assertions for markdown content
        assert "# Neo4j EHR Database Schema" in result
        assert "## Node Types" in result
        assert "### Patient" in result
        assert "**Properties:** subject_id, gender" in result
        assert "### Admission" in result
        assert "## Relationships" in result
        assert "### HAS_ADMISSION" in result
        assert "- **From:** Patient" in result
        assert "- **To:** Admission" in result
        assert "## Indexes" in result
        assert "- index_1 (State: ONLINE)" in result
        assert "## Constraints" in result
        assert "- constraint_1" in result
        assert "## Example Queries" in result
    
    @pytest.mark.asyncio
    async def test_get_schema_empty_collections(self, mock_db_connection):
        """Test handling of empty schema collections."""
        # Mock minimal schema
        mock_schema = {
            "nodes": [],
            "relationships": [],
            "constraints": [],
            "indexes": []
        }
        mock_db_connection.get_schema.return_value = mock_schema
        
        # Call function
        result = await get_schema(mock_db_connection, format=OUTPUT_FORMAT_JSON)
        
        # Parse result
        data = json.loads(result)
        
        # Should still have known relationships
        assert data['nodes'] == []
        assert data['relationships'] == []
        assert len(data['known_relationships']) == 7
    
    def test_format_schema_as_markdown_complete(self):
        """Test markdown formatting with complete schema."""
        schema = {
            "nodes": [
                {"label": "Patient", "properties": ["subject_id", "gender", "anchor_age"]},
                {"label": "Admission", "properties": ["hadm_id", "admission_type"]},
                {"label": "DischargeNote", "properties": ["note_id", "text", "charttime"]}
            ],
            "relationships": [
                {"relationshipType": "HAS_ADMISSION"},
                {"relationshipType": "INCLUDES_DISCHARGE_NOTE"}
            ],
            "known_relationships": [
                {
                    "from": "Patient",
                    "to": "Admission",
                    "type": "HAS_ADMISSION",
                    "description": "Patient has hospital admissions"
                },
                {
                    "from": "Admission",
                    "to": "DischargeNote",
                    "type": "INCLUDES_DISCHARGE_NOTE",
                    "description": "Admission includes discharge summary notes"
                }
            ],
            "indexes": [
                {"name": "patient_subject_id_idx", "state": "ONLINE"},
                {"name": "note_embeddings", "state": "ONLINE"}
            ],
            "constraints": [
                {"name": "patient_subject_id_unique"},
                {"name": "admission_hadm_id_unique"}
            ]
        }
        
        result = format_schema_as_markdown(schema)
        
        # Verify all sections are present
        assert "# Neo4j EHR Database Schema" in result
        assert "## Node Types" in result
        assert "### Patient" in result
        assert "### Admission" in result
        assert "### DischargeNote" in result
        assert "## Relationships" in result
        assert "### HAS_ADMISSION" in result
        assert "### INCLUDES_DISCHARGE_NOTE" in result
        assert "## Indexes" in result
        assert "patient_subject_id_idx" in result
        assert "## Constraints" in result
        assert "patient_subject_id_unique" in result
        assert "## Example Queries" in result
        
        # Verify example queries are included
        assert "Get patient with all admissions" in result
        assert "Find discharge notes mentioning a condition" in result
        assert "Get abnormal lab results for a patient" in result
    
    def test_format_schema_as_markdown_minimal(self):
        """Test markdown formatting with minimal schema."""
        schema = {
            "nodes": [{"label": "TestNode", "properties": ["id"]}],
            "relationships": [],
            "known_relationships": [],
            "indexes": [],
            "constraints": []
        }
        
        result = format_schema_as_markdown(schema)
        
        # Should still have all sections, even if empty
        assert "## Node Types" in result
        assert "### TestNode" in result
        assert "## Relationships" in result
        assert "## Example Queries" in result
    
    @pytest.mark.asyncio
    async def test_get_schema_preserves_original(self, mock_db_connection):
        """Test that getting schema preserves original database schema data."""
        # Mock schema with extra fields
        mock_schema = {
            "nodes": [{"label": "Patient", "properties": ["subject_id"], "extra": "data"}],
            "relationships": [{"relationshipType": "HAS_ADMISSION", "count": 100}],
            "constraints": [],
            "indexes": [],
            "custom_field": "should be preserved"
        }
        mock_db_connection.get_schema.return_value = mock_schema
        
        # Call function
        result = await get_schema(mock_db_connection, format=OUTPUT_FORMAT_JSON)
        
        # Parse result
        data = json.loads(result)
        
        # Original fields should be preserved
        assert data['nodes'][0].get('extra') == "data"
        assert data['relationships'][0].get('count') == 100
        assert data.get('custom_field') == "should be preserved"


@pytest.mark.integration
class TestGetSchemaIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_get_real_schema(self, real_db_connection):
        """Test getting real schema from the database."""
        # Get schema in JSON format
        result = await get_schema(real_db_connection, format=OUTPUT_FORMAT_JSON)
        data = json.loads(result)
        
        # Basic assertions
        assert 'nodes' in data
        assert 'relationships' in data
        assert 'known_relationships' in data
        
        # Should have at least Patient node
        patient_nodes = [n for n in data['nodes'] if n['label'] == 'Patient']
        assert len(patient_nodes) > 0
        
        # Get schema in markdown format
        result_md = await get_schema(real_db_connection, format=OUTPUT_FORMAT_MARKDOWN)
        
        # Should be valid markdown
        assert isinstance(result_md, str)
        assert "# Neo4j EHR Database Schema" in result_md
        assert "Patient" in result_md