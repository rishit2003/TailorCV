# Dockerfile for VectorService
# This will be used for containerized deployment
# Note: Larger image due to ML models (transformers, torch)

# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY ./app ./app
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

# vector_service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps (optional: helps some ML libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY ./app ./app

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
