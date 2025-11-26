from fastapi import FastAPI
import threading
from app.mq_consumer import start_consumer
from app.api import router

app = FastAPI(title="VectorService", version="1.0.0")
app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vector_service"}

@app.on_event("startup")
async def startup_event():
    """Start RabbitMQ consumer in background thread"""
    print("Starting VectorService...")
    
    # Start consumer in background thread (non-blocking)
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    
    print("VectorService started. RabbitMQ consumer running in background.")

@app.get("/")
async def root():
    return {"message": "VectorService", "docs": "/docs"}
