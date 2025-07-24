#!/usr/bin/env python3
"""Test connection to Neo4j database and basic functionality.

Run with: uv run python examples/test_connection.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.mcp_server_neo4j_ehr.modules.db_connection import create_neo4j_driver, Neo4jConnection

# Load environment variables
load_dotenv()


async def test_connection():
    """Test basic database connection and queries."""
    
    # Get connection parameters
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print(f"Connecting to Neo4j at {uri}...")
    
    # Create driver and connection
    driver = create_neo4j_driver(uri, username, password)
    db = Neo4jConnection(driver, database)
    
    try:
        # Test connection
        if await db.test_connection():
            print("✓ Connection successful!")
        else:
            print("✗ Connection failed!")
            return
        
        # Get schema info
        print("\nFetching database schema...")
        schema = await db.get_schema()
        
        print(f"\nFound {len(schema['nodes'])} node types:")
        for node in schema['nodes']:
            print(f"  - {node.get('label', 'Unknown')}")
        
        print(f"\nFound {len(schema['relationships'])} relationship types:")
        for rel in schema['relationships']:
            print(f"  - {rel.get('relationshipType', 'Unknown')}")
        
        # Test a simple query
        print("\nTesting patient count query...")
        result = await db.execute_read("MATCH (p:Patient) RETURN count(p) as count")
        if result:
            print(f"✓ Found {result[0]['count']} patients in the database")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await driver.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    asyncio.run(test_connection())