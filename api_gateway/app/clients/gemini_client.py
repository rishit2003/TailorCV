# HTTP Client for GeminiService
# Makes HTTP requests to GeminiService internal APIs
#
# Internal API calls:
# - structure-cv(cv_text) -> structured_json_cv
# - missing-keywords(jd_text, cv_id) -> missing_keywords
# - score(jd_text, cv_id) -> score + explanation
# - tailored-bullets(jd_text, chunks) -> bullet_points
#
# Responsibilities:
# - Build HTTP requests to GeminiService endpoints
# - Handle connection errors and retries
# - Parse responses

