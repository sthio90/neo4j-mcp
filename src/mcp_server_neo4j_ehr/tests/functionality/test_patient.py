"""Tests for patient query functionality."""

import json
import pytest
from unittest.mock import AsyncMock

from ...modules.functionality.patient import get_patient
from ...modules.data_types import OutputFormat
from ...modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


class TestPatientFunctionality:
    """Test suite for patient query functionality."""
    
    @pytest.mark.asyncio
    async def test_get_patient_basic(self, mock_db_connection, sample_patient):
        """Test basic patient retrieval without additional data."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'p': sample_patient.model_dump()
        }]
        
        # Call function
        result = await get_patient(
            mock_db_connection,
            subject_id="10000032",
            include_admissions=False,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'patient' in data
        assert data['patient']['subject_id'] == "10000032"
        assert data['patient']['gender'] == "M"
        assert 'admissions' not in data
        
        # Verify query was called correctly
        mock_db_connection.execute_read.assert_called_once()
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "MATCH (p:Patient {subject_id: $subject_id})" in query
        assert "HAS_ADMISSION" not in query
    
    @pytest.mark.asyncio
    async def test_get_patient_with_admissions(
        self, mock_db_connection, sample_patient, sample_admission
    ):
        """Test patient retrieval with admissions."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'p': sample_patient.model_dump(),
            'admissions': [sample_admission.model_dump()]
        }]
        
        # Call function
        result = await get_patient(
            mock_db_connection,
            subject_id="10000032",
            include_admissions=True,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'admissions' in data
        assert len(data['admissions']) == 1
        assert data['admissions'][0]['hadm_id'] == "22595853"
        
        # Verify query includes admission join
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "OPTIONAL MATCH (p)-[:HAS_ADMISSION]->(a:Admission)" in query
    
    @pytest.mark.asyncio
    async def test_get_patient_with_all_data(
        self, mock_db_connection, sample_patient, sample_admission,
        sample_diagnosis, sample_procedure, sample_medication, sample_lab_event
    ):
        """Test patient retrieval with all related data."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'p': sample_patient.model_dump(),
            'admissions': [sample_admission.model_dump()],
            'diagnoses': [sample_diagnosis.model_dump()],
            'procedures': [sample_procedure.model_dump()],
            'medications': [sample_medication.model_dump()],
            'lab_events': [sample_lab_event.model_dump()]
        }]
        
        # Call function with all includes
        result = await get_patient(
            mock_db_connection,
            subject_id="10000032",
            include_admissions=True,
            include_diagnoses=True,
            include_procedures=True,
            include_medications=True,
            include_lab_events=True,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert all(key in data for key in [
            'patient', 'admissions', 'diagnoses', 
            'procedures', 'medications', 'lab_events'
        ])
        assert len(data['diagnoses']) == 1
        assert data['diagnoses'][0]['icd_code'] == "I50.9"
        assert len(data['medications']) == 1
        assert data['medications'][0]['medication'] == "Furosemide"
    
    @pytest.mark.asyncio
    async def test_patient_not_found(self, mock_db_connection):
        """Test handling when patient is not found."""
        # Mock empty response
        mock_db_connection.execute_read.return_value = []
        
        # Call function
        result = await get_patient(
            mock_db_connection,
            subject_id="99999999",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'error' in data
        assert "Patient 99999999 not found" in data['error']
    
    @pytest.mark.asyncio
    async def test_get_patient_table_format(
        self, mock_db_connection, sample_patient, sample_admission
    ):
        """Test patient retrieval with table format output."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'p': sample_patient.model_dump(),
            'admissions': [sample_admission.model_dump()]
        }]
        
        # Call function with table format
        result = await get_patient(
            mock_db_connection,
            subject_id="10000032",
            include_admissions=True,
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "PATIENT INFORMATION" in result
        assert "Subject ID" in result
        assert "10000032" in result
        assert "ADMISSIONS" in result
        assert "22595853" in result
    
    @pytest.mark.asyncio
    async def test_empty_collections_handling(self, mock_db_connection, sample_patient):
        """Test handling of empty collections in response."""
        # Mock response with empty collections
        mock_db_connection.execute_read.return_value = [{
            'p': sample_patient.model_dump(),
            'admissions': [],
            'diagnoses': None,  # Test None handling
            'medications': []
        }]
        
        # Call function
        result = await get_patient(
            mock_db_connection,
            subject_id="10000032",
            include_admissions=True,
            include_diagnoses=True,
            include_medications=True,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert data['admissions'] == []
        assert 'diagnoses' not in data or data['diagnoses'] == []
        assert data['medications'] == []


@pytest.mark.integration
class TestPatientIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_get_real_patient(self, real_db_connection):
        """Test getting a real patient from the database."""
        # Use a patient ID that exists in your test database
        result = await get_patient(
            real_db_connection,
            subject_id="10461137",  # Using actual patient ID from database
            include_admissions=True,
            include_diagnoses=True,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Basic assertions
        assert 'patient' in data
        assert data['patient']['subject_id'] == "10461137"
        
        # If patient has admissions, verify structure
        if 'admissions' in data and data['admissions']:
            admission = data['admissions'][0]
            assert 'hadm_id' in admission
            assert 'admission_type' in admission