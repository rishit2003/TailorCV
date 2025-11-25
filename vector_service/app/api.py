# VectorService - Internal API Endpoints
# These endpoints are called by API Gateway (not exposed to client)
#
# Internal Endpoints:
# 1. POST /internal/similar_chunks - Find similar CV chunks to JD
#    Input: {jd_text}
#    Output: {chunks: [{text, section, cv_id, score}, ...]}
#    Flow:
#      - Embed jd_text using BGE-large model
#      - Query Pinecone for top similar vectors
#      - Return chunks with metadata
#
# 2. POST /internal/search_top_k_cvs - Find top-k similar CVs
#    Input: {jd_text, top_k: 3}
#    Output: {cvs: [{cv_id, score}, ...]}
#    Flow:
#      - Embed jd_text using BGE-large model
#      - Query Pinecone for similar vectors
#      - Aggregate scores by cv_id
#      - Return top k CVs sorted by score
#
# Responsibilities:
# - Route requests to service.py business logic
# - Validate input
# - Handle errors and return appropriate HTTP status codes

# vector_service/app/api.py

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from . import service

router = APIRouter(prefix="/internal", tags=["internal"])


# --- Pydantic models ---------------------------------------------------------


class SimilarChunksRequest(BaseModel):
    jd_text: str = Field(..., description="Job description text")
    top_k: int = Field(10, ge=1, le=50, description="Number of chunks to return")


class ChunkResponse(BaseModel):
    text: str
    section: str
    cv_id: str
    score: float


class SimilarChunksResponse(BaseModel):
    chunks: List[ChunkResponse]


class SearchTopKCVsRequest(BaseModel):
    jd_text: str
    top_k: int = Field(3, ge=1, le=50, description="Number of CVs to return")


class SearchTopKCVItem(BaseModel):
    cv_id: str
    score: float


class SearchTopKCVsResponse(BaseModel):
    cvs: List[SearchTopKCVItem]


# --- Routes ------------------------------------------------------------------


@router.post(
    "/similar_chunks",
    response_model=SimilarChunksResponse,
    summary="Find similar CV chunks for a job description",
)
async def similar_chunks(body: SimilarChunksRequest) -> SimilarChunksResponse:
    try:
        chunks_data = await service.find_similar_chunks(
            jd_text=body.jd_text,
            top_k=body.top_k,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while finding similar chunks: {e}",
        )

    return SimilarChunksResponse(
        chunks=[ChunkResponse(**ch) for ch in chunks_data]
    )


@router.post(
    "/search_top_k_cvs",
    response_model=SearchTopKCVsResponse,
    summary="Find top-k most relevant CVs for a job description",
)
async def search_top_k_cvs(body: SearchTopKCVsRequest) -> SearchTopKCVsResponse:
    try:
        cvs_data = await service.search_top_k_cvs(
            jd_text=body.jd_text,
            top_k=body.top_k,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while searching top-k CVs: {e}",
        )

    return SearchTopKCVsResponse(
        cvs=[SearchTopKCVItem(**cv) for cv in cvs_data]
    )