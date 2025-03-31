from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.knowledge_graph.manager import KnowledgeGraphManager

router = APIRouter()
kg_manager = KnowledgeGraphManager()

class EntityResponse(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any]
    relationships: List[Dict[str, Any]]

class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    query_info: Dict[str, Any]

class CategoryInfo(BaseModel):
    name: str
    count: int
    description: Optional[str] = None

@router.get("/entity/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str):
    """
    Get detailed information about a specific financial entity
    """
    try:
        entity = kg_manager.get_entity(entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity with ID {entity_id} not found"
            )
        return entity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving entity: {str(e)}"
        )

@router.post("/query", response_model=QueryResponse)
async def query_graph(request: QueryRequest):
    """
    Query the financial knowledge graph with natural language
    """
    try:
        results = kg_manager.query(
            query=request.query,
            filters=request.filters,
            limit=request.limit
        )
        
        return QueryResponse(
            results=results.get("results", []),
            count=len(results.get("results", [])),
            query_info=results.get("query_info", {})
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying knowledge graph: {str(e)}"
        )

@router.get("/concepts", response_model=List[Dict[str, Any]])
async def get_concepts(
    category: Optional[str] = Query(None, description="Filter by concept category"),
    limit: int = Query(20, description="Maximum number of concepts to return")
):
    """
    Get top-level financial concepts from the knowledge graph
    """
    try:
        concepts = kg_manager.get_concepts(category=category, limit=limit)
        return concepts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving concepts: {str(e)}"
        )

@router.get("/categories", response_model=Dict[str, List[CategoryInfo]])
async def get_categories():
    """
    Get all available categories in the knowledge graph with counts
    """
    try:
        categories_with_counts = kg_manager.get_categories_with_counts()
        return {"categories": categories_with_counts}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        ) 