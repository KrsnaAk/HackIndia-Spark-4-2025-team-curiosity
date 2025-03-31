"""
Test script for vector database functionality
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.vector_db import VectorDatabase

def test_vector_db():
    """Test the vector database functionality"""
    logger.info("Creating vector database...")
    db = VectorDatabase(collection_name="test")
    
    # Add some test documents
    texts = [
        "SingularityNET is a decentralized AI marketplace",
        "Fetch.ai is developing autonomous agents for machine learning",
        "Ocean Protocol enables data sharing with privacy protection",
        "Ethereum is a decentralized blockchain platform for smart contracts",
        "Solana is a high-performance blockchain with fast transaction speeds"
    ]
    
    metadatas = [
        {"project": "SingularityNET", "symbol": "AGIX", "category": "AI"},
        {"project": "Fetch.ai", "symbol": "FET", "category": "AI"},
        {"project": "Ocean Protocol", "symbol": "OCEAN", "category": "Data"},
        {"project": "Ethereum", "symbol": "ETH", "category": "Layer 1"},
        {"project": "Solana", "symbol": "SOL", "category": "Layer 1"}
    ]
    
    logger.info("Adding documents to vector database...")
    db.add_documents(texts, metadatas)
    
    # Test search
    query = "What is SingularityNET?"
    logger.info(f"Searching for: {query}")
    results = db.search(query, top_k=2)
    
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}:")
        logger.info(f"Text: {result['text']}")
        logger.info(f"Metadata: {result['metadata']}")
        logger.info(f"Score: {result['score']}")
    
    # Test another query
    query2 = "Tell me about blockchain platforms"
    logger.info(f"Searching for: {query2}")
    results2 = db.search(query2, top_k=2)
    
    for i, result in enumerate(results2):
        logger.info(f"Result {i+1}:")
        logger.info(f"Text: {result['text']}")
        logger.info(f"Metadata: {result['metadata']}")
        logger.info(f"Score: {result['score']}")
    
    logger.info("Vector database test completed")

if __name__ == "__main__":
    test_vector_db() 