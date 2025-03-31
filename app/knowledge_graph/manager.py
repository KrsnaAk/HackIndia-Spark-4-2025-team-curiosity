import os
import json
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class KnowledgeGraphManager:
    """
    Manager class for the finance domain knowledge graph
    - Handles initialization, querying, and management of the graph
    - Simplified mock implementation for testing
    """
    
    def __init__(self):
        # Initialize the graph
        self._load_mock_data()
        self.logger = logging.getLogger(__name__)
    
    def _load_mock_data(self):
        """Load mock data for development"""
        self.mock_data = {
            "entities": {},
            "concepts": [],
            "categories": {
                "investment": ["stocks", "bonds", "mutual_funds", "etfs", "real_estate"],
                "personal_finance": ["budgeting", "savings", "credit", "debt", "retirement"],
                "banking": ["accounts", "loans", "interest_rates", "fees", "services"],
                "market": ["indicators", "trends", "analysis", "sectors", "indices"],
                "risk": ["types", "assessment", "management", "mitigation", "insurance"]
            }
        }
    
    def add_node(self, name: str, node_type: str, properties: Dict[str, Any] = None):
        """
        Add a node to the knowledge graph
        
        Args:
            name: Name of the node
            node_type: Type of the node
            properties: Node properties
        """
        try:
            if name not in self.mock_data["entities"]:
                self.mock_data["entities"][name] = {
                    "type": node_type,
                    "properties": properties or {}
                }
            else:
                # Update existing node
                self.mock_data["entities"][name]["type"] = node_type
                if properties:
                    self.mock_data["entities"][name]["properties"].update(properties)
            
            return True
        except Exception as e:
            self.logger.error(f"Error adding node: {str(e)}")
            return False
    
    def add_relationship(self, source: str, target: str, relationship_type: str, properties: Dict[str, Any] = None):
        """
        Add a relationship between nodes in the knowledge graph
        
        Args:
            source: Source node name
            target: Target node name
            relationship_type: Type of relationship
            properties: Relationship properties
        """
        try:
            # Make sure both nodes exist
            if source not in self.mock_data["entities"]:
                self.add_node(source, "Unknown")
            
            if target not in self.mock_data["entities"]:
                self.add_node(target, "Unknown")
            
            # Add relationship to source node
            if "relationships" not in self.mock_data["entities"][source]:
                self.mock_data["entities"][source]["relationships"] = []
            
            # Add relationship with properties
            relationship = {
                "target": target,
                "type": relationship_type,
                "properties": properties or {}
            }
            
            self.mock_data["entities"][source]["relationships"].append(relationship)
            return True
        except Exception as e:
            self.logger.error(f"Error adding relationship: {str(e)}")
            return False
    
    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific entity
        
        Args:
            entity_id: Unique identifier of the entity
            
        Returns:
            Entity data including properties and relationships
        """
        # In a real implementation, this would query the graph database
        entities = self.mock_data.get("entities", {})
        if entity_id in entities:
            return entities[entity_id]
        return None
    
    def query(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Query the knowledge graph with natural language
        
        Args:
            query: Natural language query
            filters: Optional filters to apply
            limit: Maximum number of results to return
            
        Returns:
            Results and query metadata
        """
        # Mock implementation
        results = []
        concepts = self.mock_data.get("concepts", [])
        
        # Apply filters if provided
        if filters and "category" in filters:
            categories = filters.get("category", [])
            if categories:
                return {
                    "results": [],
                    "query_info": {
                        "original_query": query,
                        "filters_applied": filters if filters else {},
                        "total_matches": 0,
                        "returned": 0
                    }
                }
        
        return {
            "results": [],
            "query_info": {
                "original_query": query,
                "filters_applied": filters if filters else {},
                "total_matches": 0,
                "returned": 0
            }
        }
    
    def get_concepts(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top-level financial concepts, optionally filtered by category
        
        Args:
            category: Optional category filter
            limit: Maximum number of concepts to return
            
        Returns:
            List of concept data
        """
        return []
    
    def get_categories(self) -> List[str]:
        """
        Get all available categories in the knowledge graph
        
        Returns:
            List of category names
        """
        return list(self.mock_data.get("categories", {}).keys())
    
    def get_categories_with_counts(self) -> List[Dict[str, Any]]:
        """Get all available categories in the knowledge graph with counts"""
        categories = self.mock_data.get("categories", {})
        result = []
        
        for category, subcategories in categories.items():
            # In a real implementation, this would query the actual count from the database
            # For mock data, we'll use the number of subcategories as the count
            result.append({
                "name": category,
                "count": len(subcategories),
                "description": f"Financial information related to {category.replace('_', ' ')}"
            })
            
        return result

    def get_graph_enhanced_context(self, query, vector_results):
        """
        Get graph-enhanced context for RAG by combining vector search results with graph knowledge
        
        Args:
            query: User query
            vector_results: Results from vector search
            
        Returns:
            Enhanced context with knowledge graph connections
        """
        try:
            # Extract entities from vector results
            entities = set()
            for result in vector_results:
                metadata = result.get('metadata', {})
                if 'symbol' in metadata:
                    entities.add(metadata['symbol'])
                if 'name' in metadata:
                    entities.add(metadata['name'])
            
            # Get graph context
            graph_context = ""
            for entity in entities:
                # Get node properties
                node = self.get_node_by_name(entity)
                if node:
                    graph_context += f"Information about {node.get('name', entity)}:\n"
                    
                    for prop, value in node.get('properties', {}).items():
                        if prop not in ['name'] and value:
                            graph_context += f"- {prop}: {value}\n"
                    
                    # Get relationships
                    relationships = self.get_relationships(entity)
                    if relationships:
                        graph_context += "Relationships:\n"
                        for rel in relationships:
                            graph_context += f"- {rel.get('relationship_type', '')} {rel.get('target', '')}\n"
                    
                    graph_context += "\n"
            
            # Combine with vector results
            combined_context = "Relevant information:\n\n"
            for i, result in enumerate(vector_results, 1):
                text = result.get('text', '')
                metadata = result.get('metadata', {})
                symbol = metadata.get('symbol', '')
                name = metadata.get('name', symbol)
                
                if name and text:
                    combined_context += f"{i}. {name} ({symbol}): {text}\n\n"
                elif text:
                    combined_context += f"{i}. {text}\n\n"
            
            # Add graph knowledge
            if graph_context:
                combined_context += "\nAdditional knowledge graph information:\n\n" + graph_context
            
            return combined_context
        
        except Exception as e:
            self.logger.error(f"Error generating graph-enhanced context: {str(e)}")
            return ""

    def get_node_by_name(self, name):
        """
        Get a node by its name
        
        Args:
            name: Name of the node
            
        Returns:
            Node properties or None if not found
        """
        try:
            # Search for the node in the graph
            node = self.mock_data.get("entities", {}).get(name)
            if node:
                return node
            
            # Try searching as a property
            for node_name, props in self.mock_data.get("entities", {}).items():
                if props.get('properties', {}).get('symbol') == name:
                    return {**props, 'name': node_name}
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting node by name: {str(e)}")
            return None

    def get_relationships(self, node_name):
        """
        Get all relationships for a node
        
        Args:
            node_name: Name of the node
            
        Returns:
            List of relationships
        """
        try:
            relationships = []
            
            # Get outgoing relationships
            for source, target, props in self.mock_data.get("entities", {}).items():
                if source == node_name:
                    relationships.append({
                        'source': source,
                        'target': target,
                        'relationship_type': props.get('properties', {}).get('type', 'RELATED_TO'),
                        'properties': props.get('properties', {})
                    })
            
            # Get incoming relationships
            for source, target, props in self.mock_data.get("entities", {}).items():
                if target == node_name:
                    relationships.append({
                        'source': source,
                        'target': target,
                        'relationship_type': f"INVERSE_{props.get('properties', {}).get('type', 'RELATED_TO')}",
                        'properties': props.get('properties', {})
                    })
            
            return relationships
        except Exception as e:
            self.logger.error(f"Error getting relationships: {str(e)}")
            return []

    def populate_from_crypto_data(self, crypto_data):
        """
        Populate the knowledge graph with cryptocurrency data
        
        Args:
            crypto_data: Dictionary of crypto data from CoinGecko
        """
        try:
            # Add crypto entities and relationships
            for symbol, data in crypto_data.items():
                name = data.get('name', symbol)
                category = data.get('category', 'Unknown')
                description = data.get('description', '')
                
                # Add the node
                self.add_node(
                    name=name,
                    node_type="Project",
                    properties={
                        "symbol": symbol,
                        "category": category,
                        "description": description,
                        "funding": data.get('funding', 'Unknown'),
                        "market_cap": data.get('mcap', 'Unknown')
                    }
                )
                
                # Add category relationship
                self.add_relationship(
                    source=name,
                    target=category,
                    relationship_type="BELONGS_TO"
                )
                
                # Add relationships between projects of the same category
                for other_symbol, other_data in crypto_data.items():
                    if symbol != other_symbol and other_data.get('category') == category:
                        self.add_relationship(
                            source=name,
                            target=other_data.get('name', other_symbol),
                            relationship_type="RELATED_TO",
                            properties={"relationship": "Same category"}
                        )
            
            return True
        except Exception as e:
            self.logger.error(f"Error populating knowledge graph with crypto data: {str(e)}")
            return False 