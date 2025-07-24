"""Tests for list medications functionality."""

import json
import pytest

from ...modules.functionality.list_medications import list_medications
from ...modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


class TestListMedicationsFunctionality:
    """Test suite for list medications functionality."""
    
    @pytest.mark.asyncio
    async def test_list_medications_by_admission(self, mock_db_connection, sample_medication):
        """Test listing medications for a specific admission."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'm': sample_medication.model_dump()
        }]
        
        # Call function
        result = await list_medications(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'medications' in data
        assert 'count' in data
        assert data['count'] == 1
        assert data['medications'][0]['medication'] == "Furosemide"
        assert data['medications'][0]['route'] == "PO"
        assert data['medications'][0]['frequency'] == "BID"
        
        # Verify query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "m.hadm_id = $admission_id" in query
        assert "ORDER BY m.verifiedtime DESC" in query
    
    @pytest.mark.asyncio
    async def test_list_medications_by_patient(self, mock_db_connection, sample_medication):
        """Test listing medications for a specific patient."""
        mock_db_connection.execute_read.return_value = [{
            'm': sample_medication.model_dump()
        }]
        
        # Call function
        result = await list_medications(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify query uses patient_id
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "m.subject_id = $patient_id" in query
    
    @pytest.mark.asyncio
    async def test_list_medications_by_name(self, mock_db_connection, sample_medication):
        """Test filtering medications by name."""
        mock_db_connection.execute_read.return_value = [{
            'm': sample_medication.model_dump()
        }]
        
        # Call function
        result = await list_medications(
            mock_db_connection,
            patient_id="10000032",
            medication="furosemide",  # Test case-insensitive search
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify medication filter
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "toLower(m.medication) CONTAINS toLower($medication)" in query
        
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['medication'] == "furosemide"
    
    @pytest.mark.asyncio
    async def test_list_medications_by_route(self, mock_db_connection, sample_medication):
        """Test filtering medications by route."""
        mock_db_connection.execute_read.return_value = [{
            'm': sample_medication.model_dump()
        }]
        
        # Call function
        result = await list_medications(
            mock_db_connection,
            admission_id="22595853",
            route="po",  # Test case-insensitive
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify route filter
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "toLower(m.route) = toLower($route)" in query
        
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['route'] == "po"
    
    @pytest.mark.asyncio
    async def test_list_medications_no_params_error(self, mock_db_connection):
        """Test error when neither patient_id nor admission_id provided."""
        result = await list_medications(
            mock_db_connection,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert 'error' in data
        assert "Either patient_id or admission_id must be provided" in data['error']
    
    @pytest.mark.asyncio
    async def test_list_medications_empty_results(self, mock_db_connection):
        """Test handling of empty results."""
        mock_db_connection.execute_read.return_value = []
        
        result = await list_medications(
            mock_db_connection,
            patient_id="99999999",
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert data['medications'] == []
        assert data['message'] == "No medications found"
    
    @pytest.mark.asyncio
    async def test_list_medications_table_format(self, mock_db_connection, sample_medication):
        """Test table format output."""
        # Add verifiedtime to sample
        med_data = sample_medication.model_dump()
        med_data['verifiedtime'] = '2124-08-08T10:00:00'
        
        mock_db_connection.execute_read.return_value = [{'m': med_data}]
        
        result = await list_medications(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "Medication" in result
        assert "Route" in result
        assert "Frequency" in result
        assert "Furosemide" in result
        assert "PO" in result
        assert "BID" in result
        assert "2124-08-08" in result
    
    @pytest.mark.asyncio
    async def test_list_medications_missing_fields(self, mock_db_connection):
        """Test handling medications with missing optional fields."""
        # Medication with minimal fields
        minimal_med = {
            'medication': 'Aspirin',
            'hadm_id': '22595853',
            'subject_id': '10000032',
            'route': None,
            'frequency': None,
            'verifiedtime': None
        }
        
        mock_db_connection.execute_read.return_value = [{'m': minimal_med}]
        
        result = await list_medications(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Should show N/A for missing fields
        assert "Aspirin" in result
        assert "N/A" in result  # For missing fields
    
    @pytest.mark.asyncio
    async def test_list_medications_combined_filters(self, mock_db_connection):
        """Test using multiple filters together."""
        mock_db_connection.execute_read.return_value = []
        
        await list_medications(
            mock_db_connection,
            patient_id="10000032",
            medication="metformin",
            route="PO",
            limit=5,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify all conditions in query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "m.subject_id = $patient_id" in query
        assert "toLower(m.medication) CONTAINS toLower($medication)" in query
        assert "toLower(m.route) = toLower($route)" in query
        
        # Verify all parameters
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['patient_id'] == "10000032"
        assert params['medication'] == "metformin"
        assert params['route'] == "PO"
        assert params['limit'] == 5


@pytest.mark.integration
class TestListMedicationsIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_list_real_medications_by_patient(self, real_db_connection):
        """Test listing real medications from the database."""
        result = await list_medications(
            real_db_connection,
            patient_id="10461137",  # Adjust based on test data
            limit=5,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        
        # Basic assertions
        assert 'medications' in data
        assert 'count' in data
        assert isinstance(data['medications'], list)
        
        # If medications found, verify structure
        if data['medications']:
            medication = data['medications'][0]
            assert 'medication' in medication