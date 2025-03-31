from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    A mock Neo4j client for development purposes
    """
    
    def __init__(self):
        """Initialize the mock Neo4j client"""
        logger.info("Initializing mock Neo4j client")
        self.connected = True
    
    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query against the Neo4j database
        
        Args:
            cypher_query: The Cypher query to execute
            params: Optional parameters for the query
            
        Returns:
            List of query results as dictionaries
        """
        logger.debug(f"Mock query executed: {cypher_query}")
        # Return empty results for all queries
        return []
    
    def close(self):
        """Close the connection to the Neo4j database"""
        logger.info("Closing mock Neo4j client connection")
        self.connected = False 