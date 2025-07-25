"""Natural language query functionality using LLM."""

import json
import logging
from typing import Any, Dict, List
from openai import OpenAI
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import OutputFormat
from ..constants import (
    OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_MARKDOWN,
    NATURAL_QUERY_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


async def natural_query(
    db: Neo4jConnection,
    query: str,
    limit: int = 10,
    format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
    openai_api_key: str = None
) -> str:
    """Convert natural language query to Cypher and execute."""
    
    try:
        # Log the incoming natural language query
        logger.info(f"Natural language query: {query}")
        
        # First, get the database schema
        schema = await db.get_schema()
        schema_text = format_schema_for_llm(schema)
        logger.debug(f"Schema text sent to LLM: {schema_text[:500]}...")  # First 500 chars
        
        # Generate Cypher query using LLM
        client = OpenAI(api_key=openai_api_key)
        
        messages = [
            {"role": "system", "content": NATURAL_QUERY_SYSTEM_PROMPT},
            {"role": "user", "content": f"Database Schema:\n{schema_text}\n\nQuestion: {query}\n\nGenerate a Cypher query with LIMIT {limit}:"}
        ]
        
        logger.info("Sending query to OpenAI GPT-4...")
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
        
        cypher_query = response.choices[0].message.content.strip()
        logger.info(f"Raw LLM response: {cypher_query}")
        
        # Clean up the query (remove markdown code blocks if present)
        if cypher_query.startswith("```"):
            cypher_query = cypher_query.split("```")[1]
            if cypher_query.startswith("cypher"):
                cypher_query = cypher_query[6:]
        cypher_query = cypher_query.strip()
        
        logger.info(f"Cleaned Cypher query: {cypher_query}")
        
        # Execute the query
        try:
            results = await db.execute_read(cypher_query)
            logger.info(f"Query executed successfully. Result count: {len(results)}")
            if results and len(results) > 0:
                logger.debug(f"First result: {results[0]}")
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return json.dumps({
                "error": "Failed to execute generated query",
                "query": cypher_query,
                "details": str(e)
            })
        
        # Format results
        response_data = {
            "question": query,
            "cypher_query": cypher_query,
            "results": results,
            "count": len(results)
        }
        logger.info(f"Returning {len(results)} results for query: {query}")
        
        if format == OUTPUT_FORMAT_MARKDOWN:
            return format_natural_query_as_markdown(response_data)
        elif format == OUTPUT_FORMAT_TABLE:
            return format_natural_query_as_table(response_data)
        else:
            return json.dumps(response_data)
            
    except Exception as e:
        logger.error(f"Error in natural language query: {e}")
        return json.dumps({
            "error": "Failed to process natural language query",
            "details": str(e)
        })


def format_schema_for_llm(schema: Dict[str, Any]) -> str:
    """Format schema information for LLM context."""
    lines = []
    
    # Node labels and properties
    lines.append("NODES:")
    for node in schema.get("nodes", []):
        label = node.get("label", "Unknown")
        properties = node.get("properties", [])
        lines.append(f"- {label}: {', '.join(properties)}")
    
    # Relationships
    lines.append("\nRELATIONSHIPS:")
    for rel in schema.get("relationships", []):
        rel_type = rel.get("relationshipType", "Unknown")
        lines.append(f"- {rel_type}")
    
    # Key relationships based on our spec
    lines.append("\nKEY RELATIONSHIPS:")
    lines.append("- (Patient)-[:HAS_ADMISSION]->(Admission)")
    lines.append("- (Admission)-[:INCLUDES_DISCHARGE_NOTE]->(DischargeNote)")
    lines.append("- (Admission)-[:INCLUDES_RADIOLOGY_REPORT]->(RadiologyReport)")
    lines.append("- (Admission)-[:HAS_DIAGNOSIS]->(Diagnosis)")
    lines.append("- (Admission)-[:HAS_PROCEDURE]->(Procedure)")
    lines.append("- (Admission)-[:HAS_MEDICATION]->(Medication)")
    lines.append("- (Admission)-[:INCLUDES_LAB_EVENT]->(LabEvent)")
    
    return "\n".join(lines)


def format_natural_query_as_markdown(data: Dict[str, Any]) -> str:
    """Format natural query results as markdown."""
    lines = []
    
    lines.append(f"## Question\n{data['question']}\n")
    lines.append(f"## Generated Cypher Query\n```cypher\n{data['cypher_query']}\n```\n")
    lines.append(f"## Results ({data['count']} rows)\n")
    
    if data['results']:
        # Create table from results
        first_row = data['results'][0]
        headers = list(first_row.keys())
        
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["-" * len(h) for h in headers]) + " |")
        
        for row in data['results']:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")
    else:
        lines.append("No results found.")
    
    return "\n".join(lines)


def format_natural_query_as_table(data: Dict[str, Any]) -> str:
    """Format natural query results as table."""
    output = []
    
    output.append(f"QUESTION: {data['question']}")
    output.append(f"\nCYPHER QUERY:\n{data['cypher_query']}")
    output.append(f"\nRESULTS ({data['count']} rows):")
    
    if data['results']:
        # Convert results to table
        headers = list(data['results'][0].keys())
        table_data = []
        
        for row in data['results']:
            table_data.append([str(row.get(h, "")) for h in headers])
        
        output.append(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        output.append("No results found.")
    
    return "\n".join(output)