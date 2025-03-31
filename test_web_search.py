"""
Test script for web search functionality
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.web_search import WebSearchClient

def test_web_search():
    """Test the web search functionality"""
    logger.info("Creating web search client...")
    web_search = WebSearchClient()
    
    # Test Wikipedia search
    query = "SingularityNET AGI"
    logger.info(f"Searching Wikipedia for: {query}")
    results = web_search.search_wikipedia(query, limit=1)
    
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}:")
        logger.info(f"Title: {result['title']}")
        logger.info(f"URL: {result['url']}")
        logger.info(f"Content snippet: {result['content'][:150]}...")
    
    # Test project docs search
    project = "singularitynet"
    logger.info(f"Searching docs for project: {project}")
    doc_results = web_search.search_docs(project, "What is SingularityNET?")
    
    for i, result in enumerate(doc_results):
        logger.info(f"Result {i+1}:")
        logger.info(f"Title: {result['title']}")
        logger.info(f"URL: {result['url']}")
        logger.info(f"Content: {result['content']}")
    
    # Test combined search
    combined_query = "What is SingularityNET and how does it work?"
    logger.info(f"Performing combined search for: {combined_query}")
    combined_results = web_search.search(combined_query, context="blockchain AI")
    
    logger.info(f"Found {len(combined_results.get('results', []))} results")
    for i, result in enumerate(combined_results.get('results', [])):
        logger.info(f"Result {i+1}:")
        logger.info(f"Title: {result.get('title', 'No title')}")
        logger.info(f"Source: {result.get('source', 'Unknown')}")
        logger.info(f"URL: {result.get('url', 'No URL')}")
        content = result.get('content', 'No content')
        logger.info(f"Content snippet: {content[:150]}..." if len(content) > 150 else f"Content: {content}")
    
    logger.info("Web search test completed")

if __name__ == "__main__":
    test_web_search() 