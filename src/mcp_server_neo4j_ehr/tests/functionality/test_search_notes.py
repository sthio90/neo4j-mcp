"""Tests for search notes functionality."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ...modules.functionality.search_notes import search_notes, text_search, semantic_search
from ...modules.constants import (
    OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_TEXT,
    NOTE_TYPE_DISCHARGE, NOTE_TYPE_RADIOLOGY, NOTE_TYPE_ALL
)


class TestSearchNotesFunctionality:
    """Test suite for search notes functionality."""
    
    @pytest.mark.asyncio
    async def test_text_search_basic(self, mock_db_connection, sample_discharge_note):
        """Test basic text search functionality."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'note_id': sample_discharge_note.note_id,
            'note_type': sample_discharge_note.note_type,
            'subject_id': sample_discharge_note.subject_id,
            'hadm_id': sample_discharge_note.hadm_id,
            'charttime': sample_discharge_note.charttime,
            'text': sample_discharge_note.text
        }]
        
        # Call function
        result = await search_notes(
            mock_db_connection,
            query="heart failure",
            note_type=NOTE_TYPE_ALL,
            limit=5,
            semantic=False,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['note_id'] == sample_discharge_note.note_id
        assert data[0]['text'] == sample_discharge_note.text
    
    @pytest.mark.asyncio
    async def test_text_search_with_filters(self, mock_db_connection):
        """Test text search with patient and admission filters."""
        # Mock empty response
        mock_db_connection.execute_read.return_value = []
        
        # Call function with filters
        await search_notes(
            mock_db_connection,
            query="medication",
            note_type=NOTE_TYPE_DISCHARGE,
            patient_id="10000032",
            admission_id="22595853",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify query includes filters
        query = mock_db_connection.execute_read.call_args[0][0]
        params = mock_db_connection.execute_read.call_args[0][1]
        
        assert "note:DischargeNote" in query
        assert "note.subject_id = $patient_id" in query
        assert "note.hadm_id = $admission_id" in query
        assert params['patient_id'] == "10000032"
        assert params['admission_id'] == "22595853"
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, mock_db_connection, mock_openai_response):
        """Test semantic search functionality."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'note_id': 'note_001',
            'note_type': 'Discharge summary',
            'subject_id': '10000032',
            'hadm_id': '22595853',
            'charttime': '2124-08-10T14:00:00',
            'text': 'Patient with heart failure',
            'score': 0.95
        }]
        
        # Mock OpenAI
        with patch('src.mcp_server_neo4j_ehr.modules.functionality.search_notes.OpenAI', return_value=mock_openai_response):
            result = await search_notes(
                mock_db_connection,
                query="cardiac issues",
                semantic=True,
                limit=5,
                format=OUTPUT_FORMAT_JSON,
                openai_api_key="test-key"
            )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert len(data) == 1
        assert data[0]['score'] == 0.95
        
        # Verify vector search query was used
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "db.index.vector.queryNodes" in query
    
    @pytest.mark.asyncio
    async def test_semantic_search_no_api_key(self, mock_db_connection):
        """Test semantic search without API key returns error."""
        result = await search_notes(
            mock_db_connection,
            query="test",
            semantic=True,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert 'error' in data
        assert "OpenAI API key is required" in data['error']
    
    @pytest.mark.asyncio
    async def test_note_type_filtering(self, mock_db_connection):
        """Test filtering by note type."""
        mock_db_connection.execute_read.return_value = []
        
        # Test discharge notes only
        await search_notes(
            mock_db_connection,
            query="test",
            note_type=NOTE_TYPE_DISCHARGE,
            format=OUTPUT_FORMAT_JSON
        )
        
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "note:DischargeNote" in query
        
        # Test radiology reports only
        await search_notes(
            mock_db_connection,
            query="test",
            note_type=NOTE_TYPE_RADIOLOGY,
            format=OUTPUT_FORMAT_JSON
        )
        
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "note:RadiologyReport" in query
    
    @pytest.mark.asyncio
    async def test_table_format_output(self, mock_db_connection, sample_discharge_note):
        """Test table format output."""
        mock_db_connection.execute_read.return_value = [{
            'note_id': sample_discharge_note.note_id,
            'note_type': sample_discharge_note.note_type,
            'subject_id': sample_discharge_note.subject_id,
            'hadm_id': sample_discharge_note.hadm_id,
            'charttime': str(sample_discharge_note.charttime),
            'text': sample_discharge_note.text
        }]
        
        result = await search_notes(
            mock_db_connection,
            query="test",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "Note ID" in result
        assert "Type" in result
        assert sample_discharge_note.note_id in result
    
    @pytest.mark.asyncio
    async def test_text_format_output(self, mock_db_connection, sample_discharge_note):
        """Test text format output."""
        mock_db_connection.execute_read.return_value = [{
            'note_id': sample_discharge_note.note_id,
            'note_type': sample_discharge_note.note_type,
            'subject_id': sample_discharge_note.subject_id,
            'hadm_id': sample_discharge_note.hadm_id,
            'charttime': str(sample_discharge_note.charttime),
            'text': sample_discharge_note.text
        }]
        
        result = await search_notes(
            mock_db_connection,
            query="test",
            format=OUTPUT_FORMAT_TEXT
        )
        
        # Assertions
        assert isinstance(result, str)
        assert f"Note 1/1" in result
        assert sample_discharge_note.text in result
        assert "=" * 80 in result  # Separator
    
    @pytest.mark.asyncio
    async def test_empty_search_results(self, mock_db_connection):
        """Test handling of empty search results."""
        mock_db_connection.execute_read.return_value = []
        
        # JSON format
        result = await search_notes(
            mock_db_connection,
            query="nonexistent",
            format=OUTPUT_FORMAT_JSON
        )
        assert json.loads(result) == []
        
        # Table format
        result = await search_notes(
            mock_db_connection,
            query="nonexistent",
            format=OUTPUT_FORMAT_TABLE
        )
        assert result == "No notes found."
        
        # Text format
        result = await search_notes(
            mock_db_connection,
            query="nonexistent",
            format=OUTPUT_FORMAT_TEXT
        )
        assert result == "No notes found."


@pytest.mark.integration
class TestSearchNotesIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_search_real_notes(self, real_db_connection):
        """Test searching real notes in the database."""
        # Search for common medical terms
        result = await search_notes(
            real_db_connection,
            query="patient",  # Common word likely to exist
            limit=2,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Basic assertions
        assert isinstance(data, list)
        # If results found, verify structure
        if data:
            note = data[0]
            assert 'note_id' in note
            assert 'text' in note
            assert 'note_type' in note