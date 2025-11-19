# GeminiService - Business Logic
# Orchestrates LLM operations and combines with CV data
#
# Functions:
# - structure_cv(cv_text) -> structured_json
#   * Call llm_client.py to structure CV
#   * Return structured JSON with sections
#
# - get_missing_keywords(jd_text, cv_id) -> keywords + explanation
#   * Fetch CV from StoringService via storing_client.py
#   * Combine JD + CV in prompt
#   * Call llm_client.py
#   * Return missing keywords
#
# - score_cv(jd_text, cv_id) -> score + explanation
#   * Fetch CV from StoringService
#   * Call llm_client.py with scoring prompt
#   * Return score and explanation
#
# - generate_tailored_bullets(jd_text, chunks) -> bullet_points
#   * Use chunks as context (from VectorService)
#   * Call llm_client.py with tailoring prompt
#   * Return bullet points
#
# Responsibilities:
# - Orchestrate calls between LLM and StoringService
# - Build prompts for different operations
# - Parse and format LLM responses

