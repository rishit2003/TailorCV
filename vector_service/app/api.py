# VectorService - Internal API Endpoints
# These endpoints are called by API Gateway (not exposed to client)
#
# Internal Endpoints:
# 1. POST /internal/similar_chunks - Find similar CV chunks to JD
#    Input: {jd_text}
#    Output: {chunks: [{text, section, cv_id, score}, ...]}
#    Flow:
#      - Embed jd_text using BGE-large model
#      - Query Pinecone for top similar vectors
#      - Return chunks with metadata
#
# 2. POST /internal/search_top_k_cvs - Find top-k similar CVs
#    Input: {jd_text, top_k: 3}
#    Output: {cvs: [{cv_id, score}, ...]}
#    Flow:
#      - Embed jd_text using BGE-large model
#      - Query Pinecone for similar vectors
#      - Aggregate scores by cv_id
#      - Return top k CVs sorted by score
#
# Responsibilities:
# - Route requests to service.py business logic
# - Validate input
# - Handle errors and return appropriate HTTP status codes

