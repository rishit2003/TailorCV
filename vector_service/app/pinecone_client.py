# vector_service/app/pinecone_client.py

import os
import logging
from typing import List, Dict, Any

from pinecone import Pinecone  # new SDK
from pinecone import ServerlessSpec

logger = logging.getLogger(__name__)

# Hardcode index settings so teammates can just set API key
INDEX_NAME = "tailorcv-cv-chunks"
INDEX_DIMENSION = 1024   # BGE-large-en-v1.5 output size
INDEX_METRIC = "cosine"
INDEX_CLOUD = "aws"
INDEX_REGION = "us-east-1"   # matches your Pinecone console region


class PineconeVectorClient:
    def __init__(self) -> None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY not set in environment")

        # Initialize client (no environment string needed anymore)
        self.pc = Pinecone(api_key=api_key)

        # Ensure index exists (serverless)
        index_names = [idx["name"] for idx in self.pc.list_indexes()]
        if INDEX_NAME not in index_names:
            logger.info(f"Creating Pinecone index '{INDEX_NAME}'...")
            self.pc.create_index(
                name=INDEX_NAME,
                dimension=INDEX_DIMENSION,
                metric=INDEX_METRIC,
                spec=ServerlessSpec(
                    cloud=INDEX_CLOUD,
                    region=INDEX_REGION,
                ),
                deletion_protection="disabled",
            )

        # Get index host and create handle
        desc = self.pc.describe_index(INDEX_NAME)
        host = desc["host"]
        self.index = self.pc.Index(host=host)
        logger.info(f"Pinecone index '{INDEX_NAME}' ready at host {host}")

    # --- Basic operations used by service.py ---

    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = "default",
    ) -> None:
        """
        vectors: list of dicts like:
        {
          "id": "cv123_experience",
          "values": [...1024 floats...],
          "metadata": {"cv_id": "cv123", "section": "experience", "raw_text": "..."}
        }
        """
        self.index.upsert(
            vectors=[(v["id"], v["values"], v.get("metadata", {})) for v in vectors],
            namespace=namespace,
        )

    def query_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        namespace: str = "default",
        filter: Dict[str, Any] | None = None,
    ):
        """
        Returns Pinecone matches (each has id, score, metadata).
        """
        return self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
            filter=filter or {},
        )

    def delete_by_cv_id(self, cv_id: str, namespace: str = "default") -> None:
        """
        Optional: delete all vectors for a given cv_id by metadata filter.
        """
        self.index.delete(
            delete_all=False,
            filter={"cv_id": {"$eq": cv_id}},
            namespace=namespace,
        )
