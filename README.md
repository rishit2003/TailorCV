# TailorCV - AI-Powered CV Optimization Platform

TailorCV is a microservices-based platform that helps users optimize their CVs for specific job descriptions using AI. The system structures CVs, identifies missing keywords, scores CV-JD alignment, finds similar CVs, and generates tailored bullet points.

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Components](#system-components)
- [Public API Endpoints](#public-api-endpoints)
- [Data Flow & Architecture Decisions](#data-flow--architecture-decisions)
- [Folder Structure](#folder-structure)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Service Details](#service-details)

---

## 🏗️ Architecture Overview

TailorCV follows a **microservices architecture** with 4 independent services:

```
Client
   ↓
API Gateway (0)
   ↓
   ├─→ StoringService (1) ←→ MongoDB (5) + Redis (4)
   ├─→ GeminiService (2)
   └─→ VectorService (3) ←→ VectorDB/Pinecone (7)
```

### Architecture Diagram
<img width="468" height="228" alt="architecture_diagram" src="https://github.com/user-attachments/assets/7f7a7cb7-568e-4f92-8dae-7528a6e20215" />

*High-level microservices architecture showing API Gateway, StoringService, GeminiService, VectorService, and supporting infrastructure.*

### Key Design Principles

1. **Service Independence**: Each service is independently deployable with its own dependencies
2. **Async Processing**: Background embedding via RabbitMQ for non-blocking user experience
3. **Deduplication**: Hash-based CV deduplication to prevent duplicate storage and embeddings
4. **Caching**: Redis for fast retrieval of latest CV
5. **Semantic Search**: Vector embeddings for intelligent CV matching

---

## 🧩 System Components

### Services

| Service | Port | Responsibility | Dependencies |
|---------|------|---------------|--------------|
| **API Gateway** | 8000 | Routes client requests, orchestrates service calls | None |
| **StoringService** | 8001 | CV storage, retrieval, deduplication | MongoDB, Redis, RabbitMQ |
| **GeminiService** | 8002 | LLM operations (structuring, analysis) | Gemini API |
| **VectorService** | 8003 | Embedding generation, semantic search | Pinecone, BGE-large model |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| **MongoDB (5)** | Primary CV storage (owned by StoringService) |
| **Redis (4)** | Cache for latest CV lookup (owned by StoringService) |
| **RabbitMQ (6)** | Event queue for async embedding (cv.created events) |
| **Pinecone (7)** | Vector database for semantic search (owned by VectorService) |

---

## 🌐 Public API Endpoints

All endpoints are exposed through the **API Gateway** on port 8000.

### Client Interface
<img width="1104" height="1337" alt="frontend" src="https://github.com/user-attachments/assets/3583d429-de4d-4e5a-b420-a66841a8b891" />

*Example client interface used to upload CVs, analyze job descriptions, and view results.*

### 1. `POST /attach_cv`
**Upload and structure a CV**

**Request:**
```json
{
  "cv_file": "file upload",
  "cv_text": "raw CV text (alternative to file)"
}
```

**Response:**
```json
{
  "status": "success",
  "cv_id": "sha256_hash_value",
  "message": "CV uploaded and queued for embedding"
}
```

**Flow:**
1. Gateway extracts CV text from file
2. Calls GeminiService → `structure-cv` (returns structured JSON)
3. Calls StoringService → `StoreCV` (saves to MongoDB, publishes to RabbitMQ)
4. Returns cv_id to client
5. **Background:** VectorService consumes event → embeds CV → stores in Pinecone

---

### 2. `POST /keywords`
**Find missing keywords in CV for a job description**

**Request:**
```json
{
  "cv_id": "sha256_hash_value",
  "job_description": "We are looking for a Senior Python Developer..."
}
```

**Response:**
```json
{
  "missing_keywords": ["FastAPI", "Docker", "Kubernetes"],
  "explanation": "Your CV lacks modern deployment keywords..."
}
```

#### Example Output
<img width="1018" height="669" alt="keyword" src="https://github.com/user-attachments/assets/1646adcd-ea48-4492-8b2d-6f68a207f4c2" />


**Flow:**
1. Gateway → GeminiService `missing-keywords`
2. GeminiService internally calls StoringService `getCV(cv_id)`
3. Gemini API analyzes CV + JD
4. Returns missing keywords

---

### 3. `POST /score`
**Score CV alignment with job description**

**Request:**
```json
{
  "cv_id": "sha256_hash_value",
  "job_description": "We are looking for a Senior Python Developer..."
}
```

**Response:**
```json
{
  "score": 85,
  "explanation": "Strong match due to Python experience and ML projects..."
}
```

#### Example Output
<img width="868" height="1228" alt="score" src="https://github.com/user-attachments/assets/0d1e1458-5e0b-4d6c-b20c-b19740874da6" />

**Flow:**
1. Gateway → GeminiService `score`
2. GeminiService internally calls StoringService `getCV(cv_id)`
3. Gemini API scores CV-JD alignment
4. Returns score and explanation

---

### 4. `POST /similar_cvs`
**Find top-k CVs similar to a job description**

**Request:**
```json
{
  "job_description": "We are looking for a Senior Python Developer...",
  "top_k": 3
}
```

**Response:**
```json
{
  "similar_cvs": [
    {
      "cv_id": "hash1",
      "score": 0.92,
      "cv_summary": {...}
    },
    {
      "cv_id": "hash2",
      "score": 0.87,
      "cv_summary": {...}
    }
  ]
}
```

**Flow:**
1. Gateway → VectorService `search-top-k-cvs`
2. VectorService embeds JD, queries Pinecone, aggregates by cv_id
3. Gateway → StoringService `getCV` for each returned cv_id
4. Returns CVs with scores

---

### 5. `POST /tailored_points`
**Generate tailored bullet points for a job description**

**Request:**
```json
{
  "job_description": "We are looking for a Senior Python Developer...",
  "num_chunks": 5
}
```

**Response:**
```json
{
  "tailored_bullets": [
    "Architected scalable Python microservices handling 10M+ requests/day",
    "Led team of 5 engineers in migrating monolith to FastAPI services",
    "..."
  ]
}
```

#### Example Output
<img width="866" height="578" alt="bullets" src="https://github.com/user-attachments/assets/628bef24-8b67-44eb-8fa9-c613cde0a6ed" />


**Flow:**
1. Gateway → VectorService `similar-chunks` (get relevant CV chunks)
2. Gateway → GeminiService `tailored-bullets` (with JD + chunks as context)
3. Gemini generates tailored bullet points
4. Returns bullets to client

---

### 6. `GET /my_cv`
**Get the most recently uploaded CV**

**Request:**
```
GET /my_cv
```

**Response:**
```json
{
  "cv_id": "sha256_hash_value",
  "structured_cv": {
    "experience": [...],
    "projects": [...],
    "skills": [...],
    "education": [...]
  },
  "created_at": "2025-11-19T10:30:00Z"
}
```

**Flow:**
1. Gateway → StoringService `getLatestCV()`
2. StoringService checks Redis `latest_cv` key
3. Fetches CV from MongoDB
4. Returns structured CV

---

### 7. `POST /upload_cvs` *(Optional - Future)*
**Batch upload multiple CVs**

Same as `/attach_cv` but processes multiple files in batch.

---

## 🔄 Data Flow & Architecture Decisions

### Hash-Based Deduplication Strategy

**Problem:** If the same CV is uploaded multiple times, we don't want duplicate storage and embeddings.

**Solution:** Use SHA256 hash of CV text as the primary identifier (`cv_id`).

#### MongoDB Document Structure

```javascript
{
  "_id": ObjectId("..."),           // MongoDB auto-generated (internal use only)
  "cv_id": "sha256_hash",           // OUR primary identifier (hash of CV text)
  "cv_text": "original text...",    // Raw CV text
  "structured_json": {              // Structured sections from GeminiService
    "experience": [...],
    "projects": [...],
    "skills": [...],
    "education": [...]
  },
  "created_at": "2025-11-19T10:30:00Z",
  "updated_at": "2025-11-19T10:30:00Z"
}
```

#### Stored CV Documents
<img width="1149" height="1276" alt="database" src="https://github.com/user-attachments/assets/dd71e261-31fd-48e0-8640-c6062c9fb2b2" />

#### StoreCV Logic with Deduplication

```
1. Receive structured_json_cv and cv_text from GeminiService
2. Calculate: cv_id = SHA256(cv_text)
3. Check MongoDB: Does document with cv_id exist?
   
   If YES (duplicate):
     ✓ Return existing cv_id
     ✓ Update Redis: latest_cv = cv_id
     ✗ DON'T publish to RabbitMQ (already embedded)
     ✗ DON'T create new MongoDB entry
   
   If NO (new CV):
     ✓ Insert new document with cv_id
     ✓ Update Redis: latest_cv = cv_id
     ✓ Publish cv_id to RabbitMQ for embedding
     
4. Return cv_id to Gateway
```

#### Benefits

**Deduplication**: Same CV uploaded 100 times = stored once  
**Cost Savings**: Only embed unique CVs (Pinecone + compute costs)  
**Consistency**: Same `cv_id` used across MongoDB, Redis, RabbitMQ, Pinecone  
**Idempotency**: Upload operations are safe to repeat  
**Clean VectorDB**: No duplicate embeddings in search results  

#### CV Updates

**Important:** If you update your CV (even 1 word), the hash changes → **new cv_id** → treated as a **new CV**.

This is the **desired behavior** because:
- Updated CV is genuinely different
- Should have its own embedding
- Preserves version history
- Allows comparing old vs new CV versions

---

### Redis Caching Strategy

**Key:** `latest_cv`  
**Value:** `cv_id` (SHA256 hash)  
**Meaning:** The most recently uploaded CV in the entire system

#### Why This Design?

- ✅ Simple: Single key, no user management needed
- ✅ Fast: O(1) lookup for latest CV
- ✅ Stateless: No authentication required
- ✅ Clean: Every `StoreCV` updates this one key

#### getLatestCV Flow

```
1. Redis GET latest_cv → returns cv_id
2. If found: MongoDB find({cv_id: ...})
3. If not found: MongoDB find().sort({created_at: -1}).limit(1)
4. Return structured CV JSON
```

---

### Async Embedding Pipeline

**Problem:** Embedding generation is slow (BGE-large inference + Pinecone upsert).

**Solution:** Background processing via RabbitMQ.

#### Event Flow

```
User uploads CV
    ↓
StoringService saves to MongoDB
    ↓
StoringService publishes to RabbitMQ
    ↓
User receives "Upload successful" immediately ✓
    ↓
[Background] VectorService consumes event
    ↓
[Background] Fetches CV from StoringService
    ↓
[Background] Chunks CV by sections
    ↓
[Background] Embeds with BGE-large
    ↓
[Background] Upserts to Pinecone
```

#### RabbitMQ Event

**Queue:** `cv_events`  
**Event Type:** `cv.created`

**Payload:**
```json
{
  "cv_id": "sha256_hash_value"
}
```

#### Benefits

✅ **Fast user response**: Upload returns in <1s  
✅ **Scalable**: Can scale VectorService consumers independently  
✅ **Resilient**: Retries on failure, dead letter queue  
✅ **Decoupled**: StoringService doesn't wait for embedding  

---

### Chunking Strategy

**Approach:** Chunk CV by **sections** (not fixed-size text chunks).

Each section in the structured CV JSON becomes **one chunk**:
- Experience section → 1 chunk
- Projects section → 1 chunk
- Skills section → 1 chunk
- Education section → 1 chunk

#### Pinecone Vector Metadata

```javascript
{
  "cv_id": "sha256_hash",           // Link back to MongoDB
  "section": "experience",          // Section type
  "raw_text": "Worked at XYZ..."   // Chunk content
}
```

#### Pinecone Index View
<img width="2247" height="1217" alt="pinecone" src="https://github.com/user-attachments/assets/5977751f-5659-4cee-81c0-9174db0016f6" />


#### Why Section-Based Chunking?

**Semantic coherence**: Each chunk is topically related  
**Clean metadata**: Easy to filter by section  
**Right granularity**: Not too small, not too large  
**Simple implementation**: Matches JSON structure  

#### Future Consideration

If a section is very large (e.g., 10 jobs in experience), consider splitting into:
- Experience_1, Experience_2, etc.
- Add `chunk_index` to metadata

---

### Inter-Service Communication

**Protocol:** REST HTTP (JSON)

#### Why REST?

**Simple**: Standard HTTP/JSON  
**Debug-friendly**: Use curl/Postman for testing  
**Language agnostic**: Easy to replace services  
**Familiar**: Most developers know REST  

#### Service URLs

- API Gateway: `http://localhost:8000`
- StoringService: `http://localhost:8001`
- GeminiService: `http://localhost:8002`
- VectorService: `http://localhost:8003`

#### Internal APIs

**StoringService:**
- `POST /internal/store_cv` - Store CV with deduplication
- `GET /internal/get_cv/{cv_id}` - Fetch CV by hash
- `GET /internal/get_latest_cv` - Fetch latest CV

**GeminiService:**
- `POST /internal/structure_cv` - Structure raw CV text
- `POST /internal/missing_keywords` - Find missing keywords
- `POST /internal/score` - Score CV against JD
- `POST /internal/tailored_bullets` - Generate bullet points

**VectorService:**
- `POST /internal/similar_chunks` - Find similar CV chunks
- `POST /internal/search_top_k_cvs` - Find top-k similar CVs

---

## 📁 Folder Structure

```
TailorCV/
├── api_gateway/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── routes.py                   # Public endpoints
│   │   └── clients/
│   │       ├── storing_client.py       # HTTP client to StoringService
│   │       ├── gemini_client.py        # HTTP client to GeminiService
│   │       └── vector_client.py        # HTTP client to VectorService
│   ├── requirements.txt
│   └── Dockerfile
│
├── storing_service/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── api.py                      # Internal API endpoints
│   │   ├── service.py                  # Business logic (deduplication, storage)
│   │   ├── events.py                   # RabbitMQ publisher
│   │   ├── db_mongo.py                 # MongoDB operations
│   │   └── db_redis.py                 # Redis operations
│   ├── requirements.txt
│   └── Dockerfile
│
├── gemini_service/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── api.py                      # Internal API endpoints
│   │   ├── service.py                  # LLM orchestration logic
│   │   ├── llm_client.py               # Gemini API wrapper
│   │   └── storing_client.py           # HTTP client to StoringService
│   ├── requirements.txt
│   └── Dockerfile
│
├── vector_service/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── api.py                      # Internal API endpoints
│   │   ├── service.py                  # Embedding & search logic
│   │   ├── mq_consumer.py              # RabbitMQ consumer (background)
│   │   ├── pinecone_client.py          # Pinecone operations
│   │   ├── embedder.py                 # BGE-large model wrapper
│   │   └── storing_client.py           # HTTP client to StoringService
│   ├── requirements.txt
│   └── Dockerfile
│
├── infra/
│   ├── docker-compose.yml              # Local dev environment
│   └── configs/                        # Shared configs (if needed)
│
├── .env.example                        # Environment variables template
├── .gitignore
└── README.md
```

---

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI** (Python 3.11+) - All services

### Databases
- **MongoDB** - Primary CV storage (StoringService)
- **Redis** - Caching layer (StoringService)
- **Pinecone** - Vector database for embeddings (VectorService)

### Message Queue
- **RabbitMQ** - Async event processing

### AI/ML
- **Google Gemini API** - LLM for CV analysis
- **BGE-large (BAAI/bge-large-en-v1.5)** - Embedding model
- **Hugging Face Transformers** - Model loading

### Dependencies per Service

**API Gateway:**
- `fastapi`, `uvicorn`, `httpx`, `pydantic`

**StoringService:**
- `fastapi`, `pymongo`, `redis`, `pika` (RabbitMQ)

**GeminiService:**
- `fastapi`, `google-generativeai`, `httpx`

**VectorService:**
- `fastapi`, `pinecone-client`, `transformers`, `torch`, `pika`

---

## 🚀 Getting Started
TailorCV is fully Dockerized and can be started with a single command using Docker Compose.

### Prerequisites

- Docker & Docker Compose
- Pinecone account & API key
- Google Gemini API key
**Note: Python is only required if running services outside Docker (development mode).**

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/TailorCV.git
cd TailorCV
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## 🐳 Run with Docker (Recommended)

4. **Start infrastructure (MongoDB, Redis, RabbitMQ)**
```bash
cd infra
docker-compose up -d
```

5. **Run services (in separate terminals)**
```bash
# Terminal 1 - StoringService
cd storing_service
uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2 - GeminiService
cd gemini_service
uvicorn app.main:app --host 0.0.0.0 --port 8002

# Terminal 3 - VectorService
cd vector_service
uvicorn app.main:app --host 0.0.0.0 --port 8003

# Terminal 4 - API Gateway
cd api_gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

6. **Test the system**
```bash
curl -X POST http://localhost:8000/attach_cv \
  -F "cv_file=@my_cv.pdf"
```

---

## 📖 Service Details

### API Gateway (Port 8000)

**Responsibility:** Route client requests to appropriate services

**Key Files:**
- `routes.py` - All 7 public endpoints
- `clients/` - HTTP clients for inter-service communication

**No business logic** - pure orchestration layer.

---

### StoringService (Port 8001)

**Responsibility:** CV storage, retrieval, deduplication

**Key Features:**
- Hash-based deduplication (SHA256)
- MongoDB as primary storage
- Redis for latest CV caching
- RabbitMQ event publishing

**Key Files:**
- `api.py` - Internal endpoints (store, get, getLatest)
- `service.py` - Deduplication logic
- `db_mongo.py` - MongoDB operations
- `db_redis.py` - Redis operations
- `events.py` - RabbitMQ publisher

**Database:** `tailorcv_db`  
**Collection:** `cvs`

---

### GeminiService (Port 8002)

**Responsibility:** All LLM operations

**Key Features:**
- CV structuring (raw text → JSON)
- Missing keywords analysis
- CV-JD scoring
- Tailored bullet generation

**Key Files:**
- `api.py` - Internal endpoints (4 LLM operations)
- `service.py` - LLM orchestration
- `llm_client.py` - Gemini API wrapper
- `storing_client.py` - Fetch CVs from StoringService

**External Dependency:** Google Gemini API

---

### VectorService (Port 8003)

**Responsibility:** Embedding generation & semantic search

**Key Features:**
- BGE-large embeddings (1024-dim)
- Pinecone vector storage
- Semantic similarity search
- Background embedding via RabbitMQ consumer

**Key Files:**
- `api.py` - Internal endpoints (similar chunks, top-k CVs)
- `service.py` - Chunking & embedding logic
- `mq_consumer.py` - RabbitMQ consumer (background)
- `embedder.py` - BGE-large model wrapper
- `pinecone_client.py` - Pinecone operations
- `storing_client.py` - Fetch CVs for embedding

**Embedding Model:** Hugging Face BGE-large (Hugging Face)  
**Vector Database:** Pinecone

---

## 🔒 Security Considerations (Future)

- **No authentication currently** - suitable for MVP/demo
- Future considerations:
  - JWT-based auth in API Gateway
  - User accounts and multi-tenancy
  - API rate limiting
  - Input validation and sanitization

---

## 📊 Monitoring & Observability (Future)

- Health check endpoints on all services
- Structured logging
- Metrics (Prometheus)
- Distributed tracing (Jaeger)

---

## 🧪 Testing Strategy (Future)

Each service will have:
- Unit tests for business logic
- Integration tests for API endpoints
- End-to-end tests for full flows

---

## ☁️ Deployment Notes

TailorCV was successfully deployed on a **Google Cloud Platform (GCP) virtual machine** using Dockerized microservices.

Due to **budget constraints**, the cloud deployment is currently **not kept running 24/7**.  
The system is fully reproducible locally using Docker Compose and can be redeployed to GCP at any time.

This deployment validated:
- Service-to-service communication
- RabbitMQ async pipelines
- Pinecone and Gemini API integration in a cloud environment

---

