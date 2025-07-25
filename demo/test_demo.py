#!/usr/bin/env python3
"""
Test script to verify the demo works with the hosted Neo4j database.
This script will start the server and run some basic tests.
"""

import asyncio
import aiohttp
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Server URL
SERVER_URL = "http://localhost:8080"

async def test_server_connection():
    """Test if we can connect to the MCP server."""
    print("Testing server connection...")
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                },
                "id": 1
            }
            
            async with session.post(SERVER_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ Server connection successful")
                    return True
                else:
                    print(f"❌ Server returned status: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

async def test_get_schema():
    """Test getting the database schema."""
    print("\nTesting get schema...")
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ehr_get_schema",
                    "arguments": {
                        "format": "json"
                    }
                },
                "id": 2
            }
            
            async with session.post(SERVER_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        print("✅ Schema retrieved successfully")
                        # Parse the JSON content
                        content = data["result"]["content"][0]["text"]
                        schema = json.loads(content)
                        print(f"   Found {len(schema['nodes'])} node types")
                        return True
                    else:
                        print(f"❌ Error: {data.get('error', 'Unknown error')}")
                        return False
        except Exception as e:
            print(f"❌ Schema test failed: {e}")
            return False

async def test_patient_lookup():
    """Test looking up a patient."""
    print("\nTesting patient lookup...")
    async with aiohttp.ClientSession() as session:
        try:
            # Test with a common patient ID
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ehr_patient",
                    "arguments": {
                        "subject_id": "10461137",
                        "include": ["demographics"],
                        "format": "json"
                    }
                },
                "id": 3
            }
            
            async with session.post(SERVER_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        content = data["result"]["content"][0]["text"]
                        patient_data = json.loads(content)
                        if patient_data:
                            print("✅ Patient data retrieved successfully")
                            print(f"   Patient ID: {patient_data.get('subject_id', 'N/A')}")
                            print(f"   Gender: {patient_data.get('gender', 'N/A')}")
                            return True
                        else:
                            print("⚠️  No patient found with ID 10461137")
                            print("   This might be expected if the database doesn't have this patient")
                            return True  # Not a failure, just no data
                    else:
                        print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown error')}")
                        return False
        except Exception as e:
            print(f"❌ Patient lookup failed: {e}")
            return False

async def test_list_patients():
    """Test listing some patients to find valid IDs."""
    print("\nTesting list patients...")
    async with aiohttp.ClientSession() as session:
        try:
            # Use natural query to find some patients
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ehr_natural_query",
                    "arguments": {
                        "query": "Show me 5 patient IDs",
                        "limit": 5,
                        "format": "json"
                    }
                },
                "id": 4
            }
            
            async with session.post(SERVER_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        print("✅ Natural query executed successfully")
                        content = data["result"]["content"][0]["text"]
                        result_data = json.loads(content)
                        if result_data.get("results"):
                            print(f"   Found {len(result_data['results'])} results")
                            # Show first few patient IDs if available
                            for i, result in enumerate(result_data["results"][:3]):
                                print(f"   Result {i+1}: {result}")
                        return True
                    else:
                        error_msg = data.get('error', {}).get('message', 'Unknown error')
                        if 'OPENAI_API_KEY' in error_msg:
                            print("⚠️  Natural query requires OpenAI API key")
                            print("   This is expected if OPENAI_API_KEY is not set")
                            return True  # Not a failure
                        else:
                            print(f"❌ Error: {error_msg}")
                            return False
        except Exception as e:
            print(f"❌ Natural query test failed: {e}")
            return False

async def test_search_notes():
    """Test searching clinical notes."""
    print("\nTesting note search...")
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ehr_search_notes",
                    "arguments": {
                        "query": "pain",
                        "search_type": "text",
                        "limit": 5,
                        "format": "json"
                    }
                },
                "id": 5
            }
            
            async with session.post(SERVER_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        content = data["result"]["content"][0]["text"]
                        results = json.loads(content)
                        if results:
                            print("✅ Note search completed successfully")
                            print(f"   Found {len(results)} notes")
                        else:
                            print("⚠️  No notes found containing 'pain'")
                            print("   This might be expected if the database is empty")
                        return True
                    else:
                        print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown error')}")
                        return False
        except Exception as e:
            print(f"❌ Note search failed: {e}")
            return False

async def run_all_tests():
    """Run all tests."""
    print("🧪 Neo4j MCP Server Demo Test Suite")
    print("=" * 50)
    print(f"Server URL: {SERVER_URL}")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    await asyncio.sleep(2)
    
    tests = [
        test_server_connection,
        test_get_schema,
        test_patient_lookup,
        test_list_patients,
        test_search_notes
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed!")
        print("\nThe demo is working correctly. You can now:")
        print("1. Open demo/index.html in your browser")
        print("2. Click 'Connect' to connect to the server")
        print("3. Start exploring the data!")
    else:
        print("\n⚠️  Some tests did not pass")
        print("This might be expected if:")
        print("- The database doesn't have MIMIC data loaded")
        print("- OpenAI API key is not configured")
        print("- The server is still starting up")
    
    return passed == total

async def main():
    """Main function."""
    # Check if server is supposed to be running
    print("⚠️  Make sure the MCP server is running!")
    print("In another terminal, run:")
    print("  cd demo")
    print("  python run_http_server.py")
    print("\nPress Enter when the server is running...")
    input()
    
    try:
        success = await run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())