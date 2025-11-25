# VectorService - Business Logic
# Handles chunking, embedding, and semantic search
#
# Functions:
# - find_similar_chunks(jd_text) -> chunks
#   * Embed JD using embedder.py
#   * Query Pinecone using pinecone_client.py
#   * Return similar chunks with metadata
#
# - search_top_k_cvs(jd_text, top_k) -> cv_ids with scores
#   * Embed JD using embedder.py
#   * Query Pinecone for similar vectors
#   * Aggregate scores by cv_id (sum or average)
#   * Sort and return top k
#
# - process_cv_for_embedding(cv_id) -> success/failure
#   * Called by mq_consumer.py when cv.created event received
#   * Fetch CV from StoringService
#   * Chunk CV by sections
#   * Embed each chunk
#   * Upsert to Pinecone with metadata
#
# Chunking Strategy:
# - Each section (experience, projects, skills, education) = 1 chunk
# - Metadata per chunk: {cv_id, section, raw_text}
#
# Responsibilities:
# - Chunking logic
# - Orchestrate embedding and vector operations
# - Coordinate between StoringService and Pinecone

# vector_service/app/service.py

# vector_service/app/service.py

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from . import embedder
from .pinecone_client import PineconeVectorClient
from . import storing_client


# --- Dependency wiring (set from main.py) ------------------------------------

_vector_client: PineconeVectorClient | None = None


def init_dependencies(vector_client: PineconeVectorClient) -> None:
    """
    Called from app.main.startup_event() to inject the Pinecone client.
    """
    global _vector_client
    _vector_client = vector_client


def _require_vector_client() -> PineconeVectorClient:
    if _vector_client is None:
        raise RuntimeError("Vector client not initialized")
    return _vector_client


# --- Public business functions used by API / MQ ------------------------------


async def find_similar_chunks(jd_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Embed JD text, query Pinecone, and return similar chunks.

    Returns a list of:
      {
        "text": "...",
        "section": "experience" | "projects" | "skills" | "education" | ...,
        "cv_id": "sha256_hash",
        "score": 0.87
      }
    """
    vc = _require_vector_client()

    # 1) Embed JD
    query_vec = embedder.embed_text(jd_text)

    # 2) Query Pinecone index
    result = vc.query_similar(query_vector=query_vec, top_k=top_k)

    # 3) Normalize result into a simple list for the API layer
    chunks: List[Dict[str, Any]] = []
    for match in result.matches:
        meta = match.metadata or {}
        chunks.append(
            {
                "text": meta.get("raw_text", ""),
                "section": meta.get("section", ""),
                "cv_id": meta.get("cv_id", ""),
                "score": float(match.score),
            }
        )
    return chunks


async def search_top_k_cvs(
    jd_text: str,
    top_k: int = 3,
    raw_top_k: int = 30,
) -> List[Dict[str, Any]]:
    """
    Embed JD text, query Pinecone for many chunks, aggregate scores by cv_id,
    and return top-k CVs ranked by total similarity score.

    Returns:
      [
        {"cv_id": "sha256", "score": 1.23},
        ...
      ]
    """
    vc = _require_vector_client()

    # 1) Embed JD
    query_vec = embedder.embed_text(jd_text)

    # 2) Query Pinecone for a larger pool of chunks
    result = vc.query_similar(query_vector=query_vec, top_k=raw_top_k)

    # 3) Aggregate scores by cv_id
    scores_by_cv: Dict[str, float] = defaultdict(float)
    for match in result.matches:
        meta = match.metadata or {}
        cv_id = meta.get("cv_id")
        if not cv_id:
            continue
        scores_by_cv[cv_id] += float(match.score)

    # 4) Sort and take top_k
    sorted_items: List[Tuple[str, float]] = sorted(
        scores_by_cv.items(), key=lambda x: x[1], reverse=True
    )[:top_k]

    return [{"cv_id": cv_id, "score": score} for cv_id, score in sorted_items]


async def process_cv_for_embedding(cv_id: str) -> None:
    """
    Background pipeline:

    - Fetch CV by cv_id from StoringService
    - Chunk it by section
    - Embed each chunk
    - Upsert vectors into Pinecone with metadata

    This is meant to be called from RabbitMQ consumer when a "cv.created"
    event is received. It doesn't expose any HTTP endpoint by itself.
    """
    vc = _require_vector_client()

    cv_doc = await storing_client.get_cv(cv_id)

    # We expect something like:
    # {
    #   "cv_id": "sha256...",
    #   "cv_text": "...",
    #   "structured_sections": {
    #       "experience": [...],
    #       "projects": [...],
    #       "skills": [...],
    #       "education": [...]
    #   }
    #   ...
    # }

    structured = cv_doc.get("structured_sections") or {}
    chunks: List[str] = []
    meta_list: List[Dict[str, Any]] = []

    # Simple chunking strategy: 1 chunk per high-level section
    for section in ["experience", "projects", "skills", "education"]:
        sec = structured.get(section)
        if not sec:
            continue

        # Turn section into text
        if isinstance(sec, list):
            text = "\n".join([str(x) for x in sec])
        else:
            text = str(sec)

        if not text.strip():
            continue

        chunks.append(text)
        meta_list.append(
            {
                "cv_id": cv_id,
                "section": section,
                "raw_text": text,
            }
        )

    # Fallback: if no structured sections, store full CV text as one chunk
    if not chunks:
        raw_text = cv_doc.get("cv_text", "")
        if raw_text.strip():
            chunks.append(raw_text)
            meta_list.append(
                {
                    "cv_id": cv_id,
                    "section": "full_cv",
                    "raw_text": raw_text,
                }
            )

    if not chunks:
        # Nothing to embed
        return

    # 2) Embed all chunks
    vectors = embedder.embed_batch(chunks)

    # 3) Prepare vector objects for PineconeVectorClient.upsert_vectors
    pinecone_vectors: List[Dict[str, Any]] = []
    for i, (vec, meta) in enumerate(zip(vectors, meta_list)):
        vec_id = f"{cv_id}:{meta.get('section', 'unknown')}:{i}"
        pinecone_vectors.append(
            {
                "id": vec_id,
                "values": vec,
                "metadata": meta,
            }
        )

    # 4) Upsert to Pinecone
    vc.upsert_vectors(pinecone_vectors)