# Neo4j server to connect to EHR graphRAG 

With this Model Context Protocol (MCP) server we can now query our Neo4j database in natural language. This specific server is to query a medical electronic health record (EHR) database that uses data from the MIMI-IV EHR datatbase (discharge notes, radiology reports, patient admission structured data).


## NEO4j Database Structure

### Node Types

#### Patient (10 nodes)
- **Properties**: `subject_id` (unique, indexed), `gender` (indexed), `anchor_age`, `anchor_year`, `anchor_year_group`, `dod`
- **Relationships**: HAS_ADMISSION → Admission

#### Admission (28 nodes)  
- **Properties**: `hadm_id` (unique, indexed), `admission_type` (indexed), `admittime`, `dischtime`, `deathtime`, `admission_location`, `discharge_location`, `insurance`, `language`, `marital_status`, `race`, `edregtime`, `edouttime`, `hospital_expire_flag`, `admit_provider_id`
- **Relationships**: 
  - ← HAS_ADMISSION from Patient
  - INCLUDES_DISCHARGE_NOTE → DischargeNote
  - INCLUDES_RADIOLOGY_REPORT → RadiologyReport  
  - INCLUDES_LAB_EVENT → LabEvent
  - HAS_PROCEDURE → Procedure
  - HAS_MEDICATION → Medication
  - HAS_DIAGNOSIS → Diagnosis

#### DischargeNote (25 nodes)
- **Properties**: `note_id` (unique, indexed), `hadm_id` (indexed), `subject_id` (indexed), `note_type` (indexed), `text` (indexed), `note_seq`, `charttime`, `storetime`, `embedding`, `embedding_model`, `embedding_created`
- **Relationships**: ← INCLUDES_DISCHARGE_NOTE from Admission

#### RadiologyReport (64 nodes)
- **Properties**: `note_id` (unique, indexed), `hadm_id` (indexed), `subject_id` (indexed), `note_type` (indexed), `text` (indexed), `note_seq`, `charttime`, `storetime`, `embedding`, `embedding_model`, `embedding_created`  
- **Relationships**: ← INCLUDES_RADIOLOGY_REPORT from Admission

#### LabEvent (4,346 nodes)
- **Properties**: `lab_event_id` (unique, indexed), `subject_id` (indexed), `hadm_id` (indexed), `charttime` (indexed), `label` (indexed), `itemid` (indexed), `category` (indexed), `flag` (indexed), `value` (indexed), `comments` (indexed), `ref_range_upper`, `ref_range_lower`, `fluid`, `priority`, `storetime`
- **Relationships**: ← INCLUDES_LAB_EVENT from Admission

#### Medication (1,051 nodes)
- **Properties**: `medication` (indexed), `route` (indexed), `hadm_id`, `subject_id`, `frequency`, `verifiedtime`
- **Relationships**: ← HAS_MEDICATION from Admission

#### Diagnosis (420 nodes)
- **Properties**: `icd_code` (indexed), `long_title` (indexed), `synonyms` (indexed), `hadm_id`, `subject_id`, `seq_num`, `icd_version`
- **Relationships**: ← HAS_DIAGNOSIS from Admission

#### Procedure (29 nodes)
- **Properties**: `icd_code` (indexed), `long_title` (indexed), `hadm_id`, `seq_num`, `chartdate`, `icd_version`
- **Relationships**: ← HAS_PROCEDURE from Admission

### Key Features
- **Vector Embeddings**: DischargeNote and RadiologyReport nodes include embeddings for semantic search
- **Temporal Data**: Comprehensive timestamps across all clinical events
- **Rich Laboratory Data**: Extensive lab results with reference ranges and flags
- **Clinical Coding**: ICD codes for diagnoses and procedures with full titles

## Implementation Notes
- Use the official `neo4j` Python driver for database connections.
- Connection parameters will be managed via environment variables: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`.
- Use `python-dotenv` to load environment variables.
- Use OpenAI's API for generating embeddings for natural language queries.
- All API responses should be structured and predictable, preferably using Pydantic models.
- Required libraries:
  - `click`
  - `mcp`
  - `pydantic`
  - `neo4j`
  - `python-dotenv`
  - `openai`
  - `pytest` (dev dependency)
- Use `uv add <package>` to add libraries.
- Use `uv` for project and dependency management.
- Add `mcp-server-neo4j-ehr = "mcp_server_neo4j_ehr:main"` to the `project.scripts` section in `pyproject.toml`.

## API

```
ehr patient <subject_id> \
    --include-admissions: bool = True \
    --include-diagnoses: bool = False \
    --include-procedures: bool = False \
    --include-medications: bool = False \
    --include-lab-events: bool = False \
    --format: json | table = json

