"""Tests for list diagnoses functionality."""

import json
import pytest

from ...modules.functionality.list_diagnoses import list_diagnoses
from ...modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


class TestListDiagnosesFunctionality:
    """Test suite for list diagnoses functionality."""
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_by_admission(self, mock_db_connection, sample_diagnosis):
        """Test listing diagnoses for a specific admission."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'd': sample_diagnosis.model_dump()
        }]
        
        # Call function
        result = await list_diagnoses(
            mock_db_connection,
            admission_id="22595853",
            limit=20,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'diagnoses' in data
        assert 'count' in data
        assert data['count'] == 1
        assert data['diagnoses'][0]['icd_code'] == "I50.9"
        assert data['diagnoses'][0]['long_title'] == "Heart failure, unspecified"
        
        # Verify query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "MATCH (a:Admission {hadm_id: $admission_id})" in query
        assert "-[:HAS_DIAGNOSIS]->" in query
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_by_patient(self, mock_db_connection, sample_diagnosis):
        """Test listing diagnoses for a specific patient."""
        # Mock database response with admission ID
        diagnosis_data = sample_diagnosis.model_dump()
        mock_db_connection.execute_read.return_value = [{
            'd': diagnosis_data,
            'hadm_id': "22595853"
        }]
        
        # Call function
        result = await list_diagnoses(
            mock_db_connection,
            patient_id="10000032",
            limit=20,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert data['count'] == 1
        assert data['diagnoses'][0]['hadm_id'] == "22595853"
        
        # Verify query includes patient join
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "MATCH (p:Patient {subject_id: $patient_id})" in query
        assert "-[:HAS_ADMISSION]->" in query
        assert "-[:HAS_DIAGNOSIS]->" in query
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_no_params_error(self, mock_db_connection):
        """Test error when neither patient_id nor admission_id provided."""
        result = await list_diagnoses(
            mock_db_connection,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert 'error' in data
        assert "Either patient_id or admission_id must be provided" in data['error']
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_empty_results(self, mock_db_connection):
        """Test handling of empty results."""
        mock_db_connection.execute_read.return_value = []
        
        result = await list_diagnoses(
            mock_db_connection,
            admission_id="99999999",
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert data['diagnoses'] == []
        assert data['message'] == "No diagnoses found"
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_table_format(self, mock_db_connection, sample_diagnosis):
        """Test table format output."""
        mock_db_connection.execute_read.return_value = [{
            'd': sample_diagnosis.model_dump()
        }]
        
        result = await list_diagnoses(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "ICD Code" in result
        assert "Description" in result
        assert "I50.9" in result
        assert "Heart failure, unspecified" in result
        assert "ICD-10" in result
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_limit(self, mock_db_connection, sample_diagnosis):
        """Test limit parameter."""
        # Mock multiple diagnoses
        diagnoses = []
        for i in range(5):
            diag = sample_diagnosis.model_dump()
            diag['seq_num'] = i + 1
            diag['icd_code'] = f"I50.{i}"
            diagnoses.append({'d': diag})
        
        mock_db_connection.execute_read.return_value = diagnoses[:3]  # Limited to 3
        
        result = await list_diagnoses(
            mock_db_connection,
            admission_id="22595853",
            limit=3,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert len(data['diagnoses']) == 3
        
        # Verify limit in query
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['limit'] == 3
    
    @pytest.mark.asyncio
    async def test_list_diagnoses_ordering(self, mock_db_connection):
        """Test correct ordering of results."""
        # For admission query
        await list_diagnoses(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_JSON
        )
        
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "ORDER BY d.seq_num" in query
        
        # For patient query
        await list_diagnoses(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_JSON
        )
        
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "ORDER BY a.admittime DESC, d.seq_num" in query


@pytest.mark.integration
class TestListDiagnosesIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_list_real_diagnoses_by_patient(self, real_db_connection):
        """Test listing real diagnoses from the database."""
        result = await list_diagnoses(
            real_db_connection,
            patient_id="10461137",  # Adjust based on test data
            limit=5,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        
        # Basic assertions
        assert 'diagnoses' in data
        assert 'count' in data
        assert isinstance(data['diagnoses'], list)
        
        # If diagnoses found, verify structure
        if data['diagnoses']:
            diagnosis = data['diagnoses'][0]
            assert 'icd_code' in diagnosis
            assert 'hadm_id' in diagnosis