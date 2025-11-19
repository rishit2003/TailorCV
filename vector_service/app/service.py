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

