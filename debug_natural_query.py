#!/usr/bin/env python3
"""
Debug script for testing natural language queries with the Neo4j EHR MCP Server.
This script shows all the outputs from the LLM and query execution.
"""

import asyncio
import json
import logging
import os
import sys
from dotenv import load_dotenv

from src.mcp_server_neo4j_ehr.modules.db_connection import create_neo4j_driver, Neo4jConnection
from src.mcp_server_neo4j_ehr.modules.functionality.natural_query import natural_query
from src.mcp_server_neo4j_ehr.modules.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_MARKDOWN

# Configure logging to show all output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Also log debug messages from our module
logging.getLogger('src.mcp_server_neo4j_ehr').setLevel(logging.DEBUG)


async def test_query(query_text: str):
    """Test a natural language query and show all outputs."""
    
    load_dotenv()
    
    # Check for required environment variables
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not all([neo4j_uri, neo4j_username, neo4j_password, openai_api_key]):
        print("Error: Required environment variables not set.")
        print("Please ensure NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, and OPENAI_API_KEY are set.")
        return
    
    # Create database connection
    driver = create_neo4j_driver(neo4j_uri, neo4j_username, neo4j_password)
    db = Neo4jConnection(driver, neo4j_database)
    
    try:
        print(f"\nTesting connection to Neo4j...")
        if await db.test_connection():
            print("✓ Connected to Neo4j successfully!")
        else:
            print("✗ Failed to connect to Neo4j")
            return
        
        print(f"\nProcessing query: '{query_text}'")
        print("-" * 80)
        
        # Execute the natural language query
        result = await natural_query(
            db,
            query=query_text,
            limit=10,
            format=OUTPUT_FORMAT_JSON,
            openai_api_key=openai_api_key
        )
        
        # Parse and display results
        data = json.loads(result)
        
        print("\n" + "="*80)
        print("QUERY RESULTS")
        print("="*80)
        
        if "error" in data:
            print(f"ERROR: {data['error']}")
            if "details" in data:
                print(f"Details: {data['details']}")
            if "query" in data:
                print(f"Failed Query: {data['query']}")
        else:
            print(f"Question: {data.get('question', 'N/A')}")
            print(f"\nGenerated Cypher Query:")
            print(f"  {data.get('cypher_query', 'N/A')}")
            print(f"\nResult Count: {data.get('count', 0)}")
            print(f"\nResults:")
            results = data.get('results', [])
            if results:
                for i, result in enumerate(results[:5]):  # Show first 5 results
                    print(f"  [{i+1}] {json.dumps(result, indent=4)}")
                if len(results) > 5:
                    print(f"  ... and {len(results) - 5} more results")
            else:
                print("  No results found")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await driver.close()


def main():
    """Main entry point for the debug script."""
    
    # Check if query was provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        asyncio.run(test_query(query))
    else:
        # Interactive mode
        print("Neo4j EHR Natural Language Query Debugger")
        print("=========================================")
        print("Enter natural language queries to test, or 'quit' to exit.")
        print()
        
        while True:
            try:
                query = input("Query> ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if query:
                    asyncio.run(test_query(query))
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()