# StoringService - Business Logic
# Core logic for CV storage, retrieval, and deduplication
#
# Functions:
# - store_cv(structured_json, cv_text) -> cv_id
#   * Calculate SHA256 hash of cv_text
#   * Check MongoDB for existing cv_id
#   * If exists: skip storage, update Redis, return cv_id
#   * If new: insert to MongoDB, update Redis, publish event, return cv_id
#
# - get_cv_by_id(cv_id) -> structured_json
#   * Query MongoDB by cv_id field
#   * Return structured CV JSON
#
# - get_latest_cv() -> structured_json
#   * Check Redis key: latest_cv
#   * If found: get cv_id, fetch from MongoDB
#   * If not found: query MongoDB sorted by created_at DESC
#   * Return structured CV JSON
#
# Responsibilities:
# - Hash calculation for deduplication
# - MongoDB CRUD operations
# - Redis caching logic
# - Coordinate with events.py for RabbitMQ publishing

