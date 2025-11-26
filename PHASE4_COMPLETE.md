# Phase 4: Similarity Search & Tailored Bullets ✅

## 🎯 What We Achieved

Successfully implemented **semantic similarity search** and **AI-powered tailored bullet point generation** using RAG (Retrieval-Augmented Generation). The system can now find relevant CV chunks matching job descriptions and generate professional, tailored bullet points.

---

## 📊 Overview

### New Features:
1. **Similar Chunks Search** - Find CV chunks semantically similar to job description
2. **Search Top K CVs** - Find top-k CVs ranked by similarity to job description
3. **Tailored Bullets Generation** - Generate XYZ-format bullet points using RAG
4. **Public Endpoint for Similar CVs** - Get top matching CVs via API

---

## 🔄 Complete Flow: Job Description → Tailored Bullets

```
User Input (Job Description)
    ↓
Frontend / API Gateway
    ↓
1. VectorService: POST /internal/similar_chunks
   - Embeds JD text → 768-dim vector (BGE-base)
   - Queries Pinecone → Cosine similarity search
   - Filters by threshold (score >= 0.75)
   - Returns: All chunks above threshold
    ↓
2. GeminiService: POST /internal/tailored_bullets
   - Receives JD + similar chunks
   - Creates RAG-style prompt
   - Calls Gemini API
   - Generates 5-6 XYZ-format bullets
    ↓
Response: Tailored bullet points ready to use
```

---

## 🛠️ Implementation Details

### 1. Similar Chunks (VectorService)

**Endpoint**: `POST /internal/similar_chunks`

**Approach**: Threshold-based (not fixed top-k)
- Queries top 50 chunks from Pinecone (ranked best to worst)
- Filters by similarity threshold (score >= 0.75)
- Returns ALL chunks above threshold (no fixed limit)

**Why Threshold-Based?**
- Quality over quantity: Only relevant chunks
- No artificial limit: Uses all relevant chunks
- More context for LLM: Better bullet generation
- Adapts to data: Works with 1 CV or 5000 CVs

**Parameters**:
- `jd_text`: Job description text
- `min_score`: Minimum similarity threshold (default: 0.75)
- `max_chunks_to_query`: Max chunks to query from Pinecone (default: 50)

**Response**:
```json
{
  "chunks": [
    {
      "text": "Led development of microservices using FastAPI...",
      "section": "experience",
      "cv_id": "8a5b9213...",
      "score": 0.87
    },
    ...
  ]
}
```

---

### 2. Search Top K CVs (VectorService)

**Endpoint**: `POST /internal/search_top_k_cvs`

**Approach**: Aggregates chunk scores by cv_id

**Flow**:
1. Query top 50 chunks from Pinecone
2. Group chunks by `cv_id`
3. Sum scores for each CV
4. Sort by total score (descending)
5. Return top-k CVs

**Parameters**:
- `jd_text`: Job description text
- `top_k`: Number of top CVs to return (default: 3)
- `raw_top_k`: Chunks to fetch before aggregation (default: 50)

**Response**:
```json
{
  "cvs": [
    {
      "cv_id": "8a5b9213...",
      "score": 1.23
    },
    ...
  ]
}
```

---

### 3. Tailored Bullets (GeminiService)

**Endpoint**: `POST /internal/tailored_bullets`

**Approach**: RAG (Retrieval-Augmented Generation)

**Flow**:
1. Receives job description + similar chunks
2. Creates expert prompt with:
   - JD requirements
   - Chunk text (from experience, projects, skills, etc.)
   - XYZ format instructions
   - Examples and guidelines
3. Calls Gemini API
4. Returns 5-6 tailored bullet points

**XYZ Format**:
- **X** = Action Verb (Led, Developed, Implemented)
- **Y** = Task/Action (What you did, technology used)
- **Z** = Quantifiable Result (Numbers, percentages, impact)

**Parameters**:
- `job_description`: Job description text
- `similar_chunks`: List of chunks with text, section, cv_id, score

**Response**:
```json
{
  "tailored_bullets": [
    "Led development of microservices using FastAPI, reducing API latency by 40%",
    "Implemented CI/CD pipelines with Docker and Kubernetes, improving deployment speed by 3x",
    ...
  ],
  "count": 6
}
```

**Key Features**:
- Uses ACTUAL chunk text (not generic)
- Handles chunks from ANY section (experience, projects, skills, etc.)
- Follows XYZ format for maximum impact
- Professional, ATS-optimized bullets

---

### 4. Public Endpoints (API Gateway)

**New Endpoint**: `POST /api/similar_cvs`
- Finds top-k similar CVs to job description
- Returns CV IDs and similarity scores
- Useful for CV recommendation features

**Existing Endpoint**: `POST /api/tailored_bullets`
- Orchestrates VectorService → GeminiService
- Returns tailored bullets ready to use

---

## 🧪 Testing Guide

### Prerequisites

1. **Start all services** (4 terminals):

**Terminal 1 - StoringService:**
```bash
cd storing_service
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - GeminiService:**
```bash
cd gemini_service
python -m uvicorn app.main:app --reload --port 8002
```

**Terminal 3 - VectorService:**
```bash
cd vector_service
python -m uvicorn app.main:app --reload --port 8003
```

**Terminal 4 - API Gateway:**
```bash
cd api_gateway
python -m uvicorn app.main:app --reload --port 8000
```

2. **Start RabbitMQ** (if not running):
```bash
docker start rabbitmq
```

3. **Verify services**:
- StoringService: `http://localhost:8001/health`
- GeminiService: `http://localhost:8002/health`
- VectorService: `http://localhost:8003/health`
- API Gateway: `http://localhost:8000/health`

---

### Test Job Description

Use this job description for testing:

```
Backend Software Engineer - Cloud Infrastructure

We are seeking a Backend Software Engineer to join our distributed systems team. You'll work on high-scale microservices processing millions of transactions daily.

Requirements:

• 2+ years experience with Java, Spring Boot, and microservices architecture
• Strong understanding of AWS services (Lambda, S3, CloudWatch, SQS)
• Experience with Redis, PostgreSQL, and database optimization
• Proficiency in Docker and containerization
• Kubernetes and Helm for orchestration and deployment
• Experience with CI/CD pipelines (Jenkins, GitLab CI, or similar)
• Knowledge of Terraform or CloudFormation for infrastructure as code
• Strong problem-solving skills and ability to work in Agile teams
• Experience with monitoring tools like Datadog or New Relic
• GraphQL API development experience is a plus

Tech Stack: Java, Spring Boot, Kubernetes, AWS, PostgreSQL, Redis, Terraform, GraphQL

What We Offer:

• Competitive salary and equity
• Remote-first culture
• Professional development budget
```

---

### Test 1: Similar Chunks (VectorService Swagger)

1. Go to: `http://localhost:8003/docs`
2. Find: `POST /internal/similar_chunks`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "jd_text": "Backend Software Engineer - Cloud Infrastructure\n\nWe are seeking a Backend Software Engineer to join our distributed systems team. You'll work on high-scale microservices processing millions of transactions daily.\n\nRequirements:\n\n• 2+ years experience with Java, Spring Boot, and microservices architecture\n• Strong understanding of AWS services (Lambda, S3, CloudWatch, SQS)\n• Experience with Redis, PostgreSQL, and database optimization\n• Proficiency in Docker and containerization\n• Kubernetes and Helm for orchestration and deployment\n• Experience with CI/CD pipelines (Jenkins, GitLab CI, or similar)\n• Knowledge of Terraform or CloudFormation for infrastructure as code\n• Strong problem-solving skills and ability to work in Agile teams\n• Experience with monitoring tools like Datadog or New Relic\n• GraphQL API development experience is a plus\n\nTech Stack: Java, Spring Boot, Kubernetes, AWS, PostgreSQL, Redis, Terraform, GraphQL",
     "min_score": 0.75,
     "max_chunks_to_query": 50
   }
   ```
5. Click "Execute"
6. **Expected**: List of chunks with scores >= 0.75

**What to Check**:
- ✅ Number of chunks returned
- ✅ All scores >= 0.75
- ✅ Chunk sections (experience, projects, etc.)
- ✅ Chunk text content

---

### Test 2: Search Top K CVs (VectorService Swagger)

1. Same Swagger: `http://localhost:8003/docs`
2. Find: `POST /internal/search_top_k_cvs`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "jd_text": "Backend Software Engineer - Cloud Infrastructure\n\nWe are seeking a Backend Software Engineer to join our distributed systems team. You'll work on high-scale microservices processing millions of transactions daily.\n\nRequirements:\n\n• 2+ years experience with Java, Spring Boot, and microservices architecture\n• Strong understanding of AWS services (Lambda, S3, CloudWatch, SQS)\n• Experience with Redis, PostgreSQL, and database optimization\n• Proficiency in Docker and containerization\n• Kubernetes and Helm for orchestration and deployment\n• Experience with CI/CD pipelines (Jenkins, GitLab CI, or similar)\n• Knowledge of Terraform or CloudFormation for infrastructure as code\n• Strong problem-solving skills and ability to work in Agile teams\n• Experience with monitoring tools like Datadog or New Relic\n• GraphQL API development experience is a plus\n\nTech Stack: Java, Spring Boot, Kubernetes, AWS, PostgreSQL, Redis, Terraform, GraphQL",
     "top_k": 3,
     "raw_top_k": 50
   }
   ```
5. Click "Execute"
6. **Expected**: List of CVs with aggregated scores

**What to Check**:
- ✅ CV IDs returned
- ✅ Aggregated scores
- ✅ Count (should match number of CVs you have)

---

### Test 3: Tailored Bullets (API Gateway Swagger)

1. Go to: `http://localhost:8000/docs`
2. Find: `POST /api/tailored_bullets`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "job_description": "Backend Software Engineer - Cloud Infrastructure\n\nWe are seeking a Backend Software Engineer to join our distributed systems team. You'll work on high-scale microservices processing millions of transactions daily.\n\nRequirements:\n\n• 2+ years experience with Java, Spring Boot, and microservices architecture\n• Strong understanding of AWS services (Lambda, S3, CloudWatch, SQS)\n• Experience with Redis, PostgreSQL, and database optimization\n• Proficiency in Docker and containerization\n• Kubernetes and Helm for orchestration and deployment\n• Experience with CI/CD pipelines (Jenkins, GitLab CI, or similar)\n• Knowledge of Terraform or CloudFormation for infrastructure as code\n• Strong problem-solving skills and ability to work in Agile teams\n• Experience with monitoring tools like Datadog or New Relic\n• GraphQL API development experience is a plus\n\nTech Stack: Java, Spring Boot, Kubernetes, AWS, PostgreSQL, Redis, Terraform, GraphQL"
   }
   ```
5. Click "Execute"
6. **Expected**: 5-6 tailored bullet points in XYZ format

**What to Check**:
- ✅ Bullets follow XYZ format
- ✅ Include quantifiable metrics
- ✅ Match job description requirements
- ✅ Based on actual CV chunk content

---

### Test 4: Similar CVs (API Gateway Swagger)

1. Same Swagger: `http://localhost:8000/docs`
2. Find: `POST /api/similar_cvs`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "job_description": "Backend Software Engineer - Cloud Infrastructure\n\nWe are seeking a Backend Software Engineer to join our distributed systems team. You'll work on high-scale microservices processing millions of transactions daily.\n\nRequirements:\n\n• 2+ years experience with Java, Spring Boot, and microservices architecture\n• Strong understanding of AWS services (Lambda, S3, CloudWatch, SQS)\n• Experience with Redis, PostgreSQL, and database optimization\n• Proficiency in Docker and containerization\n• Kubernetes and Helm for orchestration and deployment\n• Experience with CI/CD pipelines (Jenkins, GitLab CI, or similar)\n• Knowledge of Terraform or CloudFormation for infrastructure as code\n• Strong problem-solving skills and ability to work in Agile teams\n• Experience with monitoring tools like Datadog or New Relic\n• GraphQL API development experience is a plus\n\nTech Stack: Java, Spring Boot, Kubernetes, AWS, PostgreSQL, Redis, Terraform, GraphQL",
     "top_k": 3
   }
   ```
5. Click "Execute"
6. **Expected**: Top matching CVs with scores

---

### Test 5: Frontend

1. Start frontend server:
   ```bash
   cd frontend
   python -m http.server 8080
   ```
2. Open: `http://localhost:8080`
3. Paste job description
4. Click "Get Tailored Bullets"
5. **Expected**: Bullets displayed in UI

---

## 📁 Files Modified/Created

### New Files:
- `api_gateway/app/clients/vector_client.py` - HTTP client for VectorService

### Modified Files:
- `vector_service/app/service.py` - Added `find_similar_chunks()` and `search_top_k_cvs()`
- `vector_service/app/api.py` - Added internal endpoints
- `vector_service/app/embedder.py` - Added `embed_text()` function
- `vector_service/app/pinecone_client.py` - Added `query_similar()` function
- `gemini_service/app/llm_client.py` - Added tailored bullets prompt and function
- `gemini_service/app/service.py` - Added `generate_tailored_bullets()`
- `gemini_service/app/api.py` - Added `/internal/tailored_bullets` endpoint
- `api_gateway/app/routes.py` - Added `/api/tailored_bullets` and `/api/similar_cvs`
- `api_gateway/app/clients/gemini_client.py` - Added `generate_tailored_bullets()`
- `frontend/index.html` - Added tailored bullets button
- `frontend/app.js` - Added `generateTailoredBullets()` function
- `frontend/styles.css` - Added bullets display styles

---

## 🎓 Technical Decisions

### 1. Why Threshold-Based Approach?

**Decision**: Use similarity threshold (0.75) instead of fixed top-k

**Reasoning**:
- **Quality**: Only relevant chunks (score >= 0.75)
- **No Limit**: Uses all relevant chunks (not capped at 10)
- **Better Context**: More chunks = better LLM understanding
- **Adaptive**: Works with 1 CV or 5000 CVs

**Trade-off**: Might return 0 chunks if no matches above threshold (handled gracefully)

---

### 2. Why 50 Chunks Query Limit?

**Decision**: Query top 50 chunks, then filter by threshold

**Reasoning**:
- **Performance**: Faster than querying 100+
- **Quality**: Top 50 are most relevant (ranked by Pinecone)
- **Balance**: Good trade-off between speed and coverage
- **Safety**: Prevents excessive queries

---

### 3. Why RAG for Tailored Bullets?

**Decision**: Use RAG (Retrieval-Augmented Generation) instead of generating from scratch

**Reasoning**:
- **Accuracy**: Uses actual CV content (not generic)
- **Relevance**: Chunks matched to JD requirements
- **Quality**: Better bullets with real experience/projects
- **Context**: LLM has rich context from chunks

---

## 📊 Expected Results

### With 1 CV (20 chunks):
- Similar chunks: 5-15 chunks (depending on JD match)
- Tailored bullets: 5-6 bullets based on your CV
- Quality: Good, but limited to one CV's content

### With 5000 CVs (100,000+ chunks):
- Similar chunks: 10-50 chunks (diverse sources)
- Tailored bullets: 5-6 bullets from best matches
- Quality: Excellent, diverse, highly relevant

---

## 🚀 Next Phase: 5000 CVs Batch Upload

### Plan Overview

**Goal**: Upload 5000 structured CVs to MongoDB and embed them in Pinecone

### Strategy:

1. **MongoDB**:
   - **Collection**: `cvs_batch_5000` (new collection, separate from `cvs`)
   - **Structure**: Same as existing CVs
   - **cv_id**: SHA256 hash (calculated from structured_sections or raw text)
   - **Purpose**: Keep batch data separate from user-uploaded CVs

2. **Pinecone**:
   - **Index**: Same index (`tailorcv-cv-chunks`)
   - **Chunks**: Each CV chunked and embedded
   - **cv_id**: Same SHA256 hash as MongoDB document
   - **Purpose**: All chunks together for semantic search

3. **Process**:
   - Read 5000 structured CVs (JSON format)
   - For each CV:
     a. Calculate SHA256 hash → `cv_id`
     b. Insert into MongoDB collection `cvs_batch_5000`
     c. Chunk using existing `chunk_structured_sections()` function
     d. Embed chunks using existing `embed_chunks()` function
     e. Upload to Pinecone with same `cv_id`
   - **No RabbitMQ**: Direct processing (bypass async flow)

### Key Requirements:

1. **Consistent cv_id**:
   - Calculate SHA256 from structured_sections JSON string
   - Use same hash for MongoDB document and Pinecone chunks
   - Ensures chunks link back to correct CV

2. **Chunk ID Format**:
   - Pinecone chunk IDs: `{cv_id}_{section}_{chunk_index}`
   - Example: `abc123_experience_0`, `abc123_projects_5`
   - Same format as existing chunks

3. **Reuse Existing Functions**:
   - `chunk_structured_sections()` from `embedder.py`
   - `chunk_experience_bullets()` from `embedder.py`
   - `chunk_projects_bullets()` from `embedder.py`
   - `embed_chunks()` from `embedder.py`
   - `upsert_chunks_to_pinecone()` from `pinecone_client.py`

4. **Error Handling**:
   - Continue on individual CV failures
   - Log progress and errors
   - Track success/failure counts

### Script Structure (Future Implementation):

```python
# batch_upload_5000.py (to be created)

1. Load 5000 CVs from dataset (JSON files or single JSON array)
2. For each CV:
   a. Calculate cv_id = SHA256(structured_sections)
   b. Check if already exists (skip duplicates)
   c. Insert into MongoDB: cvs_batch_5000 collection
   d. Chunk CV using embedder functions
   e. Embed chunks using BGE-base
   f. Upload to Pinecone (same index, same cv_id)
   g. Log progress
3. Summary: X CVs processed, Y chunks uploaded
```

### Benefits:

- **Separation**: Batch CVs in separate collection
- **Consistency**: Same cv_id in MongoDB and Pinecone
- **Reusability**: Uses existing chunking/embedding logic
- **Scalability**: Can process 5000 CVs efficiently
- **Search**: All chunks searchable together

---

## ✅ Phase 4 Status: COMPLETE

- ✅ Similar chunks search (threshold-based)
- ✅ Search top K CVs (aggregation)
- ✅ Tailored bullets generation (RAG)
- ✅ Public endpoints
- ✅ Frontend integration
- ✅ Testing procedures documented

**Next**: 5000 CVs batch upload (Phase 5)

---

## 📝 Summary

Phase 4 successfully implements semantic search and AI-powered bullet generation. The system can now:
- Find relevant CV chunks matching job descriptions
- Rank CVs by similarity
- Generate professional, tailored bullet points using RAG
- Provide public APIs for integration

The threshold-based approach ensures quality while using all relevant chunks for better LLM context.