ehr search-notes <query> \
    --note-type: discharge | radiology | all = all \
    --limit: int = 5 \
    --semantic: bool = False \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --format: json | text | table = json

ehr list-diagnoses \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

ehr list-lab-events \
    --patient-id: str (required) \
    --admission-id: str (optional) \
    --abnormal-only: bool = False \
    --category: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

ehr list-medications \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --medication: str (optional) \
    --route: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

ehr list-procedures \
    --patient-id: str (optional) \
    --admission-id: str (optional) \
    --limit: int = 20 \
    --format: json | table = json

ehr natural-query <query> \
    --limit: int = 10 \
    --format: json | markdown | table = markdown

ehr get-schema \
    --format: json | markdown = markdown
```

### Example API Calls
```
# Get patient information with all admissions
ehr patient "10000032" --include-admissions=True

# Search discharge notes semantically for a specific patient
ehr search-notes "congestive heart failure" --note-type=discharge --semantic=True --limit=3 --patient-id="10000032"

# List all diagnoses for a specific admission in a table
ehr list-diagnoses --admission-id="22595853" --format=table

# Find abnormal lab results for a patient
ehr list-lab-events --patient-id="10000032" --abnormal-only=True --format=table

# Natural language query to generate a Cypher statement and execute it
ehr natural-query "Show me patients with pneumonia who also had kidney issues"

# Get the database schema to help construct queries
ehr get-schema
```

## Project Structure
- `src/`
  - `mcp_server_neo4j_ehr/`
    - `__init__.py`
    - `__main__.py`
    - `server.py`
      - `serve(neo4j_uri: str, neo4j_user: str, neo4j_pass: str, neo4j_db: str) -> None`
    - `modules/`
      - `__init__.py`
      - `db_connection.py`
      - `data_types.py`
      - `constants.py`
      - `query_builder.py`
      - `functionality/`
        - `patient.py`
        - `search_notes.py`
        - `list_diagnoses.py`
        - `list_lab_events.py`
        - `list_medications.py`
        - `list_procedures.py`
        - `natural_query.py`
        - `get_schema.py`
- `tests/`
  - `__init__.py`
  - `test_db_connection.py`
  - `functionality/`
    - `test_patient.py`
    - `test_search_notes.py`
    - `test_list_diagnoses.py`
    - `test_list_lab_events.py`
    - `test_list_medications.py`
    - `test_list_procedures.py`
    - `test_natural_query.py`
    - `test_get_schema.py`

## Cypher Query Examples

### Patient Query
```cypher
MATCH (p:Patient {subject_id: $subject_id})
OPTIONAL MATCH (p)-[:HAS_ADMISSION]->(a:Admission)
RETURN p, collect(a) as admissions
```

### Semantic Note Search
```cypher
// 1. Generate embedding for the $query_text using OpenAI
// 2. Pass the embedding as $query_embedding to the query
MATCH (note)
WHERE note:DischargeNote OR note:RadiologyReport
CALL db.index.vector.queryNodes('note_embeddings', $limit, $query_embedding) YIELD node, score
RETURN node.text, score
ORDER BY score DESC
```

### Get Schema Query
```cypher
// This procedure returns a description of the graph schema.
// The server will format this output for the user.
CALL db.schema.visualization()
```

### Natural Language to Cypher
The `natural-query` command will use an LLM to translate the natural language input into a Cypher query. This is a multi-step process:
1. The LLM is prompted to first call the `ehr get-schema` tool to understand the graph's structure (nodes, properties, relationships).
2. With the schema as context, the LLM generates a Cypher query that accurately reflects the user's question.
3. The server executes the generated Cypher query and returns the results.

**Example:** "Find discharge notes mentioning allergic reactions to antibiotics"
**Generated Cypher (after consulting schema):**
```cypher
MATCH (p:Patient)-[:HAS_ADMISSION]->(a:Admission)-[:INCLUDES_DISCHARGE_NOTE]->(d:DischargeNote)
WHERE toLower(d.text) CONTAINS 'allergic reaction' AND toLower(d.text) CONTAINS 'antibiotic'
RETURN p.subject_id, a.hadm_id, d.note_id, d.text
LIMIT 10
```

## Validation
- Use `uv run pytest` to validate the functionality against a test Neo4j database instance.
- Use `uv run mcp-server-neo4j-ehr --help` to validate the MCP server CLI.
- Manually test a suite of queries to ensure accuracy and performance.
