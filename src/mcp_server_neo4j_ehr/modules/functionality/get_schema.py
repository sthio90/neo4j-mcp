"""Get database schema functionality."""

import json
from datetime import datetime
from typing import Dict, Any

from ..db_connection import Neo4jConnection
from ..data_types import OutputFormat
from ..constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_MARKDOWN


def convert_neo4j_types(obj):
    """Convert Neo4j types to JSON-serializable types."""
    if isinstance(obj, dict):
        return {k: convert_neo4j_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_neo4j_types(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # Handles neo4j.time.DateTime and python datetime
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):  # Handle Neo4j objects
        return convert_neo4j_types(obj.__dict__)
    return obj


async def get_schema(
    db: Neo4jConnection,
    format: OutputFormat = OUTPUT_FORMAT_MARKDOWN
) -> str:
    """Get the database schema."""
    
    # Get schema from database
    schema = await db.get_schema()
    
    # Add our known relationship structure
    schema["known_relationships"] = [
        {
            "from": "Patient",
            "to": "Admission",
            "type": "HAS_ADMISSION",
            "description": "Patient has hospital admissions"
        },
        {
            "from": "Admission",
            "to": "DischargeNote",
            "type": "INCLUDES_DISCHARGE_NOTE",
            "description": "Admission includes discharge summary notes"
        },
        {
            "from": "Admission",
            "to": "RadiologyReport",
            "type": "INCLUDES_RADIOLOGY_REPORT",
            "description": "Admission includes radiology reports"
        },
        {
            "from": "Admission",
            "to": "LabEvent",
            "type": "INCLUDES_LAB_EVENT",
            "description": "Admission includes laboratory test results"
        },
        {
            "from": "Admission",
            "to": "Diagnosis",
            "type": "HAS_DIAGNOSIS",
            "description": "Admission has associated diagnoses"
        },
        {
            "from": "Admission",
            "to": "Procedure",
            "type": "HAS_PROCEDURE",
            "description": "Admission has associated procedures"
        },
        {
            "from": "Admission",
            "to": "Medication",
            "type": "HAS_MEDICATION",
            "description": "Admission has associated medications"
        }
    ]
    
    # Format output
    if format == OUTPUT_FORMAT_MARKDOWN:
        return format_schema_as_markdown(schema)
    else:
        # Convert Neo4j types to JSON-serializable types
        schema_serializable = convert_neo4j_types(schema)
        return json.dumps(schema_serializable, indent=2)


def format_schema_as_markdown(schema: Dict[str, Any]) -> str:
    """Format schema as markdown."""
    lines = []
    
    lines.append("# Neo4j EHR Database Schema\n")
    
    # Node types
    lines.append("## Node Types\n")
    for node in schema.get("nodes", []):
        label = node.get("label", "Unknown")
        properties = node.get("properties", [])
        lines.append(f"### {label}")
        lines.append(f"**Properties:** {', '.join(properties)}\n")
    
    # Relationships
    lines.append("## Relationships\n")
    for rel in schema.get("known_relationships", []):
        lines.append(f"### {rel['type']}")
        lines.append(f"- **From:** {rel['from']}")
        lines.append(f"- **To:** {rel['to']}")
        lines.append(f"- **Description:** {rel['description']}\n")
    
    # Indexes
    if schema.get("indexes"):
        lines.append("## Indexes\n")
        for idx in schema["indexes"]:
            name = idx.get("name", "Unknown")
            state = idx.get("state", "Unknown")
            lines.append(f"- {name} (State: {state})")
    
    # Constraints
    if schema.get("constraints"):
        lines.append("\n## Constraints\n")
        for constraint in schema["constraints"]:
            name = constraint.get("name", "Unknown")
            lines.append(f"- {name}")
    
    # Usage examples
    lines.append("\n## Example Queries\n")
    lines.append("### Get patient with all admissions")
    lines.append("```cypher")
    lines.append("MATCH (p:Patient {subject_id: '10000032'})-[:HAS_ADMISSION]->(a:Admission)")
    lines.append("RETURN p, collect(a) as admissions")
    lines.append("```\n")
    
    lines.append("### Find discharge notes mentioning a condition")
    lines.append("```cypher")
    lines.append("MATCH (d:DischargeNote)")
    lines.append("WHERE toLower(d.text) CONTAINS 'heart failure'")
    lines.append("RETURN d.note_id, d.subject_id, d.hadm_id")
    lines.append("LIMIT 10")
    lines.append("```\n")
    
    lines.append("### Get abnormal lab results for a patient")
    lines.append("```cypher")
    lines.append("MATCH (l:LabEvent)")
    lines.append("WHERE l.subject_id = '10000032' AND l.flag IS NOT NULL AND l.flag <> 'normal'")
    lines.append("RETURN l.label, l.value, l.flag, l.charttime")
    lines.append("ORDER BY l.charttime DESC")
    lines.append("```")
    
    return "\n".join(lines)