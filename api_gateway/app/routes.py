# API Gateway - Public Endpoints
# Defines all 7 public endpoints exposed to clients
# 
# Endpoints:
# 1. POST /attach_cv - Upload and structure a CV
# 2. POST /keywords - Get missing keywords for a CV against a job description
# 3. POST /score - Score a CV against a job description
# 4. POST /similar_cvs - Find top-k similar CVs to a job description
# 5. POST /tailored_points - Generate tailored bullet points
# 6. GET /my_cv - Get the latest uploaded CV
# 7. POST /upload_cvs (optional, later) - Batch upload multiple CVs
#
# Responsibilities:
# - Route orchestration ONLY (no business logic)
# - Call appropriate services via HTTP clients
# - Combine responses from multiple services when needed
# - Return formatted responses to client

