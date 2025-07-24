"""List diagnoses functionality."""

import json
from typing import Optional
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import Diagnosis, OutputFormat
from ..constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


async def list_diagnoses(
    db: Neo4jConnection,
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    limit: int = 20,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List diagnoses for a patient or admission."""
    
    # Build query based on filters
    if admission_id:
        query = """
        MATCH (a:Admission {hadm_id: $admission_id})-[:HAS_DIAGNOSIS]->(d:Diagnosis)
        RETURN d
        ORDER BY d.seq_num
        LIMIT $limit
        """
        params = {"admission_id": admission_id, "limit": limit}
    elif patient_id:
        query = """
        MATCH (p:Patient {subject_id: $patient_id})-[:HAS_ADMISSION]->(a:Admission)-[:HAS_DIAGNOSIS]->(d:Diagnosis)
        RETURN d, a.hadm_id as hadm_id
        ORDER BY a.admittime DESC, d.seq_num
        LIMIT $limit
        """
        params = {"patient_id": patient_id, "limit": limit}
    else:
        return json.dumps({"error": "Either patient_id or admission_id must be provided"})
    
    results = await db.execute_read(query, params)
    
    if not results:
        return json.dumps({"diagnoses": [], "message": "No diagnoses found"})
    
    # Process results
    diagnoses = []
    for result in results:
        diagnosis_data = result['d']
        diagnosis = Diagnosis(**diagnosis_data)
        
        # Add admission ID if querying by patient
        if patient_id and 'hadm_id' in result:
            diagnosis.hadm_id = result['hadm_id']
        
        diagnoses.append(diagnosis)
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_diagnoses_as_table(diagnoses)
    else:
        return json.dumps({
            "diagnoses": [d.model_dump(exclude_none=True) for d in diagnoses],
            "count": len(diagnoses)
        })


def format_diagnoses_as_table(diagnoses: list[Diagnosis]) -> str:
    """Format diagnoses as a table."""
    if not diagnoses:
        return "No diagnoses found."
    
    table_data = []
    for diag in diagnoses:
        table_data.append([
            diag.icd_code,
            diag.long_title or "N/A",
            diag.hadm_id or "N/A",
            diag.seq_num or "N/A",
            f"ICD-{diag.icd_version}" if diag.icd_version else "N/A"
        ])
    
    headers = ["ICD Code", "Description", "Admission ID", "Sequence", "Version"]
    return tabulate(table_data, headers=headers, tablefmt="grid")