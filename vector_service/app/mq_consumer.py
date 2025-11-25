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

# vector_service/app/mq_consumer.py

import json
import os
import threading
from typing import Callable

import pika


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE", "cv.created")


def _run_consumer(process_cv_fn: Callable[[str], None]) -> None:
    """
    Blocking consumer loop. Should be run in a background thread.
    """
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    def callback(ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
            cv_id = payload.get("cv_id")
            if cv_id:
                # process_cv_fn can be async; for simplicity we call it sync via loop later if needed
                import asyncio
                asyncio.run(process_cv_fn(cv_id))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            # For now: nack without requeue to avoid infinite loops
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    try:
        channel.start_consuming()
    finally:
        connection.close()


def start_consumer(process_cv_fn: Callable[[str], None]) -> None:
    """
    Start RabbitMQ consumer in a background thread.
    """
    thread = threading.Thread(
        target=_run_consumer,
        args=(process_cv_fn,),
        daemon=True,
    )
    thread.start()
