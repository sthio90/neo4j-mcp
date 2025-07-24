"""List lab events functionality."""

import json
from typing import Optional
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import LabEvent, OutputFormat
from ..constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


async def list_lab_events(
    db: Neo4jConnection,
    patient_id: str,
    admission_id: Optional[str] = None,
    abnormal_only: bool = False,
    category: Optional[str] = None,
    limit: int = 20,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """List lab events for a patient."""
    
    # Build WHERE conditions
    where_conditions = ["l.subject_id = $patient_id"]
    
    if admission_id:
        where_conditions.append("l.hadm_id = $admission_id")
    
    if abnormal_only:
        where_conditions.append("l.flag IS NOT NULL AND l.flag <> 'normal'")
    
    if category:
        where_conditions.append("toLower(l.category) = toLower($category)")
    
    # Build query
    query = f"""
    MATCH (l:LabEvent)
    WHERE {' AND '.join(where_conditions)}
    RETURN l
    ORDER BY l.charttime DESC
    LIMIT $limit
    """
    
    params = {
        "patient_id": patient_id,
        "admission_id": admission_id,
        "category": category,
        "limit": limit
    }
    
    results = await db.execute_read(query, params)
    
    if not results:
        return json.dumps({"lab_events": [], "message": "No lab events found"})
    
    # Process results - convert Neo4j DateTime objects to Python datetime
    lab_events = []
    for result in results:
        r = result['l']
        # Convert Neo4j DateTime to Python datetime for datetime fields
        if 'charttime' in r and hasattr(r['charttime'], 'to_native'):
            r['charttime'] = r['charttime'].to_native()
        if 'storetime' in r and hasattr(r['storetime'], 'to_native'):
            r['storetime'] = r['storetime'].to_native()
        lab_events.append(LabEvent(**r))
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_lab_events_as_table(lab_events)
    else:
        return json.dumps({
            "lab_events": [l.model_dump(exclude_none=True) for l in lab_events],
            "count": len(lab_events)
        })


def format_lab_events_as_table(lab_events: list[LabEvent]) -> str:
    """Format lab events as a table."""
    if not lab_events:
        return "No lab events found."
    
    table_data = []
    for lab in lab_events:
        # Format value with reference range
        value_str = str(lab.value) if lab.value else "N/A"
        if lab.ref_range_lower is not None or lab.ref_range_upper is not None:
            ref_range = f"({lab.ref_range_lower or ''}-{lab.ref_range_upper or ''})"
            value_str = f"{value_str} {ref_range}"
        
        table_data.append([
            lab.label,
            value_str,
            lab.flag or "normal",
            lab.category or "N/A",
            str(lab.charttime) if lab.charttime else "N/A",
            lab.hadm_id or "N/A"
        ])
    
    headers = ["Test Name", "Value (Range)", "Flag", "Category", "Chart Time", "Admission ID"]
    return tabulate(table_data, headers=headers, tablefmt="grid")