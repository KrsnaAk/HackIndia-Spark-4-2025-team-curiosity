"""
Vector Database for storing and retrieving embeddings
"""

import os
import json
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class VectorDatabase:
    """
    Simple vector database using sentence transformers
    Stores embeddings in memory with persistence to disk
    """
    
    def __init__(self, collection_name: str = "default", embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector database with the specified model
        
        Args:
            collection_name: Name of the collection
            embedding_model: Name of the sentence transformer model to use
        """
        self.collection_name = collection_name
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_db")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load or initialize the database
        self.db_file = os.path.join(self.data_dir, f"{collection_name}.json")
        self.documents = []
        self.embeddings = []
        self.load_from_disk()
        
        # Initialize the embedding model
        try:
            self.model = SentenceTransformer(embedding_model)
            logger.info(f"Initialized vector database with model: {embedding_model}")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
    
    def load_from_disk(self):
        """
        Load the database from disk if it exists
        """
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    # Convert embeddings from list to numpy array
                    self.embeddings = [np.array(emb) for emb in data.get('embeddings', [])]
                logger.info(f"Loaded {len(self.documents)} documents from {self.db_file}")
            except Exception as e:
                logger.error(f"Error loading vector database from disk: {str(e)}")
                self.documents = []
                self.embeddings = []
    
    def save_to_disk(self):
        """
        Save the database to disk
        """
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                # Convert numpy arrays to lists for JSON serialization
                embeddings_list = [emb.tolist() for emb in self.embeddings]
                json.dump({
                    'documents': self.documents,
                    'embeddings': embeddings_list
                }, f)
            logger.info(f"Saved {len(self.documents)} documents to {self.db_file}")
        except Exception as e:
            logger.error(f"Error saving vector database to disk: {str(e)}")
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Add documents to the database
        
        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dictionaries
        """
        if not texts:
            return
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # Create embeddings for the texts
        try:
            new_embeddings = self.model.encode(texts)
            
            # Add documents and embeddings to the database
            for i, (text, metadata, embedding) in enumerate(zip(texts, metadatas, new_embeddings)):
                self.documents.append({
                    'text': text,
                    'metadata': metadata,
                    'id': len(self.documents) + i
                })
                self.embeddings.append(embedding)
            
            # Save to disk
            self.save_to_disk()
            logger.info(f"Added {len(texts)} documents to the database")
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {str(e)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the database
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of documents with similarity scores
        """
        if not self.embeddings:
            logger.warning("No documents in the database to search")
            return []
        
        try:
            # Create embedding for the query
            query_embedding = self.model.encode(query)
            
            # Calculate cosine similarity
            similarities = []
            for doc_embedding in self.embeddings:
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                similarities.append(similarity)
            
            # Get top k results
            if not similarities:
                return []
                
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                doc = self.documents[idx]
                results.append({
                    'id': doc['id'],
                    'text': doc['text'],
                    'metadata': doc['metadata'],
                    'score': float(similarities[idx])
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching vector database: {str(e)}")
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity score
        """
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID
        
        Args:
            doc_id: The document ID
            
        Returns:
            The document or None if not found
        """
        for doc in self.documents:
            if doc['id'] == doc_id:
                return doc
        return None
    
    @classmethod
    def get_or_create(cls, collection_name: str):
        """
        Get an existing vector database or create a new one
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            VectorDatabase instance
        """
        return cls(collection_name) 