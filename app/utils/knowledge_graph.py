"""
MeTTa-inspired Knowledge Graph for financial data
Implements a semantic knowledge graph for structured reasoning and retrieval
"""

import logging
import networkx as nx
import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import RDFS, XSD
import json
from typing import Dict, List, Any, Optional, Tuple, Set
import re

logger = logging.getLogger(__name__)

# Define namespaces
FINANCE = Namespace("http://finance.org/ontology/")
CRYPTO = Namespace("http://crypto.org/ontology/")
ENTITY = Namespace("http://entity.org/")

class MeTTaKnowledgeGraph:
    """
    MeTTa-inspired Knowledge Graph for financial data with Graph RAG capabilities
    """
    
    def __init__(self):
        """Initialize the knowledge graph"""
        # RDF Graph for semantic web compatibility
        self.rdf_graph = Graph()
        self.rdf_graph.bind("finance", FINANCE)
        self.rdf_graph.bind("crypto", CRYPTO)
        self.rdf_graph.bind("entity", ENTITY)
        
        # NetworkX graph for graph algorithms and traversal
        self.graph = nx.DiGraph()
        
        # Initialize the knowledge graph with basic financial ontology
        self._init_financial_ontology()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("MeTTa Knowledge Graph initialized")
    
    def _init_financial_ontology(self):
        """Initialize the financial ontology"""
        # Define financial asset classes
        self.add_concept_hierarchy("Asset", [
            "FinancialAsset", 
            "RealAsset"
        ])
        
        self.add_concept_hierarchy("FinancialAsset", [
            "Equity", 
            "FixedIncome",
            "Cryptocurrency",
            "Derivative", 
            "Cash"
        ])
        
        self.add_concept_hierarchy("Cryptocurrency", [
            "Layer1",
            "Layer2",
            "DeFi",
            "StableCoin",
            "PrivacyCoin",
            "MemeCoin",
            "UtilityToken",
            "NFT",
            "GameFi"
        ])
        
        # Define relationships
        self.add_predicate("has_price")
        self.add_predicate("traded_on")
        self.add_predicate("has_market_cap")
        self.add_predicate("founded_by")
        self.add_predicate("launched_in")
        self.add_predicate("based_on")
        self.add_predicate("backed_by")
        self.add_predicate("competes_with")
        self.add_predicate("invested_in")
        self.add_predicate("regulated_by")
        
        # Add common financial concepts
        self.add_predicate("has_definition")
        
        financial_concepts = {
            "Inflation": "A general increase in prices and fall in the purchasing value of money.",
            "Deflation": "A general decrease in prices and increase in the purchasing value of money.",
            "Bull_Market": "A market in which share prices are rising, encouraging buying.",
            "Bear_Market": "A market in which prices are falling, encouraging selling.",
            "Volatility": "A statistical measure of the dispersion of returns for a given security or market index.",
            "Liquidity": "The degree to which an asset can be quickly bought or sold without affecting its price.",
            "Diversification": "The practice of spreading investments among different assets to reduce risk.",
            "Yield": "The income returned on an investment, such as interest or dividends."
        }
        
        for concept, definition in financial_concepts.items():
            concept_uri = FINANCE[concept]
            self.rdf_graph.add((concept_uri, RDF.type, FINANCE.Concept))
            self.rdf_graph.add((concept_uri, FINANCE.has_definition, Literal(definition)))
            self.graph.add_node(str(concept_uri), type="Concept", definition=definition)
    
    def add_concept_hierarchy(self, parent: str, children: List[str]):
        """Add a concept hierarchy to the knowledge graph"""
        parent_uri = FINANCE[parent]
        self.rdf_graph.add((parent_uri, RDF.type, RDFS.Class))
        self.graph.add_node(str(parent_uri), type="Class")
        
        for child in children:
            child_uri = FINANCE[child]
            self.rdf_graph.add((child_uri, RDF.type, RDFS.Class))
            self.rdf_graph.add((child_uri, RDFS.subClassOf, parent_uri))
            self.graph.add_node(str(child_uri), type="Class")
            self.graph.add_edge(str(parent_uri), str(child_uri), relation="subClassOf")
    
    def add_predicate(self, predicate: str):
        """Add a predicate to the knowledge graph"""
        predicate_uri = FINANCE[predicate]
        self.rdf_graph.add((predicate_uri, RDF.type, RDF.Property))
        self.graph.add_node(str(predicate_uri), type="Property")
    
    def add_entity(self, entity_id: str, entity_type: str, attributes: Dict[str, Any] = None):
        """Add an entity to the knowledge graph"""
        entity_uri = ENTITY[entity_id]
        type_uri = FINANCE[entity_type]
        
        self.rdf_graph.add((entity_uri, RDF.type, type_uri))
        self.graph.add_node(str(entity_uri), type=entity_type, **attributes or {})
        
        # Add attributes to RDF graph
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, (str, int, float, bool)):
                    predicate_uri = FINANCE[key]
                    self.rdf_graph.add((entity_uri, predicate_uri, Literal(value)))
    
    def add_relationship(self, subject_id: str, predicate: str, object_id: str, weight: float = 1.0, metadata: Dict[str, Any] = None):
        """Add a relationship between entities to the knowledge graph"""
        subject_uri = ENTITY[subject_id]
        predicate_uri = FINANCE[predicate]
        object_uri = ENTITY[object_id]
        
        self.rdf_graph.add((subject_uri, predicate_uri, object_uri))
        
        edge_attrs = {"relation": predicate, "weight": weight}
        if metadata:
            edge_attrs.update(metadata)
        
        self.graph.add_edge(str(subject_uri), str(object_uri), **edge_attrs)
    
    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get an entity from the knowledge graph"""
        entity_uri = ENTITY[entity_id]
        
        if str(entity_uri) not in self.graph:
            return None
        
        entity_data = {
            "id": entity_id,
            "type": self.graph.nodes[str(entity_uri)].get("type"),
            "attributes": {}
        }
        
        # Get attributes from RDF graph
        for s, p, o in self.rdf_graph.triples((entity_uri, None, None)):
            if isinstance(o, Literal):
                pred_name = p.split("/")[-1]
                entity_data["attributes"][pred_name] = o.value
        
        # Get relationships
        entity_data["relationships"] = []
        for _, obj, data in self.graph.out_edges(str(entity_uri), data=True):
            obj_id = obj.split("/")[-1]
            entity_data["relationships"].append({
                "predicate": data.get("relation"),
                "object": obj_id,
                "weight": data.get("weight", 1.0)
            })
        
        return entity_data
    
    def query(self, query: str, entity_types: List[str] = None, max_hops: int = 2) -> Dict[str, Any]:
        """
        Query the knowledge graph using a natural language query
        Implements Graph RAG (Retrieval Augmented Generation) using graph traversal
        """
        self.logger.info(f"Querying knowledge graph with: {query}")
        
        # Extract entities and predicates from the query
        extracted_entities = self._extract_entities_from_query(query)
        self.logger.info(f"Extracted entities: {extracted_entities}")
        
        if not extracted_entities:
            return {"results": [], "message": "No entities found in query"}
        
        # Find matching entities in the graph
        matched_entities = []
        for entity in extracted_entities:
            entity_uri = ENTITY[entity]
            if str(entity_uri) in self.graph:
                matched_entities.append(entity)
        
        if not matched_entities:
            return {"results": [], "message": "No matching entities found in knowledge graph"}
        
        # Extract content from subgraph around matched entities
        subgraph_data = self._extract_subgraph(matched_entities, max_hops, entity_types)
        
        return {
            "results": subgraph_data,
            "matched_entities": matched_entities,
            "query": query
        }
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """Extract potential entities from a natural language query"""
        # Simple extraction based on capitalized words (could be improved with NLP)
        candidates = re.findall(r'\b[A-Z][a-zA-Z]*\b', query)
        
        # Also look for specific patterns like $BTC or #Bitcoin
        symbols = re.findall(r'[$#]([A-Za-z0-9]+)', query)
        
        # Add potential cryptocurrency tickers (all caps 2-5 letters)
        tickers = re.findall(r'\b[A-Z]{2,5}\b', query)
        
        return list(set(candidates + symbols + tickers))
    
    def _extract_subgraph(self, entity_ids: List[str], max_hops: int, entity_types: List[str] = None) -> List[Dict[str, Any]]:
        """Extract a subgraph around specified entities using graph traversal"""
        result = []
        visited = set()
        
        for entity_id in entity_ids:
            entity_uri = str(ENTITY[entity_id])
            if entity_uri not in self.graph:
                continue
            
            # Use BFS to traverse the graph up to max_hops
            queue = [(entity_uri, 0)]  # (node, distance)
            while queue:
                node, distance = queue.pop(0)
                
                if node in visited or distance > max_hops:
                    continue
                
                visited.add(node)
                
                # Get node data
                node_data = dict(self.graph.nodes[node])
                
                # Filter by entity type if specified
                if entity_types and node_data.get("type") not in entity_types:
                    continue
                
                # Add to result
                node_id = node.split("/")[-1]
                result.append({
                    "id": node_id,
                    "type": node_data.get("type"),
                    "distance": distance,
                    "data": node_data
                })
                
                # Add neighbors to queue
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        queue.append((neighbor, distance + 1))
        
        return result
    
    def populate_from_crypto_data(self, crypto_data: Dict[str, Dict[str, Any]]):
        """Populate the knowledge graph with cryptocurrency data"""
        for symbol, data in crypto_data.items():
            # Add the cryptocurrency entity
            self.add_entity(
                symbol, 
                "Cryptocurrency", 
                {
                    "name": data.get("name", symbol),
                    "symbol": symbol,
                    "category": data.get("category", "Unknown"),
                    "description": data.get("description", ""),
                    "market_cap": data.get("mcap", "Unknown"),
                    "funding": data.get("funding", "Unknown"),
                }
            )
            
            # Add relationships based on the category
            category = data.get("category", "").lower()
            
            if "layer 1" in category:
                self.add_relationship(symbol, "instanceOf", "Layer1")
            elif "layer 2" in category:
                self.add_relationship(symbol, "instanceOf", "Layer2")
            elif "defi" in category:
                self.add_relationship(symbol, "instanceOf", "DeFi")
            elif "agi" in category or "ai" in category:
                self.add_relationship(symbol, "instanceOf", "AI")
            
            # Add competitor relationships based on categories
            for other_symbol, other_data in crypto_data.items():
                if symbol != other_symbol and other_data.get("category") == data.get("category"):
                    self.add_relationship(symbol, "competes_with", other_symbol, weight=0.5)
    
    def load_from_json(self, json_file: str):
        """Load knowledge graph data from a JSON file"""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Load entities
            for entity in data.get("entities", []):
                self.add_entity(
                    entity["id"],
                    entity["type"],
                    entity.get("attributes", {})
                )
            
            # Load relationships
            for rel in data.get("relationships", []):
                self.add_relationship(
                    rel["subject"],
                    rel["predicate"],
                    rel["object"],
                    rel.get("weight", 1.0),
                    rel.get("metadata", {})
                )
            
            self.logger.info(f"Successfully loaded knowledge graph from {json_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge graph from {json_file}: {str(e)}")
    
    def save_to_json(self, json_file: str):
        """Save knowledge graph data to a JSON file"""
        data = {
            "entities": [],
            "relationships": []
        }
        
        # Extract entities
        for node, attrs in self.graph.nodes(data=True):
            if node.startswith(str(ENTITY)):
                entity_id = node.split("/")[-1]
                data["entities"].append({
                    "id": entity_id,
                    "type": attrs.get("type", "Unknown"),
                    "attributes": {k: v for k, v in attrs.items() if k != "type"}
                })
        
        # Extract relationships
        for src, dst, attrs in self.graph.edges(data=True):
            if src.startswith(str(ENTITY)) and dst.startswith(str(ENTITY)):
                src_id = src.split("/")[-1]
                dst_id = dst.split("/")[-1]
                data["relationships"].append({
                    "subject": src_id,
                    "predicate": attrs.get("relation", "unknown"),
                    "object": dst_id,
                    "weight": attrs.get("weight", 1.0)
                })
        
        try:
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Successfully saved knowledge graph to {json_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving knowledge graph to {json_file}: {str(e)}")
    
    def export_rdf(self, output_file: str, format: str = "turtle"):
        """Export the knowledge graph to RDF format"""
        try:
            self.rdf_graph.serialize(destination=output_file, format=format)
            self.logger.info(f"Successfully exported knowledge graph to {output_file} in {format} format")
        except Exception as e:
            self.logger.error(f"Error exporting knowledge graph to {output_file}: {str(e)}")
    
    # Graph RAG specific methods
    def semantic_graph_search(self, query: str, vector_db, top_k: int = 3) -> Dict[str, Any]:
        """
        Graph RAG (Retrieval Augmented Generation) implementation
        Combines vector search with graph-based knowledge retrieval
        """
        # Step 1: Perform vector search to find initial entities
        vector_results = vector_db.search(query, top_k=top_k)
        
        # Step 2: Extract entities from vector search results
        extracted_entities = set()
        for result in vector_results:
            metadata = result.get('metadata', {})
            if 'symbol' in metadata:
                extracted_entities.add(metadata['symbol'])
        
        if not extracted_entities:
            return {
                "vector_results": vector_results,
                "graph_results": [],
                "combined_results": vector_results
            }
        
        # Step 3: Query the knowledge graph with these entities
        graph_results = self.query(
            " ".join(extracted_entities), 
            entity_types=["Cryptocurrency"], 
            max_hops=2
        ).get("results", [])
        
        # Step 4: Combine results (graph knowledge enriches vector results)
        combined_results = []
        for vec_result in vector_results:
            # Create enriched result
            enriched_result = {**vec_result}
            
            # Find related graph data
            metadata = vec_result.get('metadata', {})
            symbol = metadata.get('symbol', '')
            
            if symbol:
                # Find this entity in graph results
                for graph_result in graph_results:
                    if graph_result.get('id') == symbol:
                        # Add graph-based knowledge
                        enriched_result['graph_data'] = graph_result
                        break
            
            combined_results.append(enriched_result)
        
        return {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "combined_results": combined_results
        } 