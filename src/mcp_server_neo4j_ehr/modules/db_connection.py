"""Database connection management for Neo4j."""

import logging
from typing import Optional, Dict, Any, List
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncResult
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connections and queries."""
    
    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        self.driver = driver
        self.database = database
    
    async def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read query and return results as a list of dictionaries."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(
                    self._run_query, query, parameters or {}
                )
                return result
        except Neo4jError as e:
            logger.error(f"Neo4j read error: {e}")
            raise
    
    async def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a write query and return results as a list of dictionaries."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    self._run_query, query, parameters or {}
                )
                return result
        except Neo4jError as e:
            logger.error(f"Neo4j write error: {e}")
            raise
    
    @staticmethod
    async def _run_query(tx, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run a query within a transaction."""
        result = await tx.run(query, parameters)
        records = await result.data()
        return records
    
    async def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            await self.execute_read("RETURN 1 as test")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get the database schema information."""
        schema = {
            "nodes": [],
            "relationships": [],
            "constraints": [],
            "indexes": []
        }
        
        # Get node labels and properties
        node_query = """
        CALL db.labels() YIELD label
        WITH label
        MATCH (n)
        WHERE label IN labels(n)
        WITH label, n
        LIMIT 1
        RETURN label, keys(n) as properties
        """
        nodes = await self.execute_read(node_query)
        schema["nodes"] = nodes
        
        # Get relationship types
        rel_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        """
        relationships = await self.execute_read(rel_query)
        schema["relationships"] = relationships
        
        # Get constraints
        constraint_query = "SHOW CONSTRAINTS"
        try:
            constraints = await self.execute_read(constraint_query)
            schema["constraints"] = constraints
        except:
            logger.warning("Could not fetch constraints")
        
        # Get indexes
        index_query = "SHOW INDEXES"
        try:
            indexes = await self.execute_read(index_query)
            schema["indexes"] = indexes
        except:
            logger.warning("Could not fetch indexes")
        
        return schema
    
    async def close(self):
        """Close the database connection."""
        if self.driver:
            await self.driver.close()


def create_neo4j_driver(uri: str, username: str, password: str) -> AsyncDriver:
    """Create a Neo4j async driver instance."""
    return AsyncGraphDatabase.driver(uri, auth=(username, password))