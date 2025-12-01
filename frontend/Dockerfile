# Dockerfile (in your frontend folder, same level as index.html)
FROM python:3.11-slim

WORKDIR /app

# Copy static files
COPY . .

# Cloud Run expects the app to listen on $PORT
ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "http.server", "8080"]