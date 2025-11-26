import time
import traceback
import pika
import json
import os
from dotenv import load_dotenv
from app.service import process_cv_for_embedding

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "cv_embedding_queue")

def callback(ch, method, properties, body):
    """
    Process CV when message received from RabbitMQ
    """
    cv_id = None
    try:
        data = json.loads(body)
        cv_id = data.get("cv_id")
        
        if not cv_id:
            print("Error: No cv_id in message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        print(f"Received cv_id from RabbitMQ: {cv_id}")
        
        # Process CV (fetch, chunk, embed, upload to Pinecone)
        process_cv_for_embedding(cv_id)
        
        # Acknowledge message (remove from queue)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"Successfully processed cv_id: {cv_id}")
        
    except MemoryError as e:
        print(f"CRITICAL: Memory error processing CV {cv_id}: {e}")
        print("This CV cannot be processed due to insufficient memory. Message will NOT be requeued.")
        # Don't requeue memory errors - they will fail again
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    except OSError as e:
        if "paging file" in str(e).lower() or "1455" in str(e):
            print(f"CRITICAL: Paging file error processing CV {cv_id}: {e}")
            print("This CV cannot be processed due to insufficient system resources. Message will NOT be requeued.")
            # Don't requeue paging file errors - they will fail again
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            print(f"OS Error processing CV {cv_id}: {e}")
            # Requeue other OS errors (network issues, etc.)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
    except Exception as e:
        error_msg = str(e).lower()
        # Check if it's a memory/paging file error
        if "paging file" in error_msg or "1455" in error_msg or "memory" in error_msg:
            print(f"CRITICAL: Resource error processing CV {cv_id}: {e}")
            print("Message will NOT be requeued to prevent infinite loop.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            print(f"Error processing CV {cv_id}: {e}")
            # Requeue other errors for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_consumer():
    """
    Start RabbitMQ consumer in background
    Listens for cv.created events and processes them
    """
    while True:
        try:
            print(
                f"[VectorService] Connecting to RabbitMQ at "
                f"{RABBITMQ_HOST}:{RABBITMQ_PORT}, queue={RABBITMQ_QUEUE}"
            )

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                )
            )
            channel = connection.channel()

            # Declare queue (must match publisher)
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

            # Fair dispatch
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=callback,
            )

            print("[VectorService] Consumer started. Waiting for messages...")
            channel.start_consuming()  # blocking

        except Exception as e:
            print(f"[VectorService] Failed to start RabbitMQ consumer: {e!r}")
            traceback.print_exc()
            print("[VectorService] Will retry in 5 seconds...")
            time.sleep(5)
