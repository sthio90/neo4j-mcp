"""List procedures functionality."""

import json
from typing import Optional
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import Procedure, OutputFormat
from ..constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


async def list_procedures(
    db: Neo4jConnection,
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    limit: int = 20,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List procedures for a patient or admission."""
    
    # Build query based on filters
    if admission_id:
        query = """
        MATCH (a:Admission {hadm_id: $admission_id})-[:HAS_PROCEDURE]->(p:Procedure)
        RETURN p
        ORDER BY p.seq_num
        LIMIT $limit
        """
        params = {"admission_id": admission_id, "limit": limit}
    elif patient_id:
        query = """
        MATCH (pat:Patient {subject_id: $patient_id})-[:HAS_ADMISSION]->(a:Admission)-[:HAS_PROCEDURE]->(p:Procedure)
        RETURN p, a.hadm_id as hadm_id
        ORDER BY p.chartdate DESC, p.seq_num
        LIMIT $limit
        """
        params = {"patient_id": patient_id, "limit": limit}
    else:
        return json.dumps({"error": "Either patient_id or admission_id must be provided"})
    
    results = await db.execute_read(query, params)
    
    if not results:
        return json.dumps({"procedures": [], "message": "No procedures found"})
    
    # Process results
    procedures = []
    for result in results:
        procedure_data = result['p']
        procedure = Procedure(**procedure_data)
        
        # Add admission ID if querying by patient
        if patient_id and 'hadm_id' in result:
            procedure.hadm_id = result['hadm_id']
        
        procedures.append(procedure)
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_procedures_as_table(procedures)
    else:
        return json.dumps({
            "procedures": [p.model_dump(exclude_none=True) for p in procedures],
            "count": len(procedures)
        })


def format_procedures_as_table(procedures: list[Procedure]) -> str:
    """Format procedures as a table."""
    if not procedures:
        return "No procedures found."
    
    table_data = []
    for proc in procedures:
        table_data.append([
            proc.icd_code,
            proc.long_title or "N/A",
            proc.hadm_id or "N/A",
            str(proc.chartdate) if proc.chartdate else "N/A",
            proc.seq_num or "N/A",
            f"ICD-{proc.icd_version}" if proc.icd_version else "N/A"
        ])
    
    headers = ["ICD Code", "Description", "Admission ID", "Chart Date", "Sequence", "Version"]
    return tabulate(table_data, headers=headers, tablefmt="grid")