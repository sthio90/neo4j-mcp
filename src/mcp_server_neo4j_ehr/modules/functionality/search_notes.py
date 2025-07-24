"""Search notes functionality with semantic search support."""

import json
import logging
from typing import Optional, List
from openai import OpenAI
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import NoteSearchResult, OutputFormat, NoteType
from ..constants import (
    OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_TEXT,
    NOTE_TYPE_DISCHARGE, NOTE_TYPE_RADIOLOGY, NOTE_TYPE_ALL,
    EMBEDDING_MODEL, NOTE_EMBEDDINGS_INDEX
)

logger = logging.getLogger(__name__)


async def search_notes(
    db: Neo4jConnection,
    query: str,
    note_type: NoteType = NOTE_TYPE_ALL,
    limit: int = 5,
    semantic: bool = False,
    patient_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    format: OutputFormat = OUTPUT_FORMAT_JSON,
    openai_api_key: Optional[str] = None
) -> str:
    """Search through clinical notes."""
    
    if semantic and not openai_api_key:
        return json.dumps({"error": "OpenAI API key is required for semantic search"})
    
    if semantic:
        # Perform semantic search
        results = await semantic_search(
            db, query, note_type, limit, patient_id, admission_id, openai_api_key
        )
    else:
        # Perform text search
        results = await text_search(
            db, query, note_type, limit, patient_id, admission_id
        )
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_notes_as_table(results)
    elif format == OUTPUT_FORMAT_TEXT:
        return format_notes_as_text(results)
    else:
        return json.dumps([r.model_dump(exclude_none=True) for r in results])


async def text_search(
    db: Neo4jConnection,
    query: str,
    note_type: NoteType,
    limit: int,
    patient_id: Optional[str],
    admission_id: Optional[str]
) -> List[NoteSearchResult]:
    """Perform text-based search on notes."""
    
    # Build WHERE conditions
    where_conditions = []
    
    # Note type filter
    if note_type == NOTE_TYPE_DISCHARGE:
        where_conditions.append("note:DischargeNote")
    elif note_type == NOTE_TYPE_RADIOLOGY:
        where_conditions.append("note:RadiologyReport")
    else:
        where_conditions.append("(note:DischargeNote OR note:RadiologyReport)")
    
    # Text search
    if query:
        where_conditions.append("toLower(note.text) CONTAINS toLower($query)")
    
    # Patient filter
    if patient_id:
        where_conditions.append("note.subject_id = $patient_id")
    
    # Admission filter
    if admission_id:
        where_conditions.append("note.hadm_id = $admission_id")
    
    # Build query
    cypher_query = f"""
    MATCH (note)
    WHERE {' AND '.join(where_conditions)}
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
        "query": query,
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
    return converted_results


async def semantic_search(
    db: Neo4jConnection,
    query: str,
    note_type: NoteType,
    limit: int,
    patient_id: Optional[str],
    admission_id: Optional[str],
    openai_api_key: str
) -> List[NoteSearchResult]:
    """Perform semantic search using embeddings."""
    
    # Generate embedding for query
    client = OpenAI(api_key=openai_api_key)
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        query_embedding = response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []
    
    # Build WHERE conditions
    where_conditions = []
    
    if note_type == NOTE_TYPE_DISCHARGE:
        where_conditions.append("node:DischargeNote")
    elif note_type == NOTE_TYPE_RADIOLOGY:
        where_conditions.append("node:RadiologyReport")
    else:
        where_conditions.append("(node:DischargeNote OR node:RadiologyReport)")
    
    if patient_id:
        where_conditions.append("node.subject_id = $patient_id")
    
    if admission_id:
        where_conditions.append("node.hadm_id = $admission_id")
    
    # Vector search query
    cypher_query = f"""
    CALL db.index.vector.queryNodes($index_name, $limit, $query_embedding) 
    YIELD node, score
    WHERE {' AND '.join(where_conditions) if where_conditions else 'true'}
    RETURN node.note_id as note_id,
           node.note_type as note_type,
           node.subject_id as subject_id,
           node.hadm_id as hadm_id,
           node.charttime as charttime,
           node.text as text,
           score
    """
    
    params = {
        "index_name": NOTE_EMBEDDINGS_INDEX,
        "limit": limit * 2,  # Get more results to filter
        "query_embedding": query_embedding,
        "patient_id": patient_id,
        "admission_id": admission_id
    }
    
    results = await db.execute_read(cypher_query, params)
    
    # Limit results after filtering
    results = results[:limit]
    
    # Convert Neo4j DateTime objects to Python datetime
    converted_results = []
    for r in results:
        if 'charttime' in r and hasattr(r['charttime'], 'to_native'):
            r['charttime'] = r['charttime'].to_native()
        converted_results.append(NoteSearchResult(**r))
    return converted_results


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
            note.text[:100] + "..." if len(note.text) > 100 else note.text,
            f"{note.score:.3f}" if note.score else "N/A"
        ])
    
    headers = ["Note ID", "Type", "Patient ID", "Admission ID", "Chart Time", "Text Preview", "Score"]
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
        if note.score:
            output.append(f"Relevance Score: {note.score:.3f}")
        output.append(f"\n{note.text}")
    
    return "\n".join(output)