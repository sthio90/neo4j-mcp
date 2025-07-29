#!/usr/bin/env python3
"""
Simple STDIO client to test the Neo4j EHR MCP Server.
This communicates directly with the server via STDIO, avoiding HTTP/CORS issues.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

class MCPStdioClient:
    def __init__(self, server_command):
        """Initialize the STDIO client with the server command."""
        self.server_command = server_command
        self.process = None
        self.request_id = 0
        
    def start_server(self):
        """Start the MCP server process."""
        print(f"🚀 Starting MCP server: {' '.join(self.server_command)}")
        self.process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        time.sleep(2)  # Give server time to start
        print("✅ Server started")
        
    def send_request(self, method, params=None):
        """Send a JSON-RPC request to the server."""
        if not self.process:
            raise RuntimeError("Server not started")
            
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id
        }
        
        request_json = json.dumps(request)
        print(f"\n📤 Sending: {method}")
        print(f"   Request: {request_json}")
        
        # Send request
        self.process.stdin.write(request_json + "\n")
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            stderr_output = self.process.stderr.read()
            raise RuntimeError(f"No response from server. Stderr: {stderr_output}")
            
        try:
            response = json.loads(response_line)
            print(f"📥 Response: {json.dumps(response, indent=2)}")
            return response
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {response_line}")
            print(f"   Error: {e}")
            return None
            
    def stop_server(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 Server stopped")

def test_all_tools():
    """Test all EHR tools systematically."""
    
    # Server command - using STDIO transport (default)
    server_cmd = [
        "uv", "run", "mcp-server-neo4j-ehr",
        "--neo4j-password", "0d5lUsufRUO0FNUt2FEm7gVagPP2ovThFq6n0GRXH08"
    ]
    
    client = MCPStdioClient(server_cmd)
    
    try:
        # Start server
        client.start_server()
        
        # Test 1: Initialize connection
        print("\n" + "="*60)
        print("TEST 1: Initialize Connection")
        print("="*60)
        
        init_response = client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0"
            }
        })
        
        if init_response and not init_response.get("error"):
            print("✅ Initialization successful")
        else:
            print("❌ Initialization failed:", init_response.get("error"))
            return
            
        # Test 2: Get Schema
        print("\n" + "="*60)
        print("TEST 2: Get Database Schema")
        print("="*60)
        
        schema_response = client.send_request("tools/call", {
            "name": "ehr_get_schema",
            "arguments": {
                "format": "json"
            }
        })
        
        if schema_response and not schema_response.get("error"):
            print("✅ Schema retrieval successful")
        else:
            print("❌ Schema retrieval failed:", schema_response.get("error"))
            
        # Test 3: Get Patient Info
        print("\n" + "="*60)
        print("TEST 3: Get Patient Information")
        print("="*60)
        
        patient_response = client.send_request("tools/call", {
            "name": "ehr_patient",
            "arguments": {
                "subject_id": "10000032",
                "include_admissions": True,
                "format": "json"
            }
        })
        
        if patient_response and not patient_response.get("error"):
            print("✅ Patient lookup successful")
        else:
            print("❌ Patient lookup failed:", patient_response.get("error"))
            
        # Test 4: Search Notes
        print("\n" + "="*60)
        print("TEST 4: Search Clinical Notes")
        print("="*60)
        
        notes_response = client.send_request("tools/call", {
            "name": "ehr_search_notes",
            "arguments": {
                "query": "chest pain",
                "limit": 3,
                "format": "json"
            }
        })
        
        if notes_response and not notes_response.get("error"):
            print("✅ Notes search successful")
        else:
            print("❌ Notes search failed:", notes_response.get("error"))
            
        # Test 5: List Diagnoses
        print("\n" + "="*60)
        print("TEST 5: List Diagnoses")
        print("="*60)
        
        diagnoses_response = client.send_request("tools/call", {
            "name": "ehr_list_diagnoses",
            "arguments": {
                "limit": 5,
                "format": "json"
            }
        })
        
        if diagnoses_response and not diagnoses_response.get("error"):
            print("✅ Diagnoses list successful")
        else:
            print("❌ Diagnoses list failed:", diagnoses_response.get("error"))
            
        # Test 6: Natural Language Query (if OpenAI key available)
        print("\n" + "="*60)
        print("TEST 6: Natural Language Query")
        print("="*60)
        
        natural_response = client.send_request("tools/call", {
            "name": "ehr_natural_query",
            "arguments": {
                "query": "How many patients are in the database?",
                "format": "markdown"
            }
        })
        
        if natural_response and not natural_response.get("error"):
            print("✅ Natural query successful")
        else:
            print("❌ Natural query failed:", natural_response.get("error"))
            if "OpenAI API key" in str(natural_response.get("error", "")):
                print("   (This is expected if OpenAI API key is not configured)")
            
        print("\n" + "="*60)
        print("🏁 ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        
    finally:
        client.stop_server()

def interactive_mode():
    """Interactive mode for manual testing."""
    print("🎮 Interactive Mode - Send custom requests")
    print("Available tools: ehr_patient, ehr_search_notes, ehr_list_diagnoses,")
    print("  ehr_list_medications, ehr_list_procedures, ehr_list_lab_events,")
    print("  ehr_natural_query, ehr_get_schema")
    print("Type 'quit' to exit")
    
    server_cmd = [
        "uv", "run", "mcp-server-neo4j-ehr", 
        "--neo4j-password", "0d5lUsufRUO0FNUt2FEm7gVagPP2ovThFq6n0GRXH08"
    ]
    
    client = MCPStdioClient(server_cmd)
    client.start_server()
    
    # Initialize
    client.send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "interactive-client", "version": "1.0"}
    })
    
    try:
        while True:
            print("\n" + "-"*40)
            tool_name = input("Enter tool name (or 'quit'): ").strip()
            if tool_name.lower() == 'quit':
                break
                
            print("Enter arguments as JSON (or press Enter for empty):")
            args_input = input().strip()
            
            if args_input:
                try:
                    arguments = json.loads(args_input)
                except json.JSONDecodeError:
                    print("❌ Invalid JSON format")
                    continue
            else:
                arguments = {}
                
            client.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
    except KeyboardInterrupt:
        print("\n👋 Exiting interactive mode")
    finally:
        client.stop_server()

def main():
    """Main function."""
    print("🧪 Neo4j EHR MCP Server STDIO Test Client")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        print("Running automated tests...")
        print("(Use 'python test_stdio_client.py interactive' for manual testing)")
        test_all_tools()

if __name__ == "__main__":
    main()