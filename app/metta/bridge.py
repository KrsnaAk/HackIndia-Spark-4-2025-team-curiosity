"""
MeTTa Bridge - Interface between Python and MeTTa's symbolic reasoning system
"""
import os
import subprocess
import logging
import tempfile
import re
from typing import List, Dict, Any, Optional, Tuple, Set

logger = logging.getLogger(__name__)

class MeTTaBridge:
    """
    Bridge between Python and MeTTa for symbolic reasoning
    This class handles executing MeTTa queries and parsing results
    """
    
    def __init__(self, knowledge_path: str = "app/metta/financial_knowledge.metta"):
        """
        Initialize MeTTa bridge
        
        Args:
            knowledge_path: Path to the MeTTa knowledge base file
        """
        self.knowledge_path = knowledge_path
        self.metta_executable = os.getenv("METTA_EXECUTABLE", "metta")
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing MeTTa bridge with knowledge at {knowledge_path}")
        
        # Check if MeTTa is installed
        try:
            self._check_metta_installation()
            self.metta_available = True
        except Exception as e:
            self.logger.warning(f"MeTTa not available: {str(e)}. Will use fallback reasoning.")
            self.metta_available = False
            
        # Initialize cached reasoning patterns for fallback mode
        self._init_fallback_reasoning()
    
    def _check_metta_installation(self):
        """Check if MeTTa is properly installed"""
        try:
            # Try to execute MeTTa with version flag
            result = subprocess.run(
                [self.metta_executable, "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            self.logger.info(f"MeTTa version: {result.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.logger.warning(f"MeTTa executable not found: {str(e)}")
            raise RuntimeError("MeTTa executable not found. Make sure OpenCog Hyperon is installed.")
    
    def query(self, query_pattern: str) -> List[Dict[str, Any]]:
        """
        Execute a MeTTa query and return results
        
        Args:
            query_pattern: MeTTa query pattern
            
        Returns:
            List of matched results
        """
        if not self.metta_available:
            return self._fallback_reasoning(query_pattern)
            
        try:
            # Write query to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.metta', delete=False) as query_file:
                query_path = query_file.name
                query_file.write(f"!(load \"{self.knowledge_path}\")\n")
                query_file.write(f"!(query {query_pattern})")
            
            # Execute MeTTa with the query file
            result = subprocess.run(
                [self.metta_executable, query_path], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Clean up temporary file
            os.unlink(query_path)
            
            # Parse results
            return self._parse_results(result.stdout)
        except Exception as e:
            self.logger.error(f"Error executing MeTTa query: {str(e)}")
            return self._fallback_reasoning(query_pattern)
    
    def _parse_results(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse MeTTa query results
        
        Args:
            output: MeTTa query output
            
        Returns:
            List of parsed results
        """
        results = []
        
        # Simple pattern matching for demonstration
        # In real implementation, this would need more sophisticated parsing
        pattern = r'\((\w+)\s+(.+?)\)'
        matches = re.findall(pattern, output)
        
        for match in matches:
            predicate, args = match
            results.append({
                "predicate": predicate,
                "arguments": args.split()
            })
        
        return results
    
    def _init_fallback_reasoning(self):
        """Initialize fallback reasoning patterns for when MeTTa is not available"""
        # Parse the knowledge file and extract rules
        try:
            with open(self.knowledge_path, 'r') as f:
                content = f.read()
                
            # Extract rules
            self.fallback_rules = {}
            
            # Simple pattern for rules: (<- (predicate args) (conclusion))
            rule_pattern = r'\(\<\-\s+\((\w+)\s+([^)]+)\)\s+\((\w+)\)\)'
            for match in re.findall(rule_pattern, content):
                predicate, args, conclusion = match
                
                if predicate not in self.fallback_rules:
                    self.fallback_rules[predicate] = []
                    
                self.fallback_rules[predicate].append({
                    "args": args.strip(),
                    "conclusion": conclusion.strip()
                })
                
            # Extract definitions
            self.fallback_definitions = {}
            
            # Pattern for definitions: (<- (definition term) "text")
            def_pattern = r'\(\<\-\s+\(definition\s+(\w+)\)\s+"([^"]+)"\)'
            for match in re.findall(def_pattern, content):
                term, definition = match
                self.fallback_definitions[term] = definition
                
            self.logger.info(f"Loaded {len(self.fallback_rules)} rule types and {len(self.fallback_definitions)} definitions for fallback reasoning")
            
        except Exception as e:
            self.logger.error(f"Error initializing fallback reasoning: {str(e)}")
            self.fallback_rules = {}
            self.fallback_definitions = {}
    
    def _fallback_reasoning(self, query_pattern: str) -> List[Dict[str, Any]]:
        """
        Fallback reasoning when MeTTa is not available
        
        Args:
            query_pattern: MeTTa query pattern
            
        Returns:
            List of matched results based on fallback rules
        """
        results = []
        
        try:
            # Simple query pattern parsing for fallback mode
            # Example: (effect-of inflation-increase ?X)
            match = re.match(r'\((\w+)\s+(\w+)(?:\s+\?(\w+))?\)', query_pattern)
            
            if not match:
                return []
                
            predicate, arg1, variable = match.groups()
            
            # Handle different query types
            if predicate == "effect-of" and variable:
                # Looking for effects of a cause
                if arg1 in self.fallback_rules.get("effect-of", []):
                    for rule in self.fallback_rules["effect-of"]:
                        if rule["args"] == arg1:
                            results.append({
                                "predicate": "effect-of",
                                "arguments": [arg1, rule["conclusion"]]
                            })
            
            elif predicate == "definition" and not variable:
                # Looking for definition of a term
                if arg1 in self.fallback_definitions:
                    results.append({
                        "predicate": "definition",
                        "arguments": [arg1, self.fallback_definitions[arg1]]
                    })
            
            elif predicate == "asset-type" and variable:
                # Looking for properties of an asset type
                for rule_type, rules in self.fallback_rules.items():
                    if rule_type == "asset-type":
                        for rule in rules:
                            if rule["args"] == arg1:
                                results.append({
                                    "predicate": "asset-type",
                                    "arguments": [arg1, rule["conclusion"]]
                                })
            
            # Add more fallback reasoning patterns as needed
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in fallback reasoning: {str(e)}")
            return []
    
    def reason_chain(self, query: str) -> Dict[str, Any]:
        """
        Perform multi-step reasoning on a natural language query
        
        Args:
            query: Natural language query
            
        Returns:
            Reasoning chain and results
        """
        # Map natural language queries to MeTTa queries
        metta_query = self._map_to_metta_query(query)
        
        if not metta_query:
            return {
                "success": False,
                "error": "Could not map query to MeTTa pattern",
                "reasoning": [],
                "conclusion": None
            }
        
        # Run the query
        results = self.query(metta_query["pattern"])
        
        # Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(metta_query, results)
        
        return {
            "success": True,
            "query": query,
            "metta_pattern": metta_query["pattern"],
            "reasoning": reasoning_chain["steps"],
            "conclusion": reasoning_chain["conclusion"]
        }
    
    def _map_to_metta_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Map natural language query to MeTTa query pattern
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary containing query type and pattern
        """
        query = query.lower().strip()
        
        # Check for inflation-related queries
        if "inflation" in query and "increase" in query:
            return {
                "type": "effect",
                "pattern": "(effect-of inflation-increase ?X)"
            }
        elif "inflation" in query and "decrease" in query:
            return {
                "type": "effect",
                "pattern": "(effect-of inflation-decrease ?X)"
            }
            
        # Check for interest rate queries
        elif "interest rate" in query and "high" in query:
            return {
                "type": "effect",
                "pattern": "(effect-of high-interest-rates ?X)"
            }
        elif "interest rate" in query and "low" in query:
            return {
                "type": "effect",
                "pattern": "(effect-of low-interest-rates ?X)"
            }
            
        # Check for recession queries
        elif "recession" in query:
            return {
                "type": "effect",
                "pattern": "(effect-of recession ?X)"
            }
        elif "economic growth" in query:
            return {
                "type": "effect",
                "pattern": "(effect-of economic-growth ?X)"
            }
            
        # Check for asset type queries
        elif "stock" in query or "stocks" in query:
            return {
                "type": "asset",
                "pattern": "(asset-type stocks ?X)"
            }
        elif "bond" in query or "bonds" in query:
            return {
                "type": "asset",
                "pattern": "(asset-type bonds ?X)"
            }
        elif "crypto" in query or "cryptocurrency" in query:
            return {
                "type": "asset",
                "pattern": "(asset-type cryptocurrency ?X)"
            }
            
        # Check for investment advice queries
        elif "conservative" in query and "investor" in query:
            return {
                "type": "advice",
                "pattern": "(suitable-for conservative-investor ?X)"
            }
        elif "moderate" in query and "investor" in query:
            return {
                "type": "advice",
                "pattern": "(suitable-for moderate-investor ?X)"
            }
        elif "aggressive" in query and "investor" in query:
            return {
                "type": "advice",
                "pattern": "(suitable-for aggressive-investor ?X)"
            }
            
        # Check for definition queries
        elif any(word in query for word in ["what is", "what are", "define", "explain"]):
            # Extract the term to define
            words = query.split()
            for i, word in enumerate(words):
                if word in ["is", "are"] and i + 1 < len(words):
                    term = words[i + 1].strip("?.,")
                    return {
                        "type": "definition",
                        "pattern": f"(definition {term})"
                    }
                    
        # Check for property queries
        elif "property" in query or "properties" in query:
            if "stock" in query or "stocks" in query:
                return {
                    "type": "property",
                    "pattern": "(property-of stocks ?X)"
                }
            elif "crypto" in query or "cryptocurrency" in query:
                return {
                    "type": "property",
                    "pattern": "(property-of crypto ?X)"
                }
                
        # Default to effect query if no specific pattern matches
        return {
            "type": "effect",
            "pattern": f"(effect-of {query} ?X)"
        }
    
    def _generate_reasoning_chain(self, query_info: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a reasoning chain from query results
        
        Args:
            query_info: Query information including type and pattern
            results: List of query results
            
        Returns:
            Dictionary containing reasoning steps and conclusion
        """
        reasoning_steps = []
        conclusion = None
        
        # Handle different query types
        if query_info["type"] == "effect":
            # For effect queries, build a chain of effects
            effects = []
            for result in results:
                if result["predicate"] == "effect-of":
                    cause, effect = result["arguments"]
                    effects.append(effect)
                    reasoning_steps.append(f"When {cause} occurs, it leads to {effect}")
                    
            if effects:
                # Extract the cause from the query pattern
                cause = query_info["pattern"].split(" ")[1].strip("()")
                # Format the conclusion with the cause and its effects
                conclusion = f"{cause} leads to several effects: {', '.join(effects)}"
            else:
                # If no effects found, try to use the query pattern
                cause = query_info["pattern"].split(" ")[1].strip("()")
                conclusion = f"{cause} can have various economic effects, including changes in consumer spending, investment patterns, and market behavior."
                
        elif query_info["type"] == "asset":
            # For asset queries, list properties
            properties = []
            for result in results:
                if result["predicate"] == "asset-type":
                    asset, property = result["arguments"]
                    properties.append(property)
                    
            if properties:
                conclusion = f"Properties of {asset}: {', '.join(properties)}"
                
        elif query_info["type"] == "advice":
            # For investment advice, list suitable properties
            suitable_properties = []
            for result in results:
                if result["predicate"] == "suitable-for":
                    investor_type, property = result["arguments"]
                    suitable_properties.append(property)
                    
            if suitable_properties:
                conclusion = f"Suitable investments for {investor_type} include assets with {', '.join(suitable_properties)}"
                
        elif query_info["type"] == "definition":
            # For definition queries, return the definition
            for result in results:
                if result["predicate"] == "definition":
                    term, definition = result["arguments"]
                    conclusion = f"{term}: {definition}"
                    break
                    
        elif query_info["type"] == "property":
            # For property queries, list properties
            properties = []
            for result in results:
                if result["predicate"] == "property-of":
                    asset, property = result["arguments"]
                    properties.append(property)
                    
            if properties:
                conclusion = f"Properties of {asset}: {', '.join(properties)}"
                
        # If no specific conclusion was reached, create a generic one based on the query type
        if not conclusion:
            if query_info["type"] == "effect":
                cause = query_info["pattern"].split(" ")[1].strip("()")
                conclusion = f"{cause} can have significant economic impacts, including changes in consumer behavior, investment patterns, and market conditions."
            elif reasoning_steps:
                conclusion = "Based on the reasoning steps above."
            else:
                conclusion = "I couldn't generate a specific conclusion for this query."
                
        return {
            "steps": reasoning_steps,
            "conclusion": conclusion
        } 