## Fix issue with natural query function
Neo4j return DateTime objects that cant be directly serialized to JSON.

Given fix from copilot:
import json
from datetime import datetime
from neo4j.time import DateTime

// ...existing code...

def serialize_neo4j_data(obj):
    """Convert Neo4j objects to JSON-serializable format."""
    if isinstance(obj, DateTime):
        # Convert Neo4j DateTime to ISO format string
        return obj.iso_format()
    elif isinstance(obj, datetime):
        # Convert Python datetime to ISO format string
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_neo4j_data(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_neo4j_data(item) for item in obj]
    else:
        return obj

// ...existing code...

async def natural_query(
    db_connection: Neo4jConnection,
    query: str,
    limit: int,
    format: OutputFormat,
    openai_api_key: str
) -> str:
    // ...existing code until the results processing...
    
    if format == OUTPUT_FORMAT_JSON:
        # Serialize the results to handle DateTime objects
        serialized_results = serialize_neo4j_data(results)
        return json.dumps({"results": serialized_results}, indent=2)
    elif format == OUTPUT_FORMAT_MARKDOWN:
        # Process results for markdown (likely already handling this correctly)
        // ...existing markdown processing...
    else:
        # Handle other formats


This issue likely affects other functions too, so you should apply the same fix to any other tools that return JSON with datetime fields (like patient.py, list_*.py functions, etc.).