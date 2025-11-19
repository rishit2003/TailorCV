# HTTP Client for StoringService
# Makes HTTP requests to StoringService internal APIs
#
# Internal API calls:
# - StoreCV(structured_json_cv, cv_text) -> cv_id
# - getCV(cv_id) -> structured_json
# - getLatestCV() -> structured_json
#
# Responsibilities:
# - Build HTTP requests to StoringService endpoints
# - Handle connection errors and retries
# - Parse responses

