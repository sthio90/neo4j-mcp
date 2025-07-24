"""List medications functionality."""

import json
from typing import Optional
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import Medication, OutputFormat
from ..constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


async def list_medications(
    db: Neo4jConnection,
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    medication: Optional[str] = None,
    route: Optional[str] = None,
    limit: int = 20,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List medications for a patient or admission."""
    
    # Build query based on filters
    where_conditions = []
    
    if admission_id:
        where_conditions.append("m.hadm_id = $admission_id")
    elif patient_id:
        where_conditions.append("m.subject_id = $patient_id")
    else:
        return json.dumps({"error": "Either patient_id or admission_id must be provided"})
    
    if medication:
        where_conditions.append("toLower(m.medication) CONTAINS toLower($medication)")
    
    if route:
        where_conditions.append("toLower(m.route) = toLower($route)")
    
    # Build query
    query = f"""
    MATCH (m:Medication)
    WHERE {' AND '.join(where_conditions)}
    RETURN m
    ORDER BY m.verifiedtime DESC
    LIMIT $limit
    """
    
    params = {
        "patient_id": patient_id,
        "admission_id": admission_id,
        "medication": medication,
        "route": route,
        "limit": limit
    }
    
    results = await db.execute_read(query, params)
    
    if not results:
        return json.dumps({"medications": [], "message": "No medications found"})
    
    # Process results - convert Neo4j DateTime objects to Python datetime
    medications = []
    for result in results:
        r = result['m']
        # Convert Neo4j DateTime to Python datetime for datetime fields
        if 'verifiedtime' in r and hasattr(r['verifiedtime'], 'to_native'):
            r['verifiedtime'] = r['verifiedtime'].to_native()
        medications.append(Medication(**r))
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_medications_as_table(medications)
    else:
        return json.dumps({
            "medications": [m.model_dump(exclude_none=True) for m in medications],
            "count": len(medications)
        })


def format_medications_as_table(medications: list[Medication]) -> str:
    """Format medications as a table."""
    if not medications:
        return "No medications found."
    
    table_data = []
    for med in medications:
        table_data.append([
            med.medication,
            med.route or "N/A",
            med.frequency or "N/A",
            med.hadm_id or "N/A",
            str(med.verifiedtime) if med.verifiedtime else "N/A"
        ])
    
    headers = ["Medication", "Route", "Frequency", "Admission ID", "Verified Time"]
    return tabulate(table_data, headers=headers, tablefmt="grid")