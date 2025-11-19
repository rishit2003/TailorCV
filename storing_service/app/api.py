# StoringService - Internal API Endpoints
# These endpoints are called by other services (not exposed to client)
#
# Internal Endpoints:
# 1. POST /internal/store_cv - Store structured CV with deduplication
#    Input: {structured_json_cv, cv_text}
#    Output: {cv_id (hash)}
#    Flow:
#      - Calculate hash of cv_text
#      - Check if CV exists (deduplication)
#      - If exists: return existing cv_id, update Redis
#      - If new: insert to MongoDB, publish to RabbitMQ, update Redis
#
# 2. GET /internal/get_cv/{cv_id} - Retrieve CV by cv_id
#    Output: {structured_json_cv}
#    Flow:
#      - Query MongoDB by cv_id (hash-based identifier)
#      - Return structured JSON
#
# 3. GET /internal/get_latest_cv - Get most recently uploaded CV
#    Output: {structured_json_cv}
#    Flow:
#      - Check Redis for latest_cv key (fast path)
#      - If not in Redis, query MongoDB
#      - Return structured JSON
#
# Responsibilities:
# - Route requests to service.py business logic
# - Validate input
# - Handle errors and return appropriate HTTP status codes

