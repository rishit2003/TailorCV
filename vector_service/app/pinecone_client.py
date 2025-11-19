# VectorService - Pinecone VectorDB Client
# Manages all operations with Pinecone VectorDB
#
# Index Name: tailorcv-vectors
# Dimension: 1024 (BGE-large output)
#
# Vector Metadata Schema:
# {
#   "cv_id": "sha256_hash",
#   "section": "experience" | "projects" | "skills" | "education",
#   "raw_text": "chunk text content"
# }
#
# Operations:
# - upsert_vectors(vectors, metadata) -> success/failure
#   * Insert/update vectors with metadata
#   * Used after embedding chunks
#
# - query_similar(query_vector, top_k) -> matches
#   * Find top k similar vectors
#   * Return matches with metadata and scores
#
# - delete_by_cv_id(cv_id) -> success/failure
#   * Remove all vectors for a specific CV
#   * Used if CV needs to be deleted
#
# Responsibilities:
# - Pinecone client initialization and authentication
# - Vector CRUD operations
# - Query execution with similarity search

