"""Entry point for the Neo4j EHR MCP Server."""

import os
import asyncio
import argparse
from dotenv import load_dotenv
from .server import main as server_main

# Load environment variables
load_dotenv()


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Neo4j EHR MCP Server")
    parser.add_argument("--neo4j-uri", help="Neo4j connection URI", 
                        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-username", help="Neo4j username", 
                        default=os.getenv("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--neo4j-password", help="Neo4j password", 
                        default=os.getenv("NEO4J_PASSWORD", "password"))
    parser.add_argument("--neo4j-database", help="Neo4j database name", 
                        default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--openai-api-key", help="OpenAI API key for semantic search", 
                        default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--transport", default="stdio", 
                        choices=["stdio", "sse", "http"],
                        help="Transport type (stdio, sse, http)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")
    parser.add_argument("--path", default="/mcp/", help="Path for HTTP transport")
    
    args = parser.parse_args()
    
    # Validate required parameters
    if not args.neo4j_password:
        parser.error("Neo4j password is required (via --neo4j-password or NEO4J_PASSWORD env var)")
    
    # Run the server
    asyncio.run(server_main(
        args.neo4j_uri,
        args.neo4j_username,
        args.neo4j_password,
        args.neo4j_database,
        args.openai_api_key,
        args.transport,
        args.host,
        args.port,
        args.path
    ))


if __name__ == "__main__":
    main()