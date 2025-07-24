"""Tests for list procedures functionality."""

import json
import pytest

from ...modules.functionality.list_procedures import list_procedures
from ...modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


class TestListProceduresFunctionality:
    """Test suite for list procedures functionality."""
    
    @pytest.mark.asyncio
    async def test_list_procedures_by_admission(self, mock_db_connection, sample_procedure):
        """Test listing procedures for a specific admission."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'p': sample_procedure.model_dump()
        }]
        
        # Call function
        result = await list_procedures(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'procedures' in data
        assert 'count' in data
        assert data['count'] == 1
        assert data['procedures'][0]['icd_code'] == "99.04"
        assert data['procedures'][0]['long_title'] == "Transfusion of packed cells"
        assert data['procedures'][0]['icd_version'] == 9
        
        # Verify query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "MATCH (a:Admission {hadm_id: $admission_id})" in query
        assert "-[:HAS_PROCEDURE]->" in query
        assert "ORDER BY p.seq_num" in query
    
    @pytest.mark.asyncio
    async def test_list_procedures_by_patient(self, mock_db_connection, sample_procedure):
        """Test listing procedures for a specific patient."""
        # Mock database response with admission ID
        procedure_data = sample_procedure.model_dump()
        mock_db_connection.execute_read.return_value = [{
            'p': procedure_data,
            'hadm_id': "22595853"
        }]
        
        # Call function
        result = await list_procedures(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert data['count'] == 1
        assert data['procedures'][0]['hadm_id'] == "22595853"
        
        # Verify query includes patient join
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "MATCH (pat:Patient {subject_id: $patient_id})" in query
        assert "-[:HAS_ADMISSION]->" in query
        assert "-[:HAS_PROCEDURE]->" in query
        assert "ORDER BY p.chartdate DESC, p.seq_num" in query
    
    @pytest.mark.asyncio
    async def test_list_procedures_no_params_error(self, mock_db_connection):
        """Test error when neither patient_id nor admission_id provided."""
        result = await list_procedures(
            mock_db_connection,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert 'error' in data
        assert "Either patient_id or admission_id must be provided" in data['error']
    
    @pytest.mark.asyncio
    async def test_list_procedures_empty_results(self, mock_db_connection):
        """Test handling of empty results."""
        mock_db_connection.execute_read.return_value = []
        
        result = await list_procedures(
            mock_db_connection,
            admission_id="99999999",
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert data['procedures'] == []
        assert data['message'] == "No procedures found"
    
    @pytest.mark.asyncio
    async def test_list_procedures_table_format(self, mock_db_connection, sample_procedure):
        """Test table format output."""
        mock_db_connection.execute_read.return_value = [{
            'p': sample_procedure.model_dump()
        }]
        
        result = await list_procedures(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "ICD Code" in result
        assert "Description" in result
        assert "Chart Date" in result
        assert "99.04" in result
        assert "Transfusion of packed cells" in result
        assert "2124-08-08" in result
        assert "ICD-9" in result
    
    @pytest.mark.asyncio
    async def test_list_procedures_limit(self, mock_db_connection, sample_procedure):
        """Test limit parameter."""
        # Mock multiple procedures
        procedures = []
        for i in range(5):
            proc = sample_procedure.model_dump()
            proc['seq_num'] = i + 1
            proc['icd_code'] = f"99.0{i}"
            procedures.append({'p': proc})
        
        mock_db_connection.execute_read.return_value = procedures[:3]  # Limited to 3
        
        result = await list_procedures(
            mock_db_connection,
            admission_id="22595853",
            limit=3,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert len(data['procedures']) == 3
        
        # Verify limit in query
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['limit'] == 3
    
    @pytest.mark.asyncio
    async def test_list_procedures_missing_fields(self, mock_db_connection):
        """Test handling procedures with missing optional fields."""
        # Procedure with minimal fields
        minimal_proc = {
            'icd_code': '99.99',
            'long_title': None,
            'hadm_id': '22595853',
            'seq_num': None,
            'chartdate': None,
            'icd_version': None
        }
        
        mock_db_connection.execute_read.return_value = [{'p': minimal_proc}]
        
        result = await list_procedures(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Should show N/A for missing fields
        assert "99.99" in result
        assert "N/A" in result  # For missing fields
    
    @pytest.mark.asyncio
    async def test_list_procedures_ordering(self, mock_db_connection):
        """Test correct ordering of results."""
        # Multiple procedures with different dates and sequences
        procedures = [
            {
                'p': {
                    'icd_code': '99.01',
                    'long_title': 'Procedure 1',
                    'seq_num': 2,
                    'chartdate': '2124-08-08'
                }
            },
            {
                'p': {
                    'icd_code': '99.02',
                    'long_title': 'Procedure 2',
                    'seq_num': 1,
                    'chartdate': '2124-08-08'
                }
            }
        ]
        
        mock_db_connection.execute_read.return_value = procedures
        
        # For admission query - should order by seq_num
        result = await list_procedures(
            mock_db_connection,
            admission_id="22595853",
            format=OUTPUT_FORMAT_JSON
        )
        
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "ORDER BY p.seq_num" in query
        
        # For patient query - should order by chartdate DESC, then seq_num
        result = await list_procedures(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_JSON
        )
        
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "ORDER BY p.chartdate DESC, p.seq_num" in query


@pytest.mark.integration
class TestListProceduresIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_list_real_procedures_by_patient(self, real_db_connection):
        """Test listing real procedures from the database."""
        result = await list_procedures(
            real_db_connection,
            patient_id="10461137",  # Adjust based on test data
            limit=5,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        
        # Basic assertions
        assert 'procedures' in data
        assert isinstance(data['procedures'], list)
        # count is only present when procedures are found
        if data['procedures']:
            assert 'count' in data
        
        # If procedures found, verify structure
        if data['procedures']:
            procedure = data['procedures'][0]
            assert 'icd_code' in procedure
            assert 'hadm_id' in procedure