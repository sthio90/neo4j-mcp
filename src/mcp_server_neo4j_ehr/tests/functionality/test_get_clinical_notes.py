"""Tests for get clinical notes functionality."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from ...modules.functionality.get_clinical_notes import get_clinical_notes
from ...modules.constants import (
    OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_TEXT,
    NOTE_TYPE_DISCHARGE, NOTE_TYPE_RADIOLOGY, NOTE_TYPE_ALL
)


class TestGetClinicalNotesFunctionality:
    """Test suite for get clinical notes functionality."""
    
    @pytest.mark.asyncio
    async def test_get_all_notes(self, mock_db_connection, sample_discharge_note):
        """Test getting all notes without filters."""
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
        result = await get_clinical_notes(
            mock_db_connection,
            note_type=NOTE_TYPE_ALL,
            limit=5,
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
    async def test_get_discharge_notes_by_admission(self, mock_db_connection, sample_discharge_note):
        """Test getting discharge notes for specific admission."""
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
        result = await get_clinical_notes(
            mock_db_connection,
            note_type=NOTE_TYPE_DISCHARGE,
            admission_id=sample_discharge_note.hadm_id,
            limit=10,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['hadm_id'] == sample_discharge_note.hadm_id
        
        # Check the query was built correctly
        call_args = mock_db_connection.execute_read.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "note:DischargeNote" in query
        assert "note.hadm_id = $admission_id" in query
        assert params['admission_id'] == sample_discharge_note.hadm_id
    
    @pytest.mark.asyncio
    async def test_get_radiology_notes_by_patient(self, mock_db_connection):
        """Test getting radiology reports for specific patient."""
        # Mock radiology report data
        mock_radiology_data = {
            'note_id': 'RR-123',
            'note_type': 'RR',
            'subject_id': '10461137',
            'hadm_id': '25236814',
            'charttime': None,
            'text': 'CT SCAN: Pulmonary fibrosis noted...'
        }
        
        # Mock database response
        mock_db_connection.execute_read.return_value = [mock_radiology_data]
        
        # Call function
        result = await get_clinical_notes(
            mock_db_connection,
            note_type=NOTE_TYPE_RADIOLOGY,
            patient_id=mock_radiology_data['subject_id'],
            limit=10,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['subject_id'] == mock_radiology_data['subject_id']
        
        # Check the query was built correctly
        call_args = mock_db_connection.execute_read.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "note:RadiologyReport" in query
        assert "note.subject_id = $patient_id" in query
        assert params['patient_id'] == mock_radiology_data['subject_id']
    
    @pytest.mark.asyncio
    async def test_empty_results(self, mock_db_connection):
        """Test when no notes are found."""
        # Mock empty response
        mock_db_connection.execute_read.return_value = []
        
        # Call function
        result = await get_clinical_notes(
            mock_db_connection,
            note_type=NOTE_TYPE_ALL,
            patient_id="non_existent",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_table_format_output(self, mock_db_connection, sample_discharge_note):
        """Test table format output."""
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
        result = await get_clinical_notes(
            mock_db_connection,
            note_type=NOTE_TYPE_ALL,
            limit=5,
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "Note ID" in result
        assert "Type" in result
        assert "Patient ID" in result
        assert sample_discharge_note.note_id in result
    
    @pytest.mark.asyncio
    async def test_text_format_output(self, mock_db_connection, sample_discharge_note):
        """Test text format output."""
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
        result = await get_clinical_notes(
            mock_db_connection,
            note_type=NOTE_TYPE_ALL,
            limit=5,
            format=OUTPUT_FORMAT_TEXT
        )
        
        # Assertions
        assert isinstance(result, str)
        assert f"Note 1/1" in result
        assert f"ID: {sample_discharge_note.note_id}" in result
        assert sample_discharge_note.text in result