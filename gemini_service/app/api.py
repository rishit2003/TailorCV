from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.service import structure_cv, find_missing_keywords, calculate_score, generate_tailored_bullets

router = APIRouter()

class StructureCVRequest(BaseModel):
    cv_text: str

class StructureCVResponse(BaseModel):
    metadata: dict
    structured_sections: dict

@router.post("/internal/structure_cv", response_model=StructureCVResponse)
async def structure_cv_endpoint(request: StructureCVRequest):
    """
    Structure raw CV text into JSON format
    
    Args:
        cv_text: Raw CV text string
        
    Returns:
        metadata and structured_sections
    """
    try:
        result = structure_cv(request.cv_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to structure CV: {str(e)}")

class MissingKeywordsRequest(BaseModel):
    cv_id: str
    job_description: str

class KeywordCategory(BaseModel):
    technical: List[str]
    soft: List[str]

class MissingKeywordsResponse(BaseModel):
    cv_id: str
    filename: str
    keywords_you_have: KeywordCategory
    keywords_missing: KeywordCategory

@router.post("/internal/missing_keywords", response_model=MissingKeywordsResponse)
async def missing_keywords_endpoint(request: MissingKeywordsRequest):
    """
    Find missing keywords by comparing CV with job description
    
    Args:
        cv_id: CV identifier (SHA256 hash)
        job_description: Job description text
        
    Returns:
        cv_id, filename, keywords_you_have, and keywords_missing
    """
    try:
        result = find_missing_keywords(request.cv_id, request.job_description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze keywords: {str(e)}")

class ScoreRequest(BaseModel):
    cv_id: str
    job_description: str

class CategoryScore(BaseModel):
    score: int
    max_score: int
    percentage: int
    explanation: str

class ScoreResponse(BaseModel):
    cv_id: str
    filename: str
    overall_score: int
    max_score: int
    rating: str
    category_scores: Dict[str, CategoryScore]
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]

@router.post("/internal/score", response_model=ScoreResponse)
async def score_endpoint(request: ScoreRequest):
    """
    Calculate CV score by comparing with job description
    
    Args:
        cv_id: CV identifier (SHA256 hash)
        job_description: Job description text
        
    Returns:
        cv_id, filename, overall_score, category_scores, strengths, gaps, recommendations
    """
    try:
        result = calculate_score(request.cv_id, request.job_description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate score: {str(e)}")

class TailoredBulletsRequest(BaseModel):
    job_description: str
    similar_chunks: List[Dict[str, Any]]

class TailoredBulletsResponse(BaseModel):
    tailored_bullets: List[str]
    count: int

@router.post("/internal/tailored_bullets", response_model=TailoredBulletsResponse)
async def tailored_bullets_endpoint(request: TailoredBulletsRequest):
    """
    Generate tailored bullet points based on job description and similar CV chunks
    
    Args:
        job_description: Job description text
        similar_chunks: List of similar CV chunks with text, section, cv_id, score
        
    Returns:
        tailored_bullets list and count
    """
    try:
        result = generate_tailored_bullets(request.job_description, request.similar_chunks)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tailored bullets: {str(e)}")

