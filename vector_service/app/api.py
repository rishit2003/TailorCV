# VectorService - Internal API Endpoints
# These endpoints are called by API Gateway (not exposed to client)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.service import find_similar_chunks, search_top_k_cvs

router = APIRouter(prefix="/internal", tags=["internal"])

# Request/Response Models
class SimilarChunksRequest(BaseModel):
    jd_text: str
    min_score: Optional[float] = 0.75
    max_chunks_to_query: Optional[int] = 50

class SimilarChunksResponse(BaseModel):
    chunks: List[Dict[str, Any]]

class SearchTopKCVsRequest(BaseModel):
    jd_text: str
    top_k: Optional[int] = 3
    raw_top_k: Optional[int] = 30

class SearchTopKCVsResponse(BaseModel):
    cvs: List[Dict[str, Any]]

@router.post("/similar_chunks", response_model=SimilarChunksResponse)
async def similar_chunks_endpoint(request: SimilarChunksRequest):
    """
    Find similar CV chunks to job description
    
    Uses threshold-based approach: Returns ALL chunks with similarity score >= min_score.
    No fixed limit - uses all relevant chunks for better LLM context.
    """
    try:
        chunks = find_similar_chunks(
            request.jd_text, 
            min_score=request.min_score,
            max_chunks_to_query=request.max_chunks_to_query
        )
        return SimilarChunksResponse(chunks=chunks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar chunks: {str(e)}")

@router.post("/search_top_k_cvs", response_model=SearchTopKCVsResponse)
async def search_top_k_cvs_endpoint(request: SearchTopKCVsRequest):
    """
    Find top-k similar CVs to job description
    
    Embeds JD text, queries Pinecone for chunks, aggregates scores by cv_id,
    returns top-k CVs ranked by total similarity score.
    """
    try:
        cvs = search_top_k_cvs(
            request.jd_text, 
            top_k=request.top_k,
            raw_top_k=request.raw_top_k
        )
        return SearchTopKCVsResponse(cvs=cvs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search top K CVs: {str(e)}")

