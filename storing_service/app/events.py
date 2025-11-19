# StoringService - RabbitMQ Event Publisher
# Publishes events when new CVs are stored
#
# Event: cv.created
# Payload: {
#   "cv_id": "sha256_hash_value"
# }
#
# Flow:
# - Called by service.py after successful CV insertion
# - Publishes to RabbitMQ exchange/queue
# - VectorService consumes this event for background embedding
#
# Responsibilities:
# - Establish RabbitMQ connection
# - Publish cv.created events
# - Handle connection failures gracefully

