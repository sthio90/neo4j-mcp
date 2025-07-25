#!/usr/bin/env python3
"""
Quick script to check what data is available in the Neo4j database.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables
env_path = parent_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)

from src.mcp_server_neo4j_ehr.modules.db_connection import create_neo4j_driver, Neo4jConnection

async def check_database():
    """Check what data is available in the database."""
    # Create driver
    uri = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    print(f"Connecting to: {uri}")
    print(f"Database: {database}")
    
    driver = create_neo4j_driver(uri, username, password)
    db = Neo4jConnection(driver, database)
    
    try:
        # Test connection
        print("\n1. Testing connection...")
        if await db.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed")
            return
        
        # Count nodes of each type
        print("\n2. Counting nodes by type...")
        node_types = ['Patient', 'Admission', 'DischargeNote', 'RadiologyReport', 
                      'LabEvent', 'Medication', 'Diagnosis', 'Procedure']
        
        for node_type in node_types:
            query = f"MATCH (n:{node_type}) RETURN count(n) as count"
            result = await db.execute_read(query)
            count = result[0]['count'] if result else 0
            print(f"   {node_type}: {count:,}")
        
        # Get sample patient IDs
        print("\n3. Sample Patient IDs:")
        query = "MATCH (p:Patient) RETURN p.subject_id as patient_id LIMIT 10"
        results = await db.execute_read(query)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['patient_id']}")
        else:
            print("   No patients found")
        
        # Check for specific patient
        print("\n4. Checking for patient 10006...")
        query = "MATCH (p:Patient {subject_id: '10006'}) RETURN p"
        results = await db.execute_read(query)
        
        if results:
            print("✅ Patient 10006 exists")
            patient = results[0]['p']
            for key, value in patient.items():
                print(f"   {key}: {value}")
        else:
            print("❌ Patient 10006 not found")
        
        # Check relationships
        print("\n5. Checking relationships...")
        query = """
        MATCH (p:Patient)-[r]->(a)
        RETURN type(r) as relationship, labels(a) as target_labels, count(*) as count
        LIMIT 10
        """
        results = await db.execute_read(query)
        
        if results:
            print("   Found relationships:")
            for result in results:
                print(f"   - {result['relationship']} -> {result['target_labels']}: {result['count']}")
        else:
            print("   No relationships found")
            
    finally:
        await db.close()

async def main():
    """Main function."""
    try:
        await check_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())