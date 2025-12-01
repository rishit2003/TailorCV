from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="TailorCV API Gateway",
    description="Public API Gateway for TailorCV - CV Analysis Platform",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api_gateway"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TailorCV API Gateway",
        "docs": "/docs",
        "health": "/health"
    }
