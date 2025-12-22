# Phase 3: CV Embedding & Vector Database Integration ✅

## 🎯 What We Achieved

Successfully implemented **asynchronous CV embedding** using RabbitMQ, BGE-base model, and Pinecone VectorDB. CVs are now automatically chunked, embedded, and stored for semantic search.

---

## 📊 Understanding the SCORE in Pinecone

The **SCORE** you see (e.g., 0.7031, 0.5069) is a **cosine similarity score** from Pinecone vector search:

- **Range**: 0.0 to 1.0
- **Meaning**: How similar a CV chunk is to your search query
- **0.7+**: Very relevant match
- **0.5-0.7**: Moderate match
- **<0.5**: Weak match

**Example**: If you search for "Python developer", chunks with Python experience will have scores like 0.85, while unrelated chunks might be 0.30.

**Note**: This is different from the CV scoring system (0-100) used in the `/api/score` endpoint.

---

## 🔄 Complete Flow: Upload to Pinecone Storage

### Step-by-Step Flow Diagram

```
┌─────────────┐
│  Frontend   │ User uploads CV (text or PDF)
└──────┬──────┘
       │ POST /api/upload_cv_text or /api/upload_cv_pdf
       ▼
┌─────────────────┐
│  API Gateway     │ Extracts PDF text (if PDF), forwards to services
│  (Port 8000)     │
└──────┬───────────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
       ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│ GeminiService    │                    │ StoringService   │
│ (Port 8002)      │                    │ (Port 8001)      │
│                  │                    │                  │
│ Structures CV    │                    │ Stores in MongoDB│
│ using Gemini AI  │                    │ Calculates hash  │
│                  │                    │ (cv_id)          │
└──────┬───────────┘                    └──────┬───────────┘
       │                                       │
       │ Returns structured_sections           │
       │                                       │
       └──────────────────┬────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   StoringService      │
              │   Publishes Event     │
              └───────────┬───────────┘
                          │
                          │ publish_cv_event(cv_id)
                          │
                          ▼
              ┌───────────────────────┐
              │   RabbitMQ Queue      │
              │   cv_embedding_queue  │
              │                       │
              │   Message:            │
              │   {"cv_id": "..."}    │
              │                       │
              │   📈 SPIKE APPEARS    │
              │   (Unacked: 1)        │
              └───────────┬───────────┘
                          │
                          │ Consumer picks up message
                          │
                          ▼
              ┌───────────────────────┐
              │   VectorService       │
              │   (Port 8003)         │
              │                       │
              │   1. Fetch CV from    │
              │      StoringService   │
              │   2. Chunk sections   │
              │   3. Embed chunks     │
              │   4. Upload to        │
              │      Pinecone         │
              │   5. ACK message      │
              └───────────┬───────────┘
                          │
                          │ Message acknowledged
                          │
                          ▼
              ┌───────────────────────┐
              │   RabbitMQ Queue      │
              │                       │
              │   📉 SPIKE DISAPPEARS │
              │   (Ready: 0)          │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Pinecone VectorDB   │
              │   tailorcv-cv-chunks  │
              │                       │
              │   ✅ 20 chunks stored │
              │   (768-dim vectors)   │
              └───────────────────────┘
```

---

## 📨 RabbitMQ Message Lifecycle

### Timeline Visualization

```
Time    Event                          RabbitMQ Status
─────────────────────────────────────────────────────────
T0      CV uploaded                   Queue: 0 messages
T1      StoringService publishes       Queue: 1 message (Ready)
                                        📈 SPIKE APPEARS
T2      VectorService receives        Queue: 1 message (Unacked)
T3      VectorService processing...    Queue: 1 message (Unacked)
        (fetching, chunking, embedding)
T4      VectorService uploads to       Queue: 1 message (Unacked)
        Pinecone
T5      VectorService ACKs message     Queue: 0 messages
                                        📉 SPIKE DISAPPEARS
```

### Key Points:

1. **Spike Appears**: When `StoringService` publishes `cv_id` to RabbitMQ
2. **Spike Stays**: While `VectorService` is processing (message is "Unacked")
3. **Spike Disappears**: When `VectorService` sends `basic_ack()` after successful upload

### RabbitMQ Dashboard Indicators:

- **Ready**: Messages waiting to be consumed
- **Unacked**: Messages being processed (spike visible)
- **Total**: Ready + Unacked

---

## 🛠️ Phase 3 Implementation Details

### 1. Intelligent Chunking Logic (`vector_service/app/embedder.py`)

**Strategy**: Semantic, type-based chunking for optimal embedding quality.

#### Chunking Rules:

| Section Type | Chunking Strategy | Example |
|-------------|-------------------|---------|
| **Experience** | Each bullet point = 1 chunk | "Led team of 5 developers" → separate chunk |
| **Projects** | Each bullet point = 1 chunk | "Built REST API with FastAPI" → separate chunk |
| **Summary** | Entire text = 1 chunk | Full summary paragraph |
| **Skills** | All skills combined = 1 chunk | "Python, Java, Docker, Kubernetes" |
| **Education** | Each degree = 1 chunk | "BSc Computer Science - Concordia" |
| **Leadership** | Each role = 1 chunk | "Mentor - Co-op - Concordia University" |
| **Certifications** | Each cert = 1 chunk | "AWS Certified Solutions Architect" |

#### Code Structure:

```python
def chunk_structured_sections(structured_sections, cv_id):
    """
    Intelligently chunks CV sections for embedding.
    
    Returns: List of chunks with:
    - cv_id: CV identifier
    - section: Section name (experience, projects, etc.)
    - text: Chunk text content
    - metadata: Additional context (company, title, dates, etc.)
    """
```

**Result**: Your CV created **20 chunks**:
- 9 experience chunks (one per bullet)
- 8 project chunks (one per bullet)
- 3 other chunks (summary, skills, education/leadership)

---

### 2. Embedding Model (`vector_service/app/embedder.py`)

**Model**: `BAAI/bge-base-en-v1.5`
- **Dimension**: 768 (reduced from 1024 to avoid memory issues)
- **Type**: Sentence Transformer
- **Purpose**: Converts text chunks into 768-dimensional vectors

**Why BGE-base instead of BGE-large?**
- BGE-large (1024 dim) caused "paging file too small" errors on Windows
- BGE-base (768 dim) uses less memory and works reliably
- Still provides excellent semantic search quality

**Loading Strategy**:
- Model loaded once on startup (cached globally)
- Reused for all embedding operations
- Prevents repeated downloads

---

### 3. Pinecone Integration (`vector_service/app/pinecone_client.py`)

**Index**: `tailorcv-cv-chunks`
- **Dimension**: 768 (matches BGE-base)
- **Metric**: Cosine similarity
- **Cloud**: AWS (us-east-1)
- **Type**: Serverless

**Auto-Index Management**:
- Detects if index exists
- Checks dimension compatibility
- Auto-deletes and recreates if dimension mismatch (only if empty)
- Prevents dimension errors

**Upsert Strategy**:
- Batch upsert (100 vectors per request)
- Unique IDs: `{cv_id}_{section}_{chunk_index}`
- Metadata includes: `cv_id`, `section`, `text`, and section-specific fields

**Example Vector ID**:
```
8a5b9213..._experience_0
8a5b9213..._projects_11
8a5b9213..._leadership_19
```

---

### 4. RabbitMQ Consumer (`vector_service/app/mq_consumer.py`)

**Queue**: `cv_embedding_queue`
- **Durable**: Yes (survives RabbitMQ restart)
- **Prefetch**: 1 (process one message at a time)

**Error Handling**:
- **Memory/Paging Errors**: NOT requeued (prevents infinite loop)
- **Network Errors**: Requeued for retry
- **Other Errors**: Requeued for retry

**Consumer Flow**:
```python
def callback(ch, method, properties, body):
    1. Parse cv_id from message
    2. Call process_cv_for_embedding(cv_id)
    3. If success: basic_ack() → message removed
    4. If memory error: basic_nack(requeue=False) → message discarded
    5. If other error: basic_nack(requeue=True) → retry later
```

