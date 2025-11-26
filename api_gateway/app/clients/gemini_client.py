import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_SERVICE_URL = os.getenv("GEMINI_SERVICE_URL", "http://localhost:8002")

def structure_cv(cv_text: str) -> dict:
    """
    Structure CV using GeminiService
    
    Args:
        cv_text: Raw CV text
        
    Returns:
        {"metadata": dict, "structured_sections": dict}
    """
    url = f"{GEMINI_SERVICE_URL}/internal/structure_cv"
    
    response = requests.post(
        url,
        json={"cv_text": cv_text},
        timeout=120  # Gem ini can take time
    )
    
    if response.status_code != 200:
        raise Exception(f"GeminiService error: {response.status_code}")
    
    return response.json()

def get_missing_keywords(cv_id: str, job_description: str) -> dict:
    """
    Get missing keywords from GeminiService
    
    Args:
        cv_id: CV identifier
        job_description: Job description text
        
    Returns:
        {"cv_id": str, "filename": str, "keywords_you_have": dict, "keywords_missing": dict}
    """
    url = f"{GEMINI_SERVICE_URL}/internal/missing_keywords"
    
    response = requests.post(
        url,
        json={"cv_id": cv_id, "job_description": job_description},
        timeout=120
    )
    
    if response.status_code != 200:
        raise Exception(f"GeminiService error: {response.status_code}")
    
    return response.json()

def get_score(cv_id: str, job_description: str) -> dict:
    """
    Get CV score from GeminiService
    
    Args:
        cv_id: CV identifier
        job_description: Job description text
        
    Returns:
        Complete score breakdown
    """
    url = f"{GEMINI_SERVICE_URL}/internal/score"
    
    response = requests.post(
        url,
        json={"cv_id": cv_id, "job_description": job_description},
        timeout=120
    )
    
    if response.status_code != 200:
        raise Exception(f"GeminiService error: {response.status_code}")
    
    return response.json()

def generate_tailored_bullets(job_description: str, similar_chunks: list) -> dict:
    """
    Generate tailored bullet points from GeminiService
    
    Args:
        job_description: Job description text
        similar_chunks: List of similar CV chunks
        
    Returns:
        {"tailored_bullets": list, "count": int}
    """
    url = f"{GEMINI_SERVICE_URL}/internal/tailored_bullets"
    
    response = requests.post(
        url,
        json={
            "job_description": job_description,
            "similar_chunks": similar_chunks
        },
        timeout=120
    )
    
    if response.status_code != 200:
        raise Exception(f"GeminiService error: {response.status_code}")
    
    return response.json()
