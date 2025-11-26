from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import os

# Load model on import (will be cached)
_model = None

def get_model():
    """Get or load BGE-base embedding model (lighter than BGE-large)"""
    global _model
    if _model is None:
        print("Loading BGE-base embedding model...")
        try:
            _model = SentenceTransformer('BAAI/bge-base-en-v1.5')
            print("Model loaded successfully")
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
            raise
    return _model

def chunk_structured_sections(structured_sections: Dict[str, Any], cv_id: str) -> List[Dict[str, Any]]:
    """
    Intelligently chunk structured_sections using semantic algorithm
    
    Strategy:
    - String → 1 chunk
    - List of strings → Combine into 1 chunk
    - List of objects → Process each object, extract text fields
    - Dict (nested) → Extract text fields, combine
    
    Args:
        structured_sections: Structured CV sections from MongoDB
        cv_id: CV identifier
        
    Returns:
        List of chunks with metadata
    """
    chunks = []
    
    for section_name, section_data in structured_sections.items():
        if not section_data:
            continue
        
        # Handle summary (object with text field)
        if section_name == "summary" and isinstance(section_data, dict):
            summary_text = section_data.get("text")
            if summary_text and summary_text.strip():
                chunks.append({
                    "cv_id": cv_id,
                    "section": section_name,
                    "text": summary_text.strip(),
                    "metadata": {"type": "summary"}
                })
            continue
        
        # Handle contact (skip - not useful for semantic search)
        if section_name == "contact":
            continue
        
        # Handle experience (skip - processed separately with bullets)
        if section_name == "experience":
            continue
        
        # Handle projects (skip - processed separately with bullets)
        if section_name == "projects":
            continue
        
        # Handle skills (nested dict with categories)
        if section_name == "skills" and isinstance(section_data, dict):
            skill_parts = []
            for category, items in section_data.items():
                if items and isinstance(items, list):
                    skill_parts.extend(items)
            
            if skill_parts:
                skills_text = ", ".join(skill_parts)
                chunks.append({
                    "cv_id": cv_id,
                    "section": section_name,
                    "text": skills_text,
                    "metadata": {"type": "skills", "categories": list(section_data.keys())}
                })
            continue
        
        # Handle list of objects (experience, projects, education, leadership, etc.)
        if isinstance(section_data, list):
            for idx, item in enumerate(section_data):
                if isinstance(item, dict):
                    chunk_text = extract_text_from_object(item, section_name)
                    if chunk_text:
                        chunks.append({
                            "cv_id": cv_id,
                            "section": section_name,
                            "text": chunk_text,
                            "metadata": {"type": "object", "index": idx, **item}
                        })
                elif isinstance(item, str) and item.strip():
                    # List of strings (unlikely but handle it)
                    chunks.append({
                        "cv_id": cv_id,
                        "section": section_name,
                        "text": item.strip(),
                        "metadata": {"type": "list_item", "index": idx}
                    })
            continue
        
        # Handle string (direct text)
        if isinstance(section_data, str) and section_data.strip():
            chunks.append({
                "cv_id": cv_id,
                "section": section_name,
                "text": section_data.strip(),
                "metadata": {"type": "string"}
            })
    
    return chunks

def extract_text_from_object(obj: Dict[str, Any], section: str) -> str:
    """
    Extract meaningful text from object based on section type
    
    Args:
        obj: Object from structured sections
        section: Section name (experience, projects, education, etc.)
        
    Returns:
        Formatted text string for chunking
    """
    if section == "experience":
        company = obj.get("company", "")
        title = obj.get("title", "")
        bullets = obj.get("bullets", [])
        
        if bullets:
            # Each bullet becomes separate chunk (handled in chunk_structured_sections)
            # But we need to return text for each bullet
            return None  # Will be handled separately below
        
        # Fallback if no bullets
        location = obj.get("location", "")
        return f"{company} - {title} {location}".strip()
    
    elif section == "projects":
        name = obj.get("name", "")
        description = obj.get("description", "")
        techs = obj.get("technologies", [])
        
        parts = [name]
        if description:
            parts.append(description)
        if techs:
            parts.append(f"Technologies: {', '.join(techs)}")
        
        return " - ".join(parts) if parts else None
    
    elif section == "education":
        institution = obj.get("institution", "")
        degree = obj.get("degree", "")
        field = obj.get("field", "")
        gpa = obj.get("gpa", "")
        
        parts = [institution]
        if degree:
            parts.append(degree)
        if field:
            parts.append(field)
        if gpa:
            parts.append(f"GPA: {gpa}")
        
        return " - ".join(parts) if parts else None
    
    elif section == "leadership":
        role = obj.get("role", "")
        organization = obj.get("organization", "")
        description = obj.get("description", "")
        
        parts = [role]
        if organization:
            parts.append(organization)
        if description:
            parts.append(description)
        
        return " - ".join(parts) if parts else None
    
    elif section == "certifications":
        name = obj.get("name", "")
        issuer = obj.get("issuer", "")
        date = obj.get("date", "")
        
        parts = [name]
        if issuer:
            parts.append(f"by {issuer}")
        if date:
            parts.append(date)
        
        return " - ".join(parts) if parts else None
    
    # Generic fallback
    return str(obj)

