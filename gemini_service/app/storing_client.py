# HTTP Client for StoringService
# GeminiService uses this to fetch CV data
#
# Internal API calls:
# - getCV(cv_id) -> structured_json
# - getLatestCV() -> structured_json
#
# Usage:
# - Called by service.py when needing CV data for LLM operations
# - Example: Before scoring, fetch CV by cv_id
#
# Responsibilities:
# - Build HTTP requests to StoringService endpoints
# - Handle connection errors and retries
# - Parse responses

