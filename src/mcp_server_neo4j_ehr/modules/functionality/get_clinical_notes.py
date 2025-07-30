"""Get clinical notes functionality."""

import json
import logging
from typing import Optional, List
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import NoteSearchResult, OutputFormat, NoteType
from ..constants import (
    OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_TEXT,
    NOTE_TYPE_DISCHARGE, NOTE_TYPE_RADIOLOGY, NOTE_TYPE_ALL
)

logger = logging.getLogger(__name__)


async def get_clinical_notes(
    db: Neo4jConnection,
    note_type: NoteType = NOTE_TYPE_ALL,
    limit: int = 10,
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """Retrieve clinical notes by type and patient/admission."""
    
    # Build WHERE conditions
    where_conditions = []
    
    # Note type filter
    if note_type == NOTE_TYPE_DISCHARGE:
        where_conditions.append("note:DischargeNote")
    elif note_type == NOTE_TYPE_RADIOLOGY:
        where_conditions.append("note:RadiologyReport")
    else:
        where_conditions.append("(note:DischargeNote OR note:RadiologyReport)")
    
    # Patient filter
    if patient_id:
        where_conditions.append("note.subject_id = $patient_id")
    
    # Admission filter
    if admission_id:
        where_conditions.append("note.hadm_id = $admission_id")
    
    # Build query
    cypher_query = f"""
    MATCH (note)
    WHERE {' AND '.join(where_conditions) if where_conditions else 'true'}
    RETURN note.note_id as note_id,
           note.note_type as note_type,
           note.subject_id as subject_id,
           note.hadm_id as hadm_id,
           note.charttime as charttime,
           note.text as text
    ORDER BY note.charttime DESC
    LIMIT $limit
    """
    
    params = {
        "patient_id": patient_id,
        "admission_id": admission_id,
        "limit": limit
    }
    
    results = await db.execute_read(cypher_query, params)
    
    # Convert Neo4j DateTime objects to Python datetime
    converted_results = []
    for r in results:
        if 'charttime' in r and hasattr(r['charttime'], 'to_native'):
            r['charttime'] = r['charttime'].to_native()
        converted_results.append(NoteSearchResult(**r))
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_notes_as_table(converted_results)
    elif format == OUTPUT_FORMAT_TEXT:
        return format_notes_as_text(converted_results)
    else:
        return json.dumps([r.model_dump(exclude_none=True) for r in converted_results])


def format_notes_as_table(results: List[NoteSearchResult]) -> str:
    """Format notes as a table."""
    if not results:
        return "No notes found."
    
    table_data = []
    for note in results:
        table_data.append([
            note.note_id,
            note.note_type,
            note.subject_id or "N/A",
            note.hadm_id or "N/A",
            str(note.charttime) if note.charttime else "N/A",
            note.text[:100] + "..." if len(note.text) > 100 else note.text
        ])
    
    headers = ["Note ID", "Type", "Patient ID", "Admission ID", "Chart Time", "Text Preview"]
    return tabulate(table_data, headers=headers, tablefmt="grid")


def format_notes_as_text(results: List[NoteSearchResult]) -> str:
    """Format notes as plain text."""
    if not results:
        return "No notes found."
    
    output = []
    for i, note in enumerate(results, 1):
        output.append(f"\n{'='*80}")
        output.append(f"Note {i}/{len(results)} - ID: {note.note_id}")
        output.append(f"Type: {note.note_type}")
        output.append(f"Patient: {note.subject_id or 'N/A'}, Admission: {note.hadm_id or 'N/A'}")
        if note.charttime:
            output.append(f"Chart Time: {note.charttime}")
        output.append(f"\n{note.text}")
    
    return "\n".join(output)