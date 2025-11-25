# VectorService - FastAPI Application Entry Point
# This service handles embeddings and semantic search
#
# Responsibilities:
# - Initialize FastAPI application
# - Register internal API routes from api.py
# - Initialize BGE-large embedding model
# - Initialize Pinecone VectorDB client
# - Start RabbitMQ consumer in background
# - Initialize HTTP client to StoringService
# - Health check endpoint

# vector_service/app/main.py

from fastapi import FastAPI

from .api import router as internal_router
from .pinecone_client import PineconeVectorClient
from . import service


app = FastAPI(
    title="TailorCV VectorService",
    version="0.1.0",
    description="Handles embeddings and semantic search for CVs.",
)

# Register internal routes
app.include_router(internal_router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """
    Initialize dependencies on startup.
    """
    # Initialize Pinecone vector client
    vector_client = PineconeVectorClient()
    service.init_dependencies(vector_client)

    # Optional: start RabbitMQ consumer here when ready
    # from .mq_consumer import start_consumer
    # start_consumer(service.process_cv_for_embedding)
