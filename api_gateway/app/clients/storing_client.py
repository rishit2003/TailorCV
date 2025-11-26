import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load the infra/.env file
BASE_DIR = Path(__file__).resolve().parents[2]  # go up to project root
ENV_PATH = BASE_DIR / "infra" / ".env"

load_dotenv(ENV_PATH)

STORING_SERVICE_URL = os.getenv("STORING_SERVICE_URL", "http://localhost:8001")

def store_cv(structured_json: dict, cv_text: str) -> dict:
    """
    Store CV in StoringService
    
    Args:
        structured_json: Structured CV JSON from GeminiService
        cv_text: Raw CV text
        
    Returns:
        {"cv_id": str, "status": str, "message": str}
    """
    url = f"{STORING_SERVICE_URL}/internal/store_cv"
    
    response = requests.post(
        url,
        json={"structured_json": structured_json, "cv_text": cv_text},
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"StoringService error: {response.status_code}")
    
    return response.json()

def get_cv(cv_id: str) -> dict:
    """
    Get CV by ID from StoringService
    
    Args:
        cv_id: CV identifier
        
    Returns:
        Complete CV document
    """
    url = f"{STORING_SERVICE_URL}/internal/get_cv/{cv_id}"
    
    response = requests.get(url, timeout=10)
    
    if response.status_code == 404:
        raise Exception("CV not found")
    elif response.status_code != 200:
        raise Exception(f"StoringService error: {response.status_code}")
    
    return response.json()

def get_all_cvs() -> list:
    """
    Get all CVs from MongoDB (for dropdown)
    
    Returns:
        List of CVs with cv_id, filename, metadata
    """
    url = f"{STORING_SERVICE_URL}/internal/get_all_cvs"
    
    response = requests.get(url, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"StoringService error: {response.status_code}")
    
    return response.json()
