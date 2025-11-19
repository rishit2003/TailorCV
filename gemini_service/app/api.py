# GeminiService - Internal API Endpoints
# These endpoints are called by API Gateway (not exposed to client)
#
# Internal Endpoints:
# 1. POST /internal/structure_cv - Structure raw CV text into JSON
#    Input: {cv_text}
#    Output: {structured_json_cv}
#    Flow:
#      - Call Gemini API with structuring prompt
#      - Parse response into structured JSON format
#      - Return structured CV
#
# 2. POST /internal/missing_keywords - Find missing keywords
#    Input: {jd_text, cv_id}
#    Output: {missing_keywords: [...], explanation: "..."}
#    Flow:
#      - Call StoringService.getCV(cv_id) to fetch structured CV
#      - Call Gemini API with JD + CV
#      - Return missing keywords and explanation
#
# 3. POST /internal/score - Score CV against job description
#    Input: {jd_text, cv_id}
#    Output: {score: 85, explanation: "..."}
#    Flow:
#      - Call StoringService.getCV(cv_id) to fetch structured CV
#      - Call Gemini API with scoring prompt
#      - Return score and explanation
#
# 4. POST /internal/tailored_bullets - Generate tailored bullet points
#    Input: {jd_text, chunks: [{text, section}, ...]}
#    Output: {bullets: [...]}
#    Flow:
#      - Receive JD and similar chunks from VectorService
#      - Call Gemini API with context
#      - Return generated bullet points
#
# Responsibilities:
# - Route requests to service.py business logic
# - Validate input
# - Handle errors and return appropriate HTTP status codes

