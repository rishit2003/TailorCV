import os
import requests
from typing import List, Dict, Any
from collections import defaultdict
from dotenv import load_dotenv
from app.embedder import chunk_structured_sections, chunk_experience_bullets, chunk_projects_bullets, embed_chunks, embed_text
from app.pinecone_client import upsert_chunks_to_pinecone, query_similar

load_dotenv()

STORING_SERVICE_URL = os.getenv("STORING_SERVICE_URL", "http://localhost:8001")

def process_cv_for_embedding(cv_id: str):
    """
    Process CV for embedding (called by RabbitMQ consumer)
    
    Flow:
    1. Fetch CV from StoringService
    2. Extract structured_sections
    3. Chunk sections (semantic algorithm)
    4. Embed chunks (BGE-large)
    5. Upload to Pinecone
    
    Args:
        cv_id: CV identifier
    """
    print(f"Processing CV for embedding: {cv_id}")
    
    try:
        # Step 1: Fetch CV from StoringService
        response = requests.get(
            f"{STORING_SERVICE_URL}/internal/get_cv/{cv_id}",
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch CV: {response.status_code}")
        
        cv_data = response.json()
        structured_sections = cv_data.get("structured_sections", {})
        
        print(f"Fetched CV: {cv_id}")
        print(f"Sections found: {list(structured_sections.keys())}")
        
        # Step 2: Chunk structured sections
        all_chunks = []
        
        # Handle experience separately (each bullet = 1 chunk)
        if "experience" in structured_sections and structured_sections["experience"]:
            experience_chunks = chunk_experience_bullets(
                structured_sections["experience"], 
                cv_id
            )
            all_chunks.extend(experience_chunks)
            print(f"Created {len(experience_chunks)} experience chunks")
        
        # Handle projects separately (each bullet = 1 chunk, or description if no bullets)
        if "projects" in structured_sections and structured_sections["projects"]:
            project_chunks = chunk_projects_bullets(
                structured_sections["projects"],
                cv_id
            )
            all_chunks.extend(project_chunks)
            print(f"Created {len(project_chunks)} project chunks")
        
        # Handle other sections (summary, skills, education, leadership, etc.)
        other_sections = {k: v for k, v in structured_sections.items() 
                         if k not in ["experience", "projects"]}
        other_chunks = chunk_structured_sections(other_sections, cv_id)
        all_chunks.extend(other_chunks)
        print(f"Created {len(other_chunks)} other chunks")
        
        print(f"Total chunks created: {len(all_chunks)}")
        
        if not all_chunks:
            print("Warning: No chunks created from CV")
            return
        
        # Step 3: Embed chunks
        embedded_chunks = embed_chunks(all_chunks)
        
        # Step 4: Upload to Pinecone
        upsert_chunks_to_pinecone(embedded_chunks)
        
        print(f"CV processing complete: {cv_id} - {len(embedded_chunks)} chunks uploaded to Pinecone")
        
    except Exception as e:
        print(f"Error processing CV {cv_id}: {e}")
        raise

def find_similar_chunks(
    jd_text: str, 
    min_score: float = 0.75,
    max_chunks_to_query: int = 50
) -> List[Dict[str, Any]]:
    """
    Embed JD text, query Pinecone, and return ALL chunks above similarity threshold.
    
    Uses threshold-based approach: Returns all chunks with score >= min_score.
    No fixed limit - uses all relevant chunks for better LLM context.
    
    Args:
        jd_text: Job description text
        min_score: Minimum similarity score threshold (default: 0.75)
                  Only chunks with score >= min_score will be returned
        max_chunks_to_query: Maximum chunks to query from Pinecone (default: 50)
                            This is just a safety limit for query performance
        
    Returns:
        List of chunks with score >= min_score:
        {
            "text": "...",
            "section": "experience" | "projects" | "skills" | ...,
            "cv_id": "sha256_hash",
            "score": 0.87
        }
    """
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text cannot be empty")
    
    if min_score < 0.0 or min_score > 1.0:
        raise ValueError("min_score must be between 0.0 and 1.0")
    
    # 1) Embed JD text
    print(f"Embedding job description (length: {len(jd_text)} chars)...")
    query_vector = embed_text(jd_text)
    
    # 2) Query Pinecone for top 50 chunks (we'll filter by threshold)
    print(f"Querying Pinecone for top {max_chunks_to_query} chunks (will filter by threshold >= {min_score})...")
    matches = query_similar(query_vector, top_k=max_chunks_to_query)
    
    # 3) Format results and filter by threshold
    chunks: List[Dict[str, Any]] = []
    for match in matches:
        score = match.get("score", 0.0)
        
        # Only include chunks above threshold
        if score >= min_score:
            meta = match.get("metadata", {})
            chunks.append({
                "text": meta.get("text", ""),
                "section": meta.get("section", ""),
                "cv_id": meta.get("cv_id", ""),
                "score": score
            })
    
    print(f"Found {len(chunks)} chunks above threshold {min_score} (from {len(matches)} queried)")
    
    if len(chunks) == 0:
        print(f"Warning: No chunks found above threshold {min_score}. Consider lowering the threshold.")
    
    return chunks

def search_top_k_cvs(jd_text: str, top_k: int = 3, raw_top_k: int = 30) -> List[Dict[str, Any]]:
    """
    Embed JD text, query Pinecone for many chunks, aggregate scores by cv_id,
    and return top-k CVs ranked by total similarity score.
    
    Args:
        jd_text: Job description text
        top_k: Number of top CVs to return (default: 3)
        raw_top_k: Number of chunks to fetch before aggregation (default: 30)
        
    Returns:
        List of CVs sorted by score:
        [
            {"cv_id": "sha256", "score": 1.23},
            ...
        ]
    """
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text cannot be empty")
    
    # 1) Embed JD text
    print(f"Embedding job description (length: {len(jd_text)} chars)...")
    query_vector = embed_text(jd_text)
    
    # 2) Query Pinecone for a larger pool of chunks
    print(f"Querying Pinecone for top {raw_top_k} chunks...")
    matches = query_similar(query_vector, top_k=raw_top_k)
    
    # 3) Aggregate scores by cv_id
    scores_by_cv: Dict[str, float] = defaultdict(float)
    for match in matches:
        meta = match.get("metadata", {})
        cv_id = meta.get("cv_id")
        if not cv_id:
            continue
        scores_by_cv[cv_id] += float(match.get("score", 0.0))
    
    # 4) Sort and take top_k
    sorted_items = sorted(
        scores_by_cv.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:top_k]
    
    result = [{"cv_id": cv_id, "score": score} for cv_id, score in sorted_items]
    print(f"Found {len(result)} top CVs")
    return result
