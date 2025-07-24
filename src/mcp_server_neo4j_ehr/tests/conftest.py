"""Shared test fixtures and configuration."""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from dotenv import load_dotenv

from ..modules.db_connection import Neo4jConnection, create_neo4j_driver
from ..modules.data_types import (
    Patient, Admission, Diagnosis, Procedure, 
    Medication, LabEvent, DischargeNote, RadiologyReport
)

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_connection():
    """Create a mock database connection for unit tests."""
    mock_connection = AsyncMock(spec=Neo4jConnection)
    return mock_connection


@pytest.fixture
async def real_db_connection():
    """Create a real database connection for integration tests."""
    # Use test database credentials from environment
    uri = os.getenv("NEO4J_TEST_URI", os.getenv("NEO4J_URI"))
    username = os.getenv("NEO4J_TEST_USERNAME", os.getenv("NEO4J_USERNAME"))
    password = os.getenv("NEO4J_TEST_PASSWORD", os.getenv("NEO4J_PASSWORD"))
    database = os.getenv("NEO4J_TEST_DATABASE", os.getenv("NEO4J_DATABASE"))
    
    if not all([uri, username, password]):
        pytest.skip("Neo4j credentials not configured for integration tests")
    
    driver = create_neo4j_driver(uri, username, password)
    connection = Neo4jConnection(driver, database)
    
    # Test the connection
    if not await connection.test_connection():
        pytest.skip("Cannot connect to Neo4j database")
    
    yield connection
    await driver.close()


@pytest.fixture
def sample_patient():
    """Sample patient data for testing."""
    return Patient(
        subject_id="10000032",
        gender="M",
        anchor_age=52,
        anchor_year=2126,
        anchor_year_group="2020 - 2025"
    )


@pytest.fixture
def sample_admission():
    """Sample admission data for testing."""
    from datetime import datetime
    return Admission(
        hadm_id="22595853",
        admission_type="URGENT",
        admittime=datetime.fromisoformat("2124-08-07T15:45:00"),
        dischtime=datetime.fromisoformat("2124-08-10T16:00:00"),
        admission_location="EMERGENCY ROOM",
        discharge_location="HOME",
        insurance="Medicare",
        language="ENGLISH",
        marital_status="MARRIED",
        race="WHITE"
    )


@pytest.fixture
def sample_diagnosis():
    """Sample diagnosis data for testing."""
    return Diagnosis(
        icd_code="I50.9",
        long_title="Heart failure, unspecified",
        hadm_id="22595853",
        subject_id="10000032",
        seq_num=1,
        icd_version=10
    )


@pytest.fixture
def sample_lab_event():
    """Sample lab event data for testing."""
    from datetime import datetime
    return LabEvent(
        lab_event_id="1234567",
        subject_id="10000032",
        hadm_id="22595853",
        charttime=datetime.fromisoformat("2124-08-08T06:00:00"),
        label="Sodium",
        itemid="50983",
        category="CHEMISTRY",
        flag="abnormal",
        value="130",
        ref_range_lower=136.0,
        ref_range_upper=145.0
    )


@pytest.fixture
def sample_medication():
    """Sample medication data for testing."""
    return Medication(
        medication="Furosemide",
        route="PO",
        hadm_id="22595853",
        subject_id="10000032",
        frequency="BID"
    )


@pytest.fixture
def sample_procedure():
    """Sample procedure data for testing."""
    from datetime import datetime
    return Procedure(
        icd_code="99.04",
        long_title="Transfusion of packed cells",
        hadm_id="22595853",
        seq_num=1,
        chartdate=datetime.fromisoformat("2124-08-08"),
        icd_version=9
    )


@pytest.fixture
def sample_discharge_note():
    """Sample discharge note for testing."""
    from datetime import datetime
    return DischargeNote(
        note_id="note_001",
        hadm_id="22595853",
        subject_id="10000032",
        note_type="Discharge summary",
        text="Patient admitted with acute heart failure exacerbation. Treated with IV diuretics.",
        charttime=datetime.fromisoformat("2124-08-10T14:00:00")
    )


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    mock = MagicMock()
    # Mock the client itself to avoid initialization issues
    mock.embeddings = MagicMock()
    mock.embeddings.create = MagicMock(return_value=MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    ))
    mock.chat = MagicMock()
    mock.chat.completions = MagicMock()
    mock.chat.completions.create = MagicMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"tool": "test_tool", "arguments": {}}'))]
    ))
    return mock