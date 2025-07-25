"""Constants for the Neo4j EHR MCP Server."""

# Default values
DEFAULT_LIMIT = 20
DEFAULT_NOTE_SEARCH_LIMIT = 5
DEFAULT_NATURAL_QUERY_LIMIT = 10

# Output formats
OUTPUT_FORMAT_JSON = "json"
OUTPUT_FORMAT_TABLE = "table"
OUTPUT_FORMAT_TEXT = "text"
OUTPUT_FORMAT_MARKDOWN = "markdown"

# Note types
NOTE_TYPE_DISCHARGE = "discharge"
NOTE_TYPE_RADIOLOGY = "radiology"
NOTE_TYPE_ALL = "all"

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# Neo4j indexes
NOTE_EMBEDDINGS_INDEX = "note_embeddings"

# System prompts for natural language queries
NATURAL_QUERY_SYSTEM_PROMPT = """You are a Neo4j Cypher query expert specialized in medical/EHR data.
You will be given a complete database schema with all node properties and a natural language question.
Generate a valid Cypher query that answers the question. Only return the Cypher query, no explanations.

Important guidelines:
- Use appropriate WHERE clauses for filtering
- ALWAYS include LIMIT clauses to prevent large result sets
- Use indexed properties in WHERE clauses when possible for better performance
- Use proper node labels and relationship types from the schema
- Return meaningful data that directly answers the question
- For text searches in notes, use: WHERE toLower(n.text) CONTAINS toLower('search term')
- For date comparisons, use proper datetime() functions
- For finding abnormal lab results: WHERE l.flag IS NOT NULL AND l.flag <> 'normal'
- Prefer using unique identifiers (subject_id, hadm_id, note_id) when available
- Include relevant properties in RETURN statements to provide context

Example patterns:
- Patient data: MATCH (p:Patient {subject_id: '10000032'})
- Patient admissions: MATCH (p:Patient {subject_id: '10000032'})-[:HAS_ADMISSION]->(a:Admission)
- Admission diagnoses: MATCH (a:Admission {hadm_id: '12345'})-[:HAS_DIAGNOSIS]->(d:Diagnosis)
- Lab results: MATCH (l:LabEvent) WHERE l.subject_id = '10000032' AND l.flag = 'abnormal'
"""