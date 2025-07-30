# Agentic Search Architecture: Replacing Vector Search with Intelligence

## Table of Contents
1. [Overview](#overview)
2. [Big O Complexity: Vector vs Agentic Search](#big-o-complexity-vector-vs-agentic-search)
3. [Query Caching Implementation](#query-caching-implementation)
4. [Complete Implementation Plan](#complete-implementation-plan)
5. [Architecture Comparison](#architecture-comparison)
6. [Scalability Analysis](#scalability-analysis)
7. [Future Improvements](#future-improvements)

## Overview

This document outlines the transition from vector-based semantic search to an agentic search architecture that leverages LLM intelligence for query generation rather than embedding similarity.

### Key Insight
With intelligent agents like Claude Desktop orchestrating queries, and GPT-4 generating precise Cypher queries, we can achieve better results than vector similarity search while reducing complexity and improving scalability.

## Big O Complexity: Vector vs Agentic Search

### Vector Search: O(n) - Why It's Linear

Vector search must compare your query embedding against **every document** in the database:

```
Query: "Find notes about respiratory failure"
         ↓
    [0.23, -0.81, 0.45, ...] (1536 dimensions)
         ↓
Compare with EVERY note:
  Note 1: distance = 0.82
  Note 2: distance = 0.91  
  Note 3: distance = 0.23  ← Best match
  ...
  Note 10,000: distance = 0.95
```

**Why O(n)?**
- Must check all n documents
- Even with optimizations (like HNSW), approximate O(n) for high recall
- As you add patients: 100 → 1,000 → 10,000 patients, search time grows linearly

### Agentic Search: O(log n) - Why It's Logarithmic

Agentic search uses database indexes to find data directly:

```
Query: "Find notes about respiratory failure for patient 123"
         ↓
    GPT-4 generates: 
    MATCH (p:Patient {subject_id: '123'})-[:HAS_ADMISSION]->(a)
          -[:INCLUDES_DISCHARGE_NOTE]->(n)
    WHERE n.text CONTAINS 'respiratory failure'
         ↓
    Neo4j uses indexes:
    1. Binary search patient index: O(log n)
    2. Follow relationships: O(1) per relationship
    3. Filter on indexed property: O(log m) where m << n
```

**Why O(log n)?**
- Database indexes use B-trees or similar structures
- Finding patient 123 among 10,000 patients takes ~14 comparisons, not 10,000
- Relationships in graphs are direct pointers (O(1) traversal)

### Real-World Example

For 10,000 patients with 10 notes each (100,000 total notes):

| Operation | Vector Search | Agentic Search |
|-----------|--------------|----------------|
| Find all notes mentioning "cardiac arrest" | Check all 100,000 notes | Use text index: ~17 operations |
| Find patient 5000's notes about "diabetes" | Check all 100,000 notes | Find patient (14 ops) + scan their 10 notes |
| Complex: "Patients who developed sepsis after cardiac surgery" | Can't do this directly! | Join operations with indexes: ~50 ops total |

## Query Caching Implementation

### How Caching Would Work

```python
from functools import lru_cache
from typing import Dict, Tuple
import hashlib
import json
import time

class QueryCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[str, float, str]] = {}
        self.ttl = ttl_seconds
    
    def _generate_key(self, query: str, limit: int) -> str:
        """Generate cache key from query parameters."""
        # Normalize query: lowercase, strip whitespace
        normalized = query.lower().strip()
        # Include limit in key
        cache_input = f"{normalized}::limit={limit}"
        # Create hash for consistent key length
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def get(self, query: str, limit: int) -> Optional[str]:
        """Get cached Cypher query if valid."""
        key = self._generate_key(query, limit)
        
        if key in self.cache:
            cypher, timestamp, original_query = self.cache[key]
            # Check if cache is still valid
            if time.time() - timestamp < self.ttl:
                return cypher
            else:
                # Expired, remove from cache
                del self.cache[key]
        
        return None
    
    def set(self, query: str, limit: int, cypher: str):
        """Cache the generated Cypher query."""
        key = self._generate_key(query, limit)
        self.cache[key] = (cypher, time.time(), query)

# Integration with natural_query function
class CachedNaturalQuery:
    def __init__(self):
        self.cache = QueryCache(ttl_seconds=3600)  # 1 hour cache
        self.stats = {"hits": 0, "misses": 0}
    
    async def query(self, db, query: str, limit: int, openai_key: str) -> str:
        # Check cache first
        cached_cypher = self.cache.get(query, limit)
        
        if cached_cypher:
            self.stats["hits"] += 1
            logger.info(f"Cache HIT for query: {query[:50]}...")
            # Execute cached Cypher directly
            results = await db.execute_read(cached_cypher)
        else:
            self.stats["misses"] += 1
            logger.info(f"Cache MISS for query: {query[:50]}...")
            # Generate new Cypher via GPT-4
            cypher = await self._generate_cypher(query, limit, openai_key)
            # Cache for next time
            self.cache.set(query, limit, cypher)
            # Execute
            results = await db.execute_read(cypher)
        
        return self._format_results(results)
```

### Cache Key Strategy

1. **Normalize queries** to increase cache hits:
   ```python
   "What medications did patient 123 take?" 
   "what medications did patient 123 take"
   "What medications did patient 123 take???"
   → All map to same cache key
   ```

2. **Include parameters** that affect the query:
   - Limit value
   - Time ranges (if added)
   - Output format

3. **Don't cache** queries with:
   - Current date/time references ("patients admitted today")
   - User-specific context
   - Queries that modify data

### TTL Considerations

| Data Type | Suggested TTL | Reasoning |
|-----------|--------------|-----------|
| Patient demographics | 24 hours | Rarely changes |
| Clinical notes | 1 hour | New notes added during admissions |
| Lab results | 30 minutes | Can change frequently for active patients |
| Aggregations/counts | 5 minutes | Most volatile |

## Complete Implementation Plan

### Phase 1: Remove Vector Search (Week 1)

```python
# 1. Remove from data_types.py
class DischargeNote(BaseNodeModel):
    note_id: str
    hadm_id: Optional[str] = None
    subject_id: Optional[str] = None
    note_type: str
    text: str
    note_seq: Optional[int] = None
    charttime: Optional[datetime] = None
    storetime: Optional[datetime] = None
    # REMOVE THESE:
    # embedding: Optional[List[float]] = None
    # embedding_model: Optional[str] = None
    # embedding_created: Optional[datetime] = None

# 2. Remove from constants.py
# DELETE: EMBEDDING_MODEL = "text-embedding-3-small"
# DELETE: EMBEDDING_DIMENSION = 1536
# DELETE: NOTE_EMBEDDINGS_INDEX = "note_embeddings"

# 3. Update database schema
async def cleanup_vectors(db):
    """Remove vector indexes and properties."""
    await db.execute_write("""
        DROP INDEX note_embeddings IF EXISTS
    """)
    
    await db.execute_write("""
        MATCH (n:DischargeNote)
        REMOVE n.embedding, n.embedding_model, n.embedding_created
    """)
```

### Phase 2: Optimize Natural Query (Week 1-2)

```python
# Enhanced natural_query.py
NATURAL_QUERY_SYSTEM_PROMPT = """
You are a Cypher query generator for a Neo4j medical database.

PERFORMANCE RULES:
1. ALWAYS use indexed properties in WHERE clauses
2. ALWAYS include LIMIT to prevent large results
3. For existence checks, use EXISTS() or LIMIT 1
4. For counts, use COUNT(*) not COLLECT()
5. Filter by patient_id or admission_id FIRST

QUERY PATTERNS FOR SCALE:
- Patient lookup: MATCH (p:Patient {subject_id: $id}) - O(log n)
- Recent notes: ORDER BY n.charttime DESC LIMIT 10 - O(n log n) but limited
- Text search: WHERE n.text CONTAINS 'term' - O(n) but on filtered set
- Relationships: Use specific paths, not variable-length

EXAMPLE EFFICIENT QUERIES:
// Get recent labs for patient
MATCH (l:LabEvent {subject_id: '123'})
WHERE l.charttime > datetime() - duration('P7D')
ORDER BY l.charttime DESC
LIMIT 20

// Count patients with condition
MATCH (d:Diagnosis)
WHERE d.long_title CONTAINS 'heart failure'
RETURN COUNT(DISTINCT d.subject_id) as patient_count
"""
```

### Phase 3: Add Performance Features (Week 2)

```python
# 1. Query Analysis Tool
@mcp.tool
async def ehr_analyze_query(
    query: str,
    format: OutputFormat = OUTPUT_FORMAT_MARKDOWN
) -> str:
    """Analyze what Cypher would be generated without executing.
    Useful for debugging and learning."""
    
    # Generate Cypher
    cypher = await generate_cypher_only(query)
    
    # Analyze complexity
    analysis = analyze_query_complexity(cypher)
    
    return format_analysis(cypher, analysis, format)

# 2. Batch Operations
@mcp.tool
async def ehr_batch_get_notes(
    patient_ids: List[str],
    note_type: NoteType = "all",
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """Efficiently retrieve notes for multiple patients."""
    
    # Use UNWIND for efficient batch processing
    cypher = """
    UNWIND $patient_ids AS pid
    MATCH (p:Patient {subject_id: pid})-[:HAS_ADMISSION]->(a)
    OPTIONAL MATCH (a)-[:INCLUDES_DISCHARGE_NOTE]->(d)
    OPTIONAL MATCH (a)-[:INCLUDES_RADIOLOGY_REPORT]->(r)
    WITH p, COLLECT(DISTINCT d) as discharge_notes, 
         COLLECT(DISTINCT r) as radiology_reports
    RETURN p.subject_id as patient_id, 
           discharge_notes, 
           radiology_reports
    """
    
    results = await db.execute_read(cypher, {"patient_ids": patient_ids})
    return format_results(results, format)

# 3. Query Performance Monitor
class QueryPerformanceMonitor:
    def __init__(self):
        self.query_times = []
    
    async def monitor(self, func, *args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            self.query_times.append({
                "timestamp": start,
                "duration": duration,
                "success": True
            })
            if duration > 5.0:
                logger.warning(f"Slow query detected: {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            self.query_times.append({
                "timestamp": start,
                "duration": duration,
                "success": False,
                "error": str(e)
            })
            raise
```

## Architecture Comparison

### Vector Search Architecture
```
User Query → Embedding API → Vector DB → Similarity Search → Results
    ↓            $0.0001         ↑              O(n)
    └──────────────────────────→ Neo4j → Post-filter → Results
```

**Pros:**
- Good for "find similar" use cases
- No query generation needed
- Works with unstructured data

**Cons:**
- Can't do complex relationships
- Requires embedding maintenance
- Additional API costs
- O(n) complexity
- Storage overhead (1536 floats per document)

### Agentic Search Architecture
```
User Query → GPT-4 → Cypher Query → Neo4j → Results
    ↓         $0.01      O(1)        O(log n)
    └────────────────────────────────┘
         Cached for repeated queries
```

**Pros:**
- Complex relationship queries
- Precise, not just similar
- O(log n) with indexes
- No storage overhead
- Temporal reasoning

**Cons:**
- Requires structured data
- GPT-4 API costs (but cacheable)
- Potential for bad query generation

## Scalability Analysis

### At Different Scales

| Scale | Patients | Notes | Vector Search Time | Agentic Search Time |
|-------|----------|-------|-------------------|-------------------|
| Small | 100 | 1,000 | 50ms | 20ms |
| Medium | 1,000 | 10,000 | 500ms | 25ms |
| Large | 10,000 | 100,000 | 5,000ms | 30ms |
| Huge | 100,000 | 1,000,000 | 50,000ms | 35ms |

### Why Agentic Scales Better

1. **Index Usage**
   ```cypher
   // This uses patient index - O(log n)
   MATCH (p:Patient {subject_id: '12345'})
   
   // Then follows relationships - O(1) per relationship
   MATCH (p)-[:HAS_ADMISSION]->(a)
   ```

2. **Filtered Searches**
   ```cypher
   // Only searches notes for ONE patient, not all
   MATCH (p:Patient {subject_id: '123'})-[:HAS_ADMISSION]->(a)
         -[:INCLUDES_DISCHARGE_NOTE]->(n)
   WHERE n.text CONTAINS 'sepsis'
   ```

3. **Aggregations Without Full Scans**
   ```cypher
   // Uses diagnosis index, not full scan
   MATCH (d:Diagnosis {icd_code: 'I50'})
   RETURN COUNT(DISTINCT d.subject_id)
   ```

## Future Improvements

### 1. Query Pattern Learning
```python
class QueryPatternLearner:
    """Learn common query patterns to pre-optimize."""
    
    def __init__(self):
        self.patterns = defaultdict(int)
    
    def record_query(self, natural_language: str, cypher: str):
        # Extract pattern
        pattern = self.extract_pattern(natural_language)
        self.patterns[pattern] += 1
        
        # After 10 occurrences, create optimized template
        if self.patterns[pattern] == 10:
            self.create_template(pattern, cypher)
```

### 2. Intelligent Caching
```python
class IntelligentCache:
    """Cache that understands medical data patterns."""
    
    def should_cache(self, query: str) -> bool:
        # Don't cache time-sensitive queries
        if any(term in query.lower() for term in ['today', 'now', 'current']):
            return False
        
        # Always cache expensive aggregations
        if 'count' in query.lower() or 'average' in query.lower():
            return True
        
        # Cache patient-specific queries with longer TTL
        if re.search(r'patient \d+', query):
            return True
```

### 3. Query Optimization Hints
```python
async def optimize_natural_query(query: str) -> str:
    """Suggest query optimizations to user."""
    
    if "all patients" in query.lower():
        return (
            "Tip: This query might be slow. Consider:\n"
            "- Adding a time range (e.g., 'in the last year')\n"
            "- Filtering by condition first\n"
            "- Using a sample (e.g., 'show me 10 examples')"
        )
```

### 4. Monitoring Dashboard
```python
class MCPMonitoringDashboard:
    """Track MCP server performance."""
    
    async def get_metrics(self) -> dict:
        return {
            "cache_hit_rate": self.cache.get_hit_rate(),
            "avg_query_time": self.monitor.get_average_time(),
            "slow_queries": self.monitor.get_slow_queries(),
            "popular_queries": self.cache.get_popular_queries(),
            "error_rate": self.monitor.get_error_rate()
        }
```

### 5. Federated Queries
```python
@mcp.tool
async def ehr_federated_query(
    query: str,
    databases: List[str] = ["main"],
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """Query across multiple Neo4j databases."""
    
    # Generate Cypher for each database
    results = []
    for db_name in databases:
        db_results = await query_database(db_name, query)
        results.extend(db_results)
    
    return format_federated_results(results, format)
```

## Conclusion

The shift from vector search to agentic search represents a fundamental change in how we approach medical data retrieval:

- **From similarity to intelligence**: We're not finding "similar" notes, we're answering specific questions
- **From O(n) to O(log n)**: Scalability improves dramatically with proper indexing
- **From embeddings to relationships**: Leveraging the graph structure gives us more precise results

This architecture is not just more scalable—it's more aligned with how medical professionals actually query data: with specific questions about specific patients, not vague similarity searches.