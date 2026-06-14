from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, ScoredPoint,
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY,
        https=settings.QDRANT_USE_HTTPS,
    )


def ensure_collection_exists(client: Optional[QdrantClient] = None) -> None:
    client = client or get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION}")


def upsert_product_vector(
    point_id: str,
    vector: List[float],
    payload: Dict[str, Any],
    client: Optional[QdrantClient] = None,
) -> None:
    client = client or get_qdrant_client()
    ensure_collection_exists(client)
    client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
    )


def search_similar(
    query_vector: List[float],
    top_k: int = 10,
    score_threshold: float = 0.0,
    filters: Optional[Dict] = None,
    client: Optional[QdrantClient] = None,
) -> List[ScoredPoint]:
    client = client or get_qdrant_client()
    ensure_collection_exists(client)

    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    return client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=qdrant_filter,
        with_payload=True,
    )


def delete_product_vector(point_id: str, client: Optional[QdrantClient] = None) -> None:
    client = client or get_qdrant_client()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=[point_id],
    )


def get_collection_stats(client: Optional[QdrantClient] = None) -> Dict[str, Any]:
    client = client or get_qdrant_client()
    try:
        info = client.get_collection(settings.QDRANT_COLLECTION)
        return {
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
    except Exception as e:
        return {"error": str(e), "status": "unavailable"}
