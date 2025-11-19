# HTTP Client for VectorService
# Makes HTTP requests to VectorService internal APIs
#
# Internal API calls:
# - similar-chunks(jd_text) -> list of chunks with metadata
# - search-top-k-cvs(jd_text, top_k) -> list of {cv_id, score}
#
# Responsibilities:
# - Build HTTP requests to VectorService endpoints
# - Handle connection errors and retries
# - Parse responses

