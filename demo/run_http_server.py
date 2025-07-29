#!/usr/bin/env python3
"""
HTTP Server for Neo4j MCP Server Demo

This script runs the Neo4j MCP server in HTTP mode with CORS enabled,
allowing the HTML demo interface to connect and interact with it.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import the MCP server
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
env_path = parent_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")

try:
    from src.mcp_server_neo4j_ehr.server import main as server_main
except ImportError:
    print("Error: Neo4j MCP server not found. Please ensure the server is properly installed.")
    print("Try running: pip install -e . from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_http_server():
    """Run the MCP server in HTTP mode with CORS enabled."""
    
    # Check for required environment variables
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    # Optional environment variables
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("OPENAI_API_KEY not set. Natural language queries will not work.")
    
    try:
        # Get environment variables
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        host = "localhost"
        port = 8080
        
        logger.info(f"Starting HTTP server on http://{host}:{port}")
        logger.info("CORS is enabled for all origins (*)") 
        logger.info("Press Ctrl+C to stop the server")
        
        # Use the updated server main function
        server_main(
            neo4j_uri=neo4j_uri,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            neo4j_database=neo4j_database,
            openai_api_key_param=openai_api_key,
            transport="http",
            host=host,
            port=port,
            path="/mcp/"
        )
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    print("\n🚀 Neo4j MCP Server - HTTP Mode\n")
    print("This server allows the HTML demo interface to connect to the Neo4j MCP server.")
    print("\nMake sure you have:")
    print("1. Neo4j running with MIMIC data loaded")
    print("2. Environment variables configured (.env file)")
    print("3. Required Python packages installed\n")
    
    try:
        run_http_server()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()