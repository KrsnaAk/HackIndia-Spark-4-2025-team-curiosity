"""
Graph RAG (Retrieval Augmented Generation) implementation
Combines vector search and graph-based knowledge for enhanced query responses
"""

import logging
from typing import Dict, List, Any, Optional
import networkx as nx
from app.utils.knowledge_graph import MeTTaKnowledgeGraph
from app.utils.vector_db import VectorDatabase

logger = logging.getLogger(__name__)

class GraphRAG:
    """
    Graph RAG implementation that combines Vector Database with Knowledge Graph
    for enhanced knowledge retrieval and context-aware responses
    """
    
    def __init__(self, vector_db: VectorDatabase, knowledge_graph: MeTTaKnowledgeGraph):
        """
        Initialize GraphRAG with vector database and knowledge graph
        
        Args:
            vector_db: Vector database for semantic search
            knowledge_graph: Knowledge graph for structured data and relationships
        """
        self.vector_db = vector_db
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(__name__)
        self.logger.info("GraphRAG initialized")
    
    def query(self, query: str, top_k: int = 5, max_hops: int = 2, entity_types: List[str] = None) -> Dict[str, Any]:
        """
        Execute a Graph RAG query
        
        Args:
            query: User query
            top_k: Number of top vector search results to consider
            max_hops: Maximum number of hops in the knowledge graph
            entity_types: Entity types to consider in the knowledge graph
            
        Returns:
            Combined results from vector search and knowledge graph
        """
        self.logger.info(f"GraphRAG query: {query}")
        
        # Step 1: Perform vector search
        vector_results = self.vector_db.search(query, top_k=top_k)
        
        # Step 2: Extract entities from vector search results
        extracted_entities = set()
        for result in vector_results:
            metadata = result.get('metadata', {})
            if 'symbol' in metadata:
                extracted_entities.add(metadata['symbol'])
            if 'name' in metadata:
                # Clean name for graph search
                name = metadata['name'].replace(' ', '_')
                extracted_entities.add(name)
        
        self.logger.info(f"Extracted entities from vector search: {extracted_entities}")
        
        if not extracted_entities:
            return {
                "vector_results": vector_results,
                "graph_results": [],
                "combined_results": vector_results,
                "rag_context": self._format_vector_results(vector_results)
            }
        
        # Step 3: Query the knowledge graph with these entities
        graph_results = self.knowledge_graph.query(
            " ".join(extracted_entities), 
            entity_types=entity_types,
            max_hops=max_hops
        ).get("results", [])
        
        # Step 4: Combine results (graph knowledge enriches vector results)
        combined_results = self._combine_results(vector_results, graph_results)
        
        # Step 5: Format results for RAG context
        rag_context = self._format_combined_results(combined_results)
        
        return {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "combined_results": combined_results,
            "rag_context": rag_context
        }
    
    def _combine_results(self, vector_results: List[Dict[str, Any]], graph_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine vector search results with knowledge graph results
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from knowledge graph
            
        Returns:
            Combined results with graph knowledge enhancing vector results
        """
        combined_results = []
        
        # Process each vector result
        for vec_result in vector_results:
            # Create enriched result
            enriched_result = {**vec_result}
            
            # Find related graph data
            metadata = vec_result.get('metadata', {})
            symbol = metadata.get('symbol', '')
            name = metadata.get('name', '').replace(' ', '_')
            
            # Find matches in graph results
            graph_matches = []
            for graph_result in graph_results:
                graph_id = graph_result.get('id', '')
                if (symbol and graph_id == symbol) or (name and graph_id == name):
                    graph_matches.append(graph_result)
            
            if graph_matches:
                enriched_result['graph_data'] = graph_matches
                
                # Add relationship information
                relationships = []
                for graph_match in graph_matches:
                    # Extract relationships from graph data
                    node_data = graph_match.get('data', {})
                    
                    # Add any relationship data found in the node
                    for key, value in node_data.items():
                        if key not in ['type', 'id'] and value:
                            relationships.append({
                                'type': key,
                                'value': value
                            })
                
                if relationships:
                    enriched_result['relationships'] = relationships
            
            combined_results.append(enriched_result)
        
        # Add high-relevance graph results that didn't match any vector result
        matched_ids = set()
        for result in combined_results:
            if 'graph_data' in result:
                for graph_data in result['graph_data']:
                    matched_ids.add(graph_data.get('id', ''))
        
        # Include unmatched graph results that have distance=0 (direct matches)
        for graph_result in graph_results:
            if graph_result.get('id', '') not in matched_ids and graph_result.get('distance', 1) == 0:
                # Create a synthetic result
                combined_results.append({
                    'text': f"Information about {graph_result.get('id', '')}: {graph_result.get('data', {}).get('description', 'No description available')}",
                    'score': 0.75,  # Reasonable score for direct graph matches
                    'metadata': {
                        'symbol': graph_result.get('id', ''),
                        'source': 'knowledge_graph'
                    },
                    'graph_data': [graph_result]
                })
        
        # Sort by score
        combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return combined_results
    
    def _format_vector_results(self, vector_results: List[Dict[str, Any]]) -> str:
        """Format vector results for RAG context"""
        if not vector_results:
            return ""
        
        context = "Relevant information:\n\n"
        
        for i, result in enumerate(vector_results, 1):
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            symbol = metadata.get('symbol', '')
            name = metadata.get('name', symbol)
            
            if name and text:
                context += f"{i}. {name} ({symbol}): {text}\n\n"
            elif text:
                context += f"{i}. {text}\n\n"
        
        return context
    
    def _format_combined_results(self, combined_results: List[Dict[str, Any]]) -> str:
        """Format combined results for RAG context"""
        if not combined_results:
            return ""
        
        context = "Relevant information including graph relationships:\n\n"
        
        for i, result in enumerate(combined_results, 1):
            # Basic info
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            symbol = metadata.get('symbol', '')
            name = metadata.get('name', symbol)
            
            # Graph data
            graph_data = result.get('graph_data', [])
            relationships = result.get('relationships', [])
            
            if name:
                context += f"{i}. {name} ({symbol}):\n"
            else:
                context += f"{i}. Information:\n"
            
            if text:
                context += f"   Description: {text}\n"
            
            # Add graph knowledge
            if graph_data:
                for gd in graph_data:
                    gd_data = gd.get('data', {})
                    if 'category' in gd_data:
                        context += f"   Category: {gd_data['category']}\n"
                    if 'market_cap' in gd_data:
                        context += f"   Market Cap: {gd_data['market_cap']}\n"
                    if 'funding' in gd_data:
                        context += f"   Funding: {gd_data['funding']}\n"
            
            # Add relationships
            if relationships:
                context += "   Relationships:\n"
                for rel in relationships:
                    rel_type = rel.get('type', '')
                    rel_value = rel.get('value', '')
                    if rel_type and rel_value:
                        context += f"      - {rel_type}: {rel_value}\n"
            
            context += "\n"
        
        return context
    
    def enhance_prompt(self, query: str, rag_results: Dict[str, Any]) -> str:
        """
        Enhance a prompt for an LLM with RAG context
        
        Args:
            query: Original user query
            rag_results: Results from RAG query
            
        Returns:
            Enhanced prompt with RAG context
        """
        rag_context = rag_results.get("rag_context", "")
        
        if not rag_context:
            return query
        
        # Create enhanced prompt with retrieved context
        enhanced_prompt = f"""
Please answer the following question based on the retrieved context:

RETRIEVED CONTEXT:
{rag_context}

USER QUESTION: {query}

ANSWER:
"""
        
        return enhanced_prompt
    
    def crypto_relationships_query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Specialized query for crypto relationships
        
        Args:
            query: User query about cryptocurrency relationships
            top_k: Number of top vector search results to consider
            
        Returns:
            Graph RAG results focused on relationships
        """
        results = self.query(
            query, 
            top_k=top_k,
            max_hops=2,
            entity_types=["Cryptocurrency"]
        )
        
        # Extract relationship information
        relationship_context = "Relationships between cryptocurrencies:\n\n"
        
        combined_results = results.get("combined_results", [])
        for result in combined_results:
            graph_data = result.get("graph_data", [])
            
            for gd in graph_data:
                node_id = gd.get("id", "")
                
                # Get all relationships for this node
                if node_id:
                    entity_data = self.knowledge_graph.get_entity(node_id)
                    if entity_data:
                        relationships = entity_data.get("relationships", [])
                        
                        if relationships:
                            relationship_context += f"{node_id} relationships:\n"
                            
                            for rel in relationships:
                                predicate = rel.get("predicate", "")
                                obj = rel.get("object", "")
                                weight = rel.get("weight", 1.0)
                                
                                if predicate and obj:
                                    relationship_context += f"  - {predicate} {obj} (strength: {weight:.1f})\n"
                            
                            relationship_context += "\n"
        
        # Add relationship context to results
        results["relationship_context"] = relationship_context
        
        # Enhance RAG context with relationship information
        if relationship_context and relationship_context != "Relationships between cryptocurrencies:\n\n":
            results["rag_context"] += "\n\n" + relationship_context
        
        return results 