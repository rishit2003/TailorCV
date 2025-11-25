# HTTP Client for StoringService
# VectorService uses this to fetch CV data for embedding
#
# Internal API calls:
# - getCV(cv_id) -> structured_json
#
# Usage:
# - Called by mq_consumer.py when processing cv.created event
# - Fetches CV data to chunk and embed
#
# Responsibilities:
# - Build HTTP requests to StoringService endpoints
# - Handle connection errors and retries (critical for async processing)
# - Parse responses

# vector_service/app/storing_client.py

import os
from typing import Any, Dict

import httpx


STORING_SERVICE_URL = os.getenv("STORING_SERVICE_URL", "http://localhost:8001")


class StoringClientError(Exception):
    pass


async def get_cv(cv_id: str) -> Dict[str, Any]:
    """
    Fetch CV document from StoringService.
    Internal endpoint expected: GET /internal/get_cv/{cv_id}
    """
    url = f"{STORING_SERVICE_URL}/internal/get_cv/{cv_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
    except httpx.RequestError as exc:
        raise StoringClientError(f"Error connecting to StoringService: {exc}") from exc

    if resp.status_code >= 400:
        raise StoringClientError(
            f"StoringService returned {resp.status_code}: {resp.text}"
        )

    return resp.json()
