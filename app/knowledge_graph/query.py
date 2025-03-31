from typing import Dict, Any, List, Optional
import os
from app.knowledge_graph.manager import KnowledgeGraphManager

# Initialize knowledge graph manager
kg_manager = KnowledgeGraphManager()

def query_knowledge_graph(query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Query the financial knowledge graph to get relevant context for a given query
    
    Args:
        query: Natural language query
        filters: Optional filters to apply to the query
        
    Returns:
        Dict containing relevant knowledge graph information
    """
    # Get results from knowledge graph
    kg_results = kg_manager.query(query=query, filters=filters)
    
    # Format results for LLM consumption
    formatted_results = {
        "query": query,
        "concepts": [],
        "relationships": [],
        "definitions": [],
        "sources": []
    }
    
    # Process results
    for item in kg_results.get("results", []):
        # Add concept information
        concept_info = {
            "id": item["id"],
            "name": item["properties"].get("name", item["id"]),
            "category": item["properties"].get("category", "general"),
        }
        formatted_results["concepts"].append(concept_info)
        
        # Add definition if available
        if "definition" in item["properties"]:
            formatted_results["definitions"].append({
                "concept": concept_info["name"],
                "definition": item["properties"]["definition"]
            })
        
        # Add relationships
        for rel in item.get("relationships", []):
            relationship = {
                "source": item["id"],
                "source_name": item["properties"].get("name", item["id"]),
                "type": rel["type"]
            }
            
            if "target" in rel:
                relationship["target"] = rel["target"]
                # Try to get the target name
                target_entity = kg_manager.get_entity(rel["target"])
                if target_entity:
                    relationship["target_name"] = target_entity["properties"].get("name", rel["target"])
                else:
                    relationship["target_name"] = rel["target"]
            
            if "source" in rel and rel["source"] != item["id"]:
                relationship["source"] = rel["source"]
                # Try to get the source name
                source_entity = kg_manager.get_entity(rel["source"])
                if source_entity:
                    relationship["source_name"] = source_entity["properties"].get("name", rel["source"])
                else:
                    relationship["source_name"] = rel["source"]
                    
            formatted_results["relationships"].append(relationship)
        
        # Add as source
        formatted_results["sources"].append({
            "type": "knowledge_graph",
            "content": f"Financial concept: {concept_info['name']} ({concept_info['category']})",
            "relevance": 0.9,  # Placeholder for relevance score
            "details": item
        })
    
    # Add query information
    formatted_results["query_info"] = kg_results.get("query_info", {})
    
    return formatted_results 