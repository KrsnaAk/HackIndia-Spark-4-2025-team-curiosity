"""
Web search utility for retrieving information from the web
"""

import logging
import json
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class WebSearchClient:
    """
    Client for searching the web for information
    
    This is a simple implementation that uses DuckDuckGo or Wikipedia
    to find information that's not in our knowledge base.
    """
    
    def __init__(self):
        """
        Initialize the web search client
        """
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def search_wikipedia(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for information
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Wikipedia search API
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": limit
            }
            
            response = requests.get(search_url, params=search_params, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            
            data = response.json()
            search_results = []
            
            if "query" in data and "search" in data["query"]:
                for result in data["query"]["search"]:
                    # Get page content
                    content_url = "https://en.wikipedia.org/w/api.php"
                    content_params = {
                        "action": "query",
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "pageids": result["pageid"],
                        "format": "json"
                    }
                    
                    content_response = requests.get(content_url, params=content_params, headers={"User-Agent": self.user_agent})
                    content_response.raise_for_status()
                    
                    content_data = content_response.json()
                    
                    if "query" in content_data and "pages" in content_data["query"]:
                        page_id = str(result["pageid"])
                        if page_id in content_data["query"]["pages"]:
                            page = content_data["query"]["pages"][page_id]
                            extract = page.get("extract", "")
                            
                            search_results.append({
                                "title": result["title"],
                                "snippet": result.get("snippet", ""),
                                "content": extract,
                                "source": "wikipedia",
                                "url": f"https://en.wikipedia.org/?curid={result['pageid']}"
                            })
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {str(e)}")
            return []
    
    def search_docs(self, project: str, query: str) -> List[Dict[str, Any]]:
        """
        Search project documentation 
        
        Args:
            project: Project name (e.g., "singularitynet", "fetchai")
            query: Search query
            
        Returns:
            List of search results
        """
        # Map of projects to their documentation URLs
        docs_map = {
            "singularitynet": "https://docs.singularitynet.io",
            "fetchai": "https://docs.fetch.ai",
            "ocean": "https://docs.oceanprotocol.com",
            "sui": "https://docs.sui.io",
            "aptos": "https://aptos.dev",
        }
        
        if project.lower() not in docs_map:
            logger.warning(f"No documentation available for project: {project}")
            return []
        
        # Since we can't easily scrape all docs without setting up a more complex system,
        # return a response with links to the relevant documentation
        base_url = docs_map.get(project.lower())
        
        return [{
            "title": f"{project.title()} Documentation",
            "content": f"For detailed information about {project.title()}, please refer to their official documentation.",
            "source": "project_docs",
            "url": base_url
        }]
    
    def search(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for information about a topic
        
        Args:
            query: The search query
            context: Optional context to help focus the search (e.g., "crypto", "blockchain")
            
        Returns:
            Dictionary with search results
        """
        results = []
        
        # Add context to the query if provided
        search_query = query
        if context:
            search_query = f"{query} {context}"
        
        # Search Wikipedia
        wiki_results = self.search_wikipedia(search_query)
        results.extend(wiki_results)
        
        # Check if this is about a specific project
        project_keywords = ["singularitynet", "agix", "fetchai", "fet", "ocean", "sui", "aptos"]
        detected_project = None
        
        for keyword in project_keywords:
            if keyword.lower() in query.lower():
                detected_project = keyword
                break
        
        # If a project was detected, search its documentation
        if detected_project:
            doc_results = self.search_docs(detected_project, query)
            results.extend(doc_results)
        
        return {
            "query": query,
            "results": results,
            "source": "web_search"
        }
        
    def combined_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a combined search using multiple sources and return a flattened list of results
        
        Args:
            query: The search query
            
        Returns:
            List of search results from all sources
        """
        logger.info(f"Performing combined search for: {query}")
        
        # List to store all results
        all_results = []
        
        # Search Wikipedia
        wiki_results = self.search_wikipedia(query)
        all_results.extend(wiki_results)
        
        # Check if query is about a specific project
        project_keywords = {
            "singularitynet": ["singularitynet", "agix", "agi network"],
            "fetchai": ["fetchai", "fetch.ai", "fet"],
            "ocean": ["ocean protocol", "ocean"],
            "sui": ["sui blockchain", "sui"],
            "aptos": ["aptos blockchain", "aptos"],
            "ethereum": ["ethereum", "eth"],
            "solana": ["solana", "sol"],
            "bitcoin": ["bitcoin", "btc"]
        }
        
        # Check for project mentions in the query
        query_lower = query.lower()
        for project, keywords in project_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                doc_results = self.search_docs(project, query)
                all_results.extend(doc_results)
        
        # Add context for cryptocurrency/blockchain queries
        if any(term in query_lower for term in ["crypto", "blockchain", "token", "defi", "nft", "web3"]):
            crypto_results = self.search(query, context="cryptocurrency blockchain")
            if crypto_results and "results" in crypto_results:
                # Add any results we don't already have
                existing_urls = [r.get("url") for r in all_results]
                for result in crypto_results["results"]:
                    if result.get("url") not in existing_urls:
                        all_results.append(result)
        
        logger.info(f"Found {len(all_results)} results in combined search")
        return all_results 