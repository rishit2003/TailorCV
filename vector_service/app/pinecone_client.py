from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "tailorcv-cv-chunks")

# Initialize Pinecone client
_pc = None
_index = None

def get_pinecone_client():
    """Get or initialize Pinecone client"""
    global _pc
    if _pc is None:
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        _pc = Pinecone(api_key=PINECONE_API_KEY)
    return _pc

def get_index():
    """Get or initialize Pinecone index (auto-creates if doesn't exist)"""
    global _index
    if _index is None:
        pc = get_pinecone_client()
        REQUIRED_DIMENSION = 768  # BGE-base dimension
        
        # Check if index exists
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}' with dimension {REQUIRED_DIMENSION} (BGE-base)...")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=REQUIRED_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"Index '{PINECONE_INDEX_NAME}' created successfully.")
        else:
            # Check dimension of existing index
            index_info = pc.describe_index(PINECONE_INDEX_NAME)
            existing_dim = index_info.dimension
            
            if existing_dim != REQUIRED_DIMENSION:
                # Check if index is empty (safe to delete)
                temp_index = pc.Index(PINECONE_INDEX_NAME)
                stats = temp_index.describe_index_stats()
                total_records = stats.get('total_record_count', 0)
                
                if total_records == 0:
                    print(f"WARNING: Existing index has dimension {existing_dim}, but we need {REQUIRED_DIMENSION}.")
                    print(f"Index is empty (0 records). Deleting and recreating with correct dimension...")
                    pc.delete_index(PINECONE_INDEX_NAME)
                    print(f"Deleted old index. Creating new one with dimension {REQUIRED_DIMENSION}...")
                    pc.create_index(
                        name=PINECONE_INDEX_NAME,
                        dimension=REQUIRED_DIMENSION,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                    print(f"Index '{PINECONE_INDEX_NAME}' recreated successfully.")
                else:
                    raise ValueError(
                        f"Index '{PINECONE_INDEX_NAME}' has dimension {existing_dim} but we need {REQUIRED_DIMENSION}. "
                        f"Index has {total_records} records. Please delete it manually in Pinecone dashboard."
                    )
            else:
                print(f"Index '{PINECONE_INDEX_NAME}' already exists with correct dimension ({REQUIRED_DIMENSION}).")
        
        _index = pc.Index(PINECONE_INDEX_NAME)
        print(f"Connected to Pinecone index: {PINECONE_INDEX_NAME}")
    
    return _index

def upsert_chunks_to_pinecone(chunks: List[Dict[str, Any]]):
    """
    Upload embedded chunks to Pinecone
    
    Args:
        chunks: List of chunks with 'embedding', 'cv_id', 'section', 'text', 'metadata'
    """
    if not chunks:
        print("No chunks to upload")
        return
    
    index = get_index()
    
    # Prepare vectors for Pinecone
    vectors = []
    for i, chunk in enumerate(chunks):
        vector_id = f"{chunk['cv_id']}_{chunk['section']}_{i}"
        
        # Prepare metadata (Pinecone has 10KB limit per metadata)
        metadata = {
            "cv_id": chunk["cv_id"],
            "section": chunk["section"],
            "text": chunk["text"][:1000]  # Truncate to stay under limit
        }
        
        # Add additional metadata if present
        if "metadata" in chunk:
            for key, value in chunk["metadata"].items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = str(value)[:500]  # Truncate long values
        
        vectors.append({
            "id": vector_id,
            "values": chunk["embedding"],
            "metadata": metadata
        })
    
    # Batch upsert (Pinecone supports up to 100 vectors per request)
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i//batch_size + 1}: {len(batch)} vectors")
    
    print(f"Successfully uploaded {len(vectors)} chunks to Pinecone")

def query_similar(query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Query Pinecone for similar vectors
    
    Args:
        query_vector: 768-dimensional embedding vector
        top_k: Number of similar vectors to return
        
    Returns:
        List of matches with metadata and scores:
        [
            {
                "id": "vector_id",
                "score": 0.87,
                "metadata": {"text": "...", "section": "...", "cv_id": "..."}
            },
            ...
        ]
    """
    if not query_vector:
        raise ValueError("Query vector cannot be empty")
    
    if len(query_vector) != 768:
        raise ValueError(f"Query vector must be 768 dimensions, got {len(query_vector)}")
    
    index = get_index()
    
    # Query Pinecone
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    
    # Format results
    matches = []
    for match in results.matches:
        matches.append({
            "id": match.id,
            "score": float(match.score),
            "metadata": match.metadata or {}
        })
    
    return matches
