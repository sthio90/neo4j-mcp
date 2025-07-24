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
NATURAL_QUERY_SYSTEM_PROMPT = """You are a Neo4j Cypher query expert specialized in medical data.
You will be given a database schema and a natural language question about medical/EHR data.
Generate a valid Cypher query that answers the question. Only return the Cypher query, no explanations.

Important guidelines:
- Use appropriate WHERE clauses for filtering
- Include LIMIT clauses to prevent large result sets
- Use proper node labels and relationship types from the schema
- Return meaningful data that answers the question
- For text searches in notes, use case-insensitive CONTAINS
"""