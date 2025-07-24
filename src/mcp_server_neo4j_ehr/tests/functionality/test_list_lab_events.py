"""Tests for list lab events functionality."""

import json
import pytest

from ...modules.functionality.list_lab_events import list_lab_events
from ...modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


class TestListLabEventsFunctionality:
    """Test suite for list lab events functionality."""
    
    @pytest.mark.asyncio
    async def test_list_lab_events_basic(self, mock_db_connection, sample_lab_event):
        """Test basic lab event listing for a patient."""
        # Mock database response
        mock_db_connection.execute_read.return_value = [{
            'l': sample_lab_event.model_dump()
        }]
        
        # Call function
        result = await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Parse result
        data = json.loads(result)
        
        # Assertions
        assert 'lab_events' in data
        assert 'count' in data
        assert data['count'] == 1
        assert data['lab_events'][0]['label'] == "Sodium"
        assert data['lab_events'][0]['value'] == "130"
        assert data['lab_events'][0]['flag'] == "abnormal"
        
        # Verify query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "l.subject_id = $patient_id" in query
        assert "ORDER BY l.charttime DESC" in query
    
    @pytest.mark.asyncio
    async def test_list_lab_events_with_admission(self, mock_db_connection, sample_lab_event):
        """Test listing lab events for specific admission."""
        mock_db_connection.execute_read.return_value = [{
            'l': sample_lab_event.model_dump()
        }]
        
        # Call function
        result = await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            admission_id="22595853",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify both filters in query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "l.subject_id = $patient_id" in query
        assert "l.hadm_id = $admission_id" in query
    
    @pytest.mark.asyncio
    async def test_list_lab_events_abnormal_only(self, mock_db_connection, sample_lab_event):
        """Test filtering for abnormal lab results only."""
        mock_db_connection.execute_read.return_value = [{
            'l': sample_lab_event.model_dump()
        }]
        
        # Call function
        result = await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            abnormal_only=True,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify abnormal filter in query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "l.flag IS NOT NULL" in query
        assert "l.flag <> 'normal'" in query
    
    @pytest.mark.asyncio
    async def test_list_lab_events_by_category(self, mock_db_connection, sample_lab_event):
        """Test filtering by category."""
        mock_db_connection.execute_read.return_value = [{
            'l': sample_lab_event.model_dump()
        }]
        
        # Call function
        result = await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            category="CHEMISTRY",
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify category filter
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "toLower(l.category) = toLower($category)" in query
        
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['category'] == "CHEMISTRY"
    
    @pytest.mark.asyncio
    async def test_list_lab_events_empty_results(self, mock_db_connection):
        """Test handling of empty results."""
        mock_db_connection.execute_read.return_value = []
        
        result = await list_lab_events(
            mock_db_connection,
            patient_id="99999999",
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        assert data['lab_events'] == []
        assert data['message'] == "No lab events found"
    
    @pytest.mark.asyncio
    async def test_list_lab_events_table_format(self, mock_db_connection, sample_lab_event):
        """Test table format output."""
        mock_db_connection.execute_read.return_value = [{
            'l': sample_lab_event.model_dump()
        }]
        
        result = await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Assertions
        assert isinstance(result, str)
        assert "Test Name" in result
        assert "Value (Range)" in result
        assert "Sodium" in result
        assert "130 (136.0-145.0)" in result  # Value with reference range
        assert "abnormal" in result
        assert "CHEMISTRY" in result
    
    @pytest.mark.asyncio
    async def test_list_lab_events_table_format_no_ref_range(self, mock_db_connection):
        """Test table format when reference range is missing."""
        lab_event = {
            'lab_event_id': '123',
            'subject_id': '10000032',
            'hadm_id': '22595853',
            'charttime': '2124-08-08T06:00:00',
            'label': 'Custom Test',
            'value': 'Positive',
            'flag': 'normal',
            'category': 'OTHER',
            'ref_range_lower': None,
            'ref_range_upper': None
        }
        
        mock_db_connection.execute_read.return_value = [{'l': lab_event}]
        
        result = await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            format=OUTPUT_FORMAT_TABLE
        )
        
        # Should show value without range
        assert "Positive" in result
        assert "(--)" not in result  # No empty range shown
    
    @pytest.mark.asyncio
    async def test_list_lab_events_all_filters(self, mock_db_connection):
        """Test using all available filters together."""
        mock_db_connection.execute_read.return_value = []
        
        await list_lab_events(
            mock_db_connection,
            patient_id="10000032",
            admission_id="22595853",
            abnormal_only=True,
            category="CHEMISTRY",
            limit=10,
            format=OUTPUT_FORMAT_JSON
        )
        
        # Verify all conditions in query
        query = mock_db_connection.execute_read.call_args[0][0]
        assert "l.subject_id = $patient_id" in query
        assert "l.hadm_id = $admission_id" in query
        assert "l.flag IS NOT NULL" in query
        assert "l.flag <> 'normal'" in query
        assert "toLower(l.category) = toLower($category)" in query
        
        # Verify all parameters
        params = mock_db_connection.execute_read.call_args[0][1]
        assert params['patient_id'] == "10000032"
        assert params['admission_id'] == "22595853"
        assert params['category'] == "CHEMISTRY"
        assert params['limit'] == 10


@pytest.mark.integration
class TestListLabEventsIntegration:
    """Integration tests with real Neo4j database."""
    
    @pytest.mark.asyncio
    async def test_list_real_lab_events(self, real_db_connection):
        """Test listing real lab events from the database."""
        result = await list_lab_events(
            real_db_connection,
            patient_id="10461137",  # Adjust based on test data
            limit=5,
            format=OUTPUT_FORMAT_JSON
        )
        
        data = json.loads(result)
        
        # Basic assertions
        assert 'lab_events' in data
        assert 'count' in data
        assert isinstance(data['lab_events'], list)
        
        # If lab events found, verify structure
        if data['lab_events']:
            lab_event = data['lab_events'][0]
            assert 'label' in lab_event
            assert 'value' in lab_event
            assert 'charttime' in lab_event