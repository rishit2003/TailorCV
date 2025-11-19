# StoringService - MongoDB Connection and Operations
# Manages MongoDB connection and database operations
#
# Database: tailorcv_db
# Collection: cvs
#
# Document Schema:
# {
#   "_id": ObjectId,                  # MongoDB auto-generated (internal)
#   "cv_id": "sha256_hash",           # Our primary identifier (hash of cv_text)
#   "cv_text": "original text...",    # Raw CV text
#   "structured_json": {              # Structured sections from GeminiService
#     "experience": [...],
#     "projects": [...],
#     "skills": [...],
#     "education": [...]
#   },
#   "created_at": "2025-11-19T...",
#   "updated_at": "2025-11-19T..."
# }
#
# Operations:
# - find_by_cv_id(cv_id) -> document or None
# - insert_cv(cv_id, cv_text, structured_json) -> cv_id
# - find_latest() -> document (sorted by created_at DESC)
#
# Responsibilities:
# - MongoDB client initialization
# - CRUD operations on cvs collection
# - Index management (cv_id, created_at)

