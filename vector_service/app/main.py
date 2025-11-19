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

