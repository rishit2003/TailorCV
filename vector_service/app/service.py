import os
import requests
from dotenv import load_dotenv
from app.embedder import chunk_structured_sections, chunk_experience_bullets, chunk_projects_bullets, embed_chunks
from app.pinecone_client import upsert_chunks_to_pinecone

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