**Key Fix**: Prevents infinite loops by detecting memory errors and NOT requeuing them.

---

### 5. Service Orchestration (`vector_service/app/service.py`)

**Main Function**: `process_cv_for_embedding(cv_id)`

**Flow**:
1. Fetch CV from StoringService (`GET /internal/get_cv/{cv_id}`)
2. Extract `structured_sections` from CV document
3. Chunk sections using intelligent algorithm
4. Embed chunks using BGE-base model
5. Upload embedded chunks to Pinecone

**Error Handling**:
- Raises exceptions on failure
- Consumer handles retry logic
- Logs all steps for debugging

---

## 📈 What Happens in RabbitMQ Dashboard

### Before Upload:
- **Ready**: 0
- **Unacked**: 0
- **Total**: 0
- **Graph**: Flat line at 0

### During Processing:
- **Ready**: 0
- **Unacked**: 1 (message being processed)
- **Total**: 1
- **Graph**: Red spike at 1.0

### After Processing:
- **Ready**: 0
- **Unacked**: 0
- **Total**: 0
- **Graph**: Returns to 0 (spike disappears)

---

## ✅ Testing Results

### Successful Upload:
```
✅ CV uploaded via frontend
✅ Structured by GeminiService
✅ Stored in MongoDB
✅ Published to RabbitMQ
✅ Consumed by VectorService
✅ Chunked into 20 semantic units
✅ Embedded using BGE-base (768-dim)
✅ Uploaded to Pinecone
✅ RabbitMQ message acknowledged
✅ Queue empty
```

### Pinecone Verification:
- **Index**: `tailorcv-cv-chunks`
- **Dimension**: 768 ✅
- **Record Count**: 20 ✅
- **Chunks Visible**: Yes ✅

---

## 🔍 Key Files Modified/Created

### New Files:
- `vector_service/app/embedder.py` - Chunking and embedding logic
- `vector_service/app/pinecone_client.py` - Pinecone integration
- `vector_service/app/mq_consumer.py` - RabbitMQ consumer
- `vector_service/app/service.py` - Service orchestration

### Modified Files:
- `storing_service/app/events.py` - Added RabbitMQ publisher
- `storing_service/app/service.py` - Added publish call after CV storage
- `vector_service/app/main.py` - Added RabbitMQ consumer startup
- `vector_service/requirements.txt` - Added dependencies (pinecone, sentence-transformers, pika)

---

## 🎓 Technical Decisions

### 1. Why Semantic Chunking?
- **Granularity**: Each bullet point is searchable independently
- **Context**: Metadata preserves company, title, dates
- **Quality**: Better embedding quality than large paragraphs

### 2. Why BGE-base?
- **Memory**: Fits in system memory (no paging file errors)
- **Quality**: Still excellent for semantic search
- **Speed**: Faster than BGE-large

### 3. Why Async Processing?
- **Non-blocking**: CV upload returns immediately
- **Scalable**: Can process multiple CVs in parallel
- **Resilient**: Failed CVs don't block new uploads

### 4. Why Pinecone?
- **Managed**: No infrastructure to maintain
- **Fast**: Sub-millisecond search
- **Scalable**: Handles millions of vectors

---

## 🚀 Next Steps (Future Phases)

1. **Similarity Search**: Implement `search_top_k_cvs` endpoint
2. **Tailored Bullets**: Generate job-specific bullet points using similar chunks
3. **Batch Upload**: Process 5000 CVs dataset
4. **Redis Caching**: Cache latest CV for faster retrieval

---

## 📝 Summary

**Phase 3 Status**: ✅ **COMPLETE**

- ✅ Asynchronous embedding pipeline working
- ✅ Intelligent chunking implemented
- ✅ BGE-base embedding integrated
- ✅ Pinecone storage functional
- ✅ RabbitMQ consumer with error handling
- ✅ End-to-end flow tested and verified

**Your CV is now searchable in Pinecone!** 🎉

