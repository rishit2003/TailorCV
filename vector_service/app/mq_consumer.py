# VectorService - RabbitMQ Event Consumer
# Listens to cv.created events from StoringService
#
# Event: cv.created
# Payload: {
#   "cv_id": "sha256_hash_value"
# }
#
# Flow:
# 1. Consume message from RabbitMQ queue
# 2. Extract cv_id from payload
# 3. Call service.process_cv_for_embedding(cv_id)
# 4. Acknowledge message after successful processing
#
# Background Processing:
# - Runs in separate thread/process
# - Does NOT block API endpoints
# - Provides async embedding generation
#
# Error Handling:
# - If embedding fails: log error, nack message for retry
# - If StoringService down: retry with backoff
#
# Responsibilities:
# - RabbitMQ connection and subscription
# - Message consumption and acknowledgment
# - Trigger background embedding pipeline

