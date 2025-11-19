# HTTP Client for StoringService
# VectorService uses this to fetch CV data for embedding
#
# Internal API calls:
# - getCV(cv_id) -> structured_json
#
# Usage:
# - Called by mq_consumer.py when processing cv.created event
# - Fetches CV data to chunk and embed
#
# Responsibilities:
# - Build HTTP requests to StoringService endpoints
# - Handle connection errors and retries (critical for async processing)
# - Parse responses

