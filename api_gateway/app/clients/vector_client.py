# HTTP Client for VectorService
# Makes HTTP requests to VectorService internal APIs

import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8003")

def find_similar_chunks(
    jd_text: str, 
    min_score: float = 0.75,
    max_chunks_to_query: int = 50
) -> List[Dict[str, Any]]:
    """
    Find similar CV chunks to job description
    
    Uses threshold-based approach: Returns ALL chunks with score >= min_score.
    No fixed limit - uses all relevant chunks for better LLM context.
    
    Args:
        jd_text: Job description text
        min_score: Minimum similarity score threshold (default: 0.75)
        max_chunks_to_query: Maximum chunks to query from Pinecone (default: 50)
        
    Returns:
        List of chunks with text, section, cv_id, score (all above threshold)
    """
    try:
        response = requests.post(
            f"{VECTOR_SERVICE_URL}/internal/similar_chunks",
            json={
                "jd_text": jd_text, 
                "min_score": min_score,
                "max_chunks_to_query": max_chunks_to_query
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("chunks", [])
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to find similar chunks: {str(e)}")

def search_top_k_cvs(jd_text: str, top_k: int = 3, raw_top_k: int = 30) -> List[Dict[str, Any]]:
    """
    Find top-k similar CVs to job description
    
    Args:
        jd_text: Job description text
        top_k: Number of top CVs to return
        raw_top_k: Number of chunks to fetch before aggregation
        
    Returns:
        List of CVs with cv_id and score
    """
    try:
        response = requests.post(
            f"{VECTOR_SERVICE_URL}/internal/search_top_k_cvs",
            json={"jd_text": jd_text, "top_k": top_k, "raw_top_k": raw_top_k},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("cvs", [])
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to search top K CVs: {str(e)}")
