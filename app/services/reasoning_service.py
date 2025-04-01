"""
Reasoning Service - Uses MeTTa for symbolic reasoning and logical inference
"""
import logging
from typing import Dict, Any, List, Optional
from app.metta import MeTTaBridge

logger = logging.getLogger(__name__)

class ReasoningService:
    """
    Reasoning Service provides symbolic reasoning capabilities using MeTTa
    It replaces vector search with logical inference and deduction
    """
    
    def __init__(self):
        """Initialize the reasoning service with MeTTa bridge"""
        self.metta = MeTTaBridge()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Reasoning Service initialized with MeTTa")
    
    async def infer(self, query: str) -> Dict[str, Any]:
        """
        Infer an answer to a query using symbolic reasoning
        
        Args:
            query: The user's natural language query
            
        Returns:
            Reasoning results including conclusion and reasoning steps
        """
        try:
            # Use MeTTa to reason about the query
            reasoning_result = self.metta.reason_chain(query)
            
            if not reasoning_result["success"]:
                return {
                    "success": False,
                    "error": reasoning_result.get("error", "Unknown error in reasoning"),
                    "response": "I'm not sure how to reason about that query."
                }
            
            # Format the response
            response = self._format_reasoning_response(reasoning_result)
            
            return {
                "success": True,
                "reasoning": reasoning_result["reasoning"],
                "conclusion": reasoning_result["conclusion"],
                "response": response,
                "knowledge_graph": self._extract_knowledge_graph(reasoning_result)
            }
            
        except Exception as e:
            self.logger.error(f"Error in reasoning service: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while trying to reason about your query."
            }
    
    def _format_reasoning_response(self, reasoning_result: Dict[str, Any]) -> str:
        """
        Format reasoning result into a human-readable response
        
        Args:
            reasoning_result: The result from the reasoning process
            
        Returns:
            Formatted response string
        """
        # Extract reasoning steps and conclusion
        reasoning_steps = reasoning_result.get("reasoning", [])
        conclusion = reasoning_result.get("conclusion", "No conclusion reached.")
        
        # Build the response
        if not reasoning_steps:
            return conclusion
        
        response = "Here's my reasoning:\n\n"
        
        # Add reasoning steps with numbering
        for i, step in enumerate(reasoning_steps, 1):
            response += f"{i}. {step}\n"
        
        # Add the conclusion
        response += f"\nTherefore, {conclusion}"
        
        return response
    
    def _extract_knowledge_graph(self, reasoning_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract knowledge graph data from reasoning result
        
        Args:
            reasoning_result: The result from the reasoning process
            
        Returns:
            Knowledge graph for visualization or further processing
        """
        # Extract query type and subject
        query_info = {
            "type": reasoning_result.get("metta_pattern", "").split(" ")[0].strip("()"),
            "subject": reasoning_result.get("query", "").lower()
        }
        
        # Extract reasoning steps
        reasoning_steps = reasoning_result.get("reasoning", [])
        
        # Build a simple knowledge graph
        nodes = []
        edges = []
        
        # Add the main concept node
        main_concept = reasoning_result.get("conclusion", "").split(":")[0].strip() if ":" in reasoning_result.get("conclusion", "") else "concept"
        
        # Clean up the main concept
        main_concept = main_concept.replace("causes", "").strip()
        
        nodes.append({
            "id": main_concept,
            "label": main_concept,
            "type": "concept"
        })
        
        # Add nodes and edges from reasoning steps
        for step in reasoning_steps:
            if "leads to" in step:
                parts = step.split("leads to")
                if len(parts) == 2:
                    source = parts[0].replace("When", "").strip().rstrip(",")
                    target = parts[1].strip().rstrip(".")
                    
                    # Add nodes if they don't exist
                    if not any(node["id"] == source for node in nodes):
                        nodes.append({
                            "id": source,
                            "label": source,
                            "type": "cause"
                        })
                    
                    if not any(node["id"] == target for node in nodes):
                        nodes.append({
                            "id": target,
                            "label": target,
                            "type": "effect"
                        })
                    
                    # Add edge
                    edges.append({
                        "source": source,
                        "target": target,
                        "type": "leads_to"
                    })
        
        # If no edges were created but we have properties, create property edges
        if not edges and "Properties of" in reasoning_result.get("conclusion", ""):
            subject, properties_text = reasoning_result.get("conclusion", "").split(":", 1)
            subject = subject.replace("Properties of", "").strip()
            
            # Add subject node if not exists
            if not any(node["id"] == subject for node in nodes):
                nodes.append({
                    "id": subject,
                    "label": subject,
                    "type": "concept"
                })
                
            # Add property nodes and edges
            for prop in properties_text.split(","):
                prop = prop.strip()
                if prop:
                    # Add property node
                    if not any(node["id"] == prop for node in nodes):
                        nodes.append({
                            "id": prop,
                            "label": prop,
                            "type": "property"
                        })
                    
                    # Add edge
                    edges.append({
                        "source": subject,
                        "target": prop,
                        "type": "has_property"
                    })
        
        # Return the knowledge graph if it has nodes
        if nodes:
            return {
                "nodes": nodes,
                "edges": edges,
                "query": query_info
            }
        
        return None 