"""
Chat models for request and response
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union

class ChatRequest(BaseModel):
    """
    Model for chat request
    """
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """
    Model for chat response
    """
    response: str
    additional_data: Optional[Dict[str, Any]] = None
    knowledge_graph: Optional[Dict[str, Any]] = None 