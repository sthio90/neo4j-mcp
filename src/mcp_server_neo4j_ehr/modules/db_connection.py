"""Database connection management for Neo4j."""

import logging
from typing import Optional, Dict, Any, List
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncResult
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connections and queries."""
    
    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        self.driver = driver
        self.database = database
    
    async def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read query and return results as a list of dictionaries."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(
                    self._run_query, query, parameters or {}
                )
                return result
        except Neo4jError as e:
            logger.error(f"Neo4j read error: {e}")
            raise
    
    async def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a write query and return results as a list of dictionaries."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    self._run_query, query, parameters or {}
                )
                return result
        except Neo4jError as e:
            logger.error(f"Neo4j write error: {e}")
            raise
    
    @staticmethod
    async def _run_query(tx, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run a query within a transaction."""
        result = await tx.run(query, parameters)
        records = await result.data()
        return records
    
    async def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            await self.execute_read("RETURN 1 as test")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get the database schema information - hardcoded for EHR data."""
        schema = {
            "nodes": [
                {
                    "label": "Patient",
                    "properties": [
                        "subject_id",  # unique, indexed
                        "gender",      # indexed
                        "anchor_age",
                        "anchor_year",
                        "anchor_year_group",
                        "dod"         # date of death
                    ],
                    "property_types": {
                        "subject_id": "string (unique, indexed)",
                        "gender": "string (indexed)",
                        "anchor_age": "integer",
                        "anchor_year": "integer", 
                        "anchor_year_group": "string",
                        "dod": "datetime"
                    }
                },
                {
                    "label": "Admission",
                    "properties": [
                        "hadm_id",            # unique, indexed
                        "admission_type",     # indexed
                        "admittime",
                        "dischtime",
                        "deathtime",
                        "admission_location",
                        "discharge_location",
                        "insurance",
                        "language",
                        "marital_status",
                        "race",
                        "edregtime",
                        "edouttime",
                        "hospital_expire_flag",
                        "admit_provider_id"
                    ],
                    "property_types": {
                        "hadm_id": "string (unique, indexed)",
                        "admission_type": "string (indexed)",
                        "admittime": "datetime",
                        "dischtime": "datetime",
                        "deathtime": "datetime",
                        "admission_location": "string",
                        "discharge_location": "string",
                        "insurance": "string",
                        "language": "string",
                        "marital_status": "string",
                        "race": "string",
                        "edregtime": "datetime",
                        "edouttime": "datetime",
                        "hospital_expire_flag": "integer",
                        "admit_provider_id": "string"
                    }
                },
                {
                    "label": "DischargeNote",
                    "properties": [
                        "note_id",       # unique, indexed
                        "hadm_id",       # indexed
                        "subject_id",    # indexed
                        "note_type",     # indexed
                        "text",          # indexed
                        "note_seq",
                        "charttime",
                        "storetime",
                        "embedding",
                        "embedding_model",
                        "embedding_created"
                    ],
                    "property_types": {
                        "note_id": "string (unique, indexed)",
                        "hadm_id": "string (indexed)",
                        "subject_id": "string (indexed)",
                        "note_type": "string (indexed)",
                        "text": "string (indexed)",
                        "note_seq": "integer",
                        "charttime": "datetime",
                        "storetime": "datetime",
                        "embedding": "float[]",
                        "embedding_model": "string",
                        "embedding_created": "datetime"
                    }
                },
                {
                    "label": "RadiologyReport",
                    "properties": [
                        "note_id",       # unique, indexed
                        "hadm_id",       # indexed
                        "subject_id",    # indexed
                        "note_type",     # indexed
                        "text",          # indexed
                        "note_seq",
                        "charttime",
                        "storetime",
                        "embedding",
                        "embedding_model",
                        "embedding_created"
                    ],
                    "property_types": {
                        "note_id": "string (unique, indexed)",
                        "hadm_id": "string (indexed)",
                        "subject_id": "string (indexed)",
                        "note_type": "string (indexed)",
                        "text": "string (indexed)",
                        "note_seq": "integer",
                        "charttime": "datetime",
                        "storetime": "datetime",
                        "embedding": "float[]",
                        "embedding_model": "string",
                        "embedding_created": "datetime"
                    }
                },
                {
                    "label": "LabEvent",
                    "properties": [
                        "lab_event_id",    # unique, indexed
                        "subject_id",      # indexed
                        "hadm_id",         # indexed
                        "charttime",       # indexed
                        "label",           # indexed
                        "itemid",          # indexed
                        "category",        # indexed
                        "flag",            # indexed
                        "value",           # indexed
                        "comments",        # indexed
                        "ref_range_upper",
                        "ref_range_lower",
                        "fluid",
                        "priority",
                        "storetime"
                    ],
                    "property_types": {
                        "lab_event_id": "string (unique, indexed)",
                        "subject_id": "string (indexed)",
                        "hadm_id": "string (indexed)",
                        "charttime": "datetime (indexed)",
                        "label": "string (indexed)",
                        "itemid": "string (indexed)",
                        "category": "string (indexed)",
                        "flag": "string (indexed)",
                        "value": "string (indexed)",
                        "comments": "string (indexed)",
                        "ref_range_upper": "float",
                        "ref_range_lower": "float",
                        "fluid": "string",
                        "priority": "string",
                        "storetime": "datetime"
                    }
                },
                {
                    "label": "Medication",
                    "properties": [
                        "medication",    # indexed
                        "route",         # indexed
                        "hadm_id",
                        "subject_id",
                        "frequency",
                        "verifiedtime"
                    ],
                    "property_types": {
                        "medication": "string (indexed)",
                        "route": "string (indexed)",
                        "hadm_id": "string",
                        "subject_id": "string",
                        "frequency": "string",
                        "verifiedtime": "datetime"
                    }
                },
                {
                    "label": "Diagnosis",
                    "properties": [
                        "icd_code",      # indexed
                        "long_title",    # indexed
                        "synonyms",      # indexed
                        "hadm_id",
                        "subject_id",
                        "seq_num",
                        "icd_version"
                    ],
                    "property_types": {
                        "icd_code": "string (indexed)",
                        "long_title": "string (indexed)",
                        "synonyms": "string[] (indexed)",
                        "hadm_id": "string",
                        "subject_id": "string",
                        "seq_num": "integer",
                        "icd_version": "integer"
                    }
                },
                {
                    "label": "Procedure",
                    "properties": [
                        "icd_code",      # indexed
                        "long_title",    # indexed
                        "hadm_id",
                        "seq_num",
                        "chartdate",
                        "icd_version"
                    ],
                    "property_types": {
                        "icd_code": "string (indexed)",
                        "long_title": "string (indexed)",
                        "hadm_id": "string",
                        "seq_num": "integer",
                        "chartdate": "datetime",
                        "icd_version": "integer"
                    }
                }
            ],
            "relationships": [
                {"relationshipType": "HAS_ADMISSION"},
                {"relationshipType": "INCLUDES_DISCHARGE_NOTE"},
                {"relationshipType": "INCLUDES_RADIOLOGY_REPORT"},
                {"relationshipType": "INCLUDES_LAB_EVENT"},
                {"relationshipType": "HAS_DIAGNOSIS"},
                {"relationshipType": "HAS_PROCEDURE"},
                {"relationshipType": "HAS_MEDICATION"}
            ],
            "constraints": [],  # Will be populated if needed
            "indexes": []       # Will be populated if needed
        }
        
        return schema
    
    async def close(self):
        """Close the database connection."""
        if self.driver:
            await self.driver.close()


def create_neo4j_driver(uri: str, username: str, password: str) -> AsyncDriver:
    """Create a Neo4j async driver instance."""
    return AsyncGraphDatabase.driver(uri, auth=(username, password))