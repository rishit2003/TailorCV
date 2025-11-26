from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import io

# Import HTTP clients
from app.clients import gemini_client, storing_client, vector_client

# Try to import PyPDF2 for PDF extraction
try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

router = APIRouter()

# ==========================================
# Request/Response Models
# ==========================================

class UploadCVRequest(BaseModel):
    cv_text: str

class KeywordsRequest(BaseModel):
    cv_id: str
    job_description: str

class ScoreRequest(BaseModel):
    cv_id: str
    job_description: str

class TailoredBulletsRequest(BaseModel):
    job_description: str

class SimilarCVsRequest(BaseModel):
    job_description: str
    top_k: Optional[int] = 3

# ==========================================
# Public Endpoints
# ==========================================

@router.get("/my_cvs")
async def get_my_cvs():
    """
    Get all CVs for dropdown selection
    
    Returns:
        List of CVs with cv_id, filename, created_at
    """
    try:
        cvs = storing_client.get_all_cvs()
        return {
            "success": True,
            "cvs": cvs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CVs: {str(e)}")

@router.post("/upload_cv_text")
async def upload_cv_text(request: UploadCVRequest):
    """
    Upload CV as text
    
    Flow:
    1. Structure CV with GeminiService
    2. Store CV in StoringService
    3. Return cv_id
    """
    try:
        # Structure CV
        structured = gemini_client.structure_cv(request.cv_text)
        
        # Store CV
        stored = storing_client.store_cv(structured, request.cv_text)
        
        return {
            "success": True,
            "message": "CV uploaded successfully!",
            "cv_id": stored["cv_id"],
            "status": stored["status"],
            "filename": structured["metadata"].get("filename", "Unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload CV: {str(e)}")

@router.post("/upload_cv_pdf")
async def upload_cv_pdf(file: UploadFile = File(...)):
    """
    Upload CV as PDF file
    
    Flow:
    1. Extract text from PDF
    2. Structure CV with GeminiService
    3. Store CV in StoringService
    4. Return cv_id
    """
    if not PDF_SUPPORT:
        raise HTTPException(status_code=500, detail="PDF support not available. Install PyPDF2.")
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Extract text from PDF
        pdf = PdfReader(io.BytesIO(pdf_bytes))
        cv_text = ""
        for page in pdf.pages:
            cv_text += page.extract_text() + "\n"
        
        if not cv_text.strip():
            raise ValueError("Could not extract text from PDF. The file might be scanned or empty.")
        
        # Structure CV
        structured = gemini_client.structure_cv(cv_text)
        
        # Override filename with uploaded file name
        structured["metadata"]["filename"] = file.filename
        
        # Store CV
        stored = storing_client.store_cv(structured, cv_text)
        
        return {
            "success": True,
            "message": "CV uploaded successfully!",
            "cv_id": stored["cv_id"],
            "status": stored["status"],
            "filename": file.filename
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@router.post("/keywords")
async def get_keywords(request: KeywordsRequest):
    """
    Get missing keywords
    
    Flow:
    1. Call GeminiService /internal/missing_keywords
    2. Return result
    """
    try:
        result = gemini_client.get_missing_keywords(request.cv_id, request.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze keywords: {str(e)}")

@router.post("/score")
async def get_score(request: ScoreRequest):
    """
    Get CV score
    
    Flow:
    1. Call GeminiService /internal/score
    2. Return result
    """
    try:
        result = gemini_client.get_score(request.cv_id, request.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate score: {str(e)}")

@router.post("/tailored_bullets")
async def get_tailored_bullets(request: TailoredBulletsRequest):
    """
    Get tailored bullet points for job description
    
    Flow:
    1. Call VectorService /internal/similar_chunks to find relevant CV chunks
    2. Call GeminiService /internal/tailored_bullets to generate bullets
    3. Return tailored bullets
    """
    try:
        # Step 1: Find similar chunks (threshold-based: all chunks with score >= 0.75)
        similar_chunks = vector_client.find_similar_chunks(
            request.job_description, 
            min_score=0.75,  # Only chunks with 75%+ similarity
            max_chunks_to_query=50  # Query top 50, filter by threshold (ranked best to worst)
        )
        
        if not similar_chunks:
            return {
                "success": True,
                "message": "No similar chunks found. Try uploading more CVs.",
                "tailored_bullets": [],
                "count": 0
            }
        
        # Step 2: Generate tailored bullets
        result = gemini_client.generate_tailored_bullets(request.job_description, similar_chunks)
        
        return {
            "success": True,
            "tailored_bullets": result.get("tailored_bullets", []),
            "count": result.get("count", 0),
            "chunks_used": len(similar_chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tailored bullets: {str(e)}")

@router.post("/similar_cvs")
async def get_similar_cvs(request: SimilarCVsRequest):
    """
    Get top-k similar CVs to job description
    
    Flow:
    1. Call VectorService /internal/search_top_k_cvs
    2. Return list of CVs ranked by similarity score
    
    Returns:
        {
            "success": true,
            "cvs": [
                {"cv_id": "...", "score": 1.23},
                ...
            ]
        }
    """
    try:
        # Call VectorService to find top-k similar CVs
        cvs = vector_client.search_top_k_cvs(
            request.job_description,
            top_k=request.top_k,
            raw_top_k=50  # Query top 50 chunks before aggregation
        )
        
        return {
            "success": True,
            "cvs": cvs,
            "count": len(cvs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar CVs: {str(e)}")