def chunk_projects_bullets(projects_list: List[Dict], cv_id: str) -> List[Dict[str, Any]]:
    """
    Chunk projects section - each bullet point becomes separate chunk
    
    Args:
        projects_list: List of project objects
        cv_id: CV identifier
        
    Returns:
        List of chunks (one per bullet)
    """
    chunks = []
    
    for proj_idx, project in enumerate(projects_list):
        name = project.get("name", "")
        bullets = project.get("bullets", [])
        
        # If bullets exist, chunk each bullet separately
        if bullets:
            for bullet_idx, bullet in enumerate(bullets):
                if bullet and bullet.strip():
                    chunk_text = f"{name} - {bullet.strip()}"
                    chunks.append({
                        "cv_id": cv_id,
                        "section": "projects",
                        "text": chunk_text,
                        "metadata": {
                            "type": "project_bullet",
                            "project_name": name,
                            "proj_index": proj_idx,
                            "bullet_index": bullet_idx,
                            "technologies": project.get("technologies", []),
                            "link": project.get("link", "")
                        }
                    })
        else:
            # Fallback: use description if no bullets
            description = project.get("description", "")
            if description and description.strip():
                chunk_text = f"{name} - {description.strip()}"
                chunks.append({
                    "cv_id": cv_id,
                    "section": "projects",
                    "text": chunk_text,
                    "metadata": {
                        "type": "project_description",
                        "project_name": name,
                        "proj_index": proj_idx,
                        "technologies": project.get("technologies", [])
                    }
                })
    
    return chunks

def chunk_experience_bullets(experience_list: List[Dict], cv_id: str) -> List[Dict[str, Any]]:
    """
    Chunk experience section - each bullet point becomes separate chunk
    
    Args:
        experience_list: List of experience objects
        cv_id: CV identifier
        
    Returns:
        List of chunks (one per bullet)
    """
    chunks = []
    
    for exp_idx, exp in enumerate(experience_list):
        company = exp.get("company", "")
        title = exp.get("title", "")
        bullets = exp.get("bullets", [])
        
        # Each bullet becomes a separate chunk with company context
        for bullet_idx, bullet in enumerate(bullets):
            if bullet and bullet.strip():
                chunk_text = f"{company} - {bullet.strip()}"
                chunks.append({
                    "cv_id": cv_id,
                    "section": "experience",
                    "text": chunk_text,
                    "metadata": {
                        "type": "experience_bullet",
                        "company": company,
                        "title": title,
                        "exp_index": exp_idx,
                        "bullet_index": bullet_idx,
                        "location": exp.get("location", ""),
                        "start_date": exp.get("start_date", ""),
                        "end_date": exp.get("end_date", "")
                    }
                })
    
    return chunks

def embed_text(text: str) -> List[float]:
    """
    Embed a single text string using BGE-base model
    
    Args:
        text: Text string to embed
        
    Returns:
        768-dimensional embedding vector as list of floats
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    model = get_model()
    embedding = model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
    return embedding.tolist()

def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Embed chunks using BGE-base model
    
    Args:
        chunks: List of chunk dictionaries with 'text' field
        
    Returns:
        Chunks with 'embedding' field added (768-dim vector)
    """
    if not chunks:
        return []
    
    model = get_model()
    
    # Extract texts
    texts = [chunk["text"] for chunk in chunks]
    
    # Batch embed
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()
    
    print(f"Embedded {len(chunks)} chunks successfully")
    return chunks
