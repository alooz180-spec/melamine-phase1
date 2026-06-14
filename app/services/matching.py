"""
Core matching pipeline:
1. Upload image to MinIO
2. Preprocess image
3. Extract dominant color
4. Generate embedding
5. Search Qdrant
6. Fetch matching products from DB
7. Rank by combined score (vector similarity + color ΔE)
8. Persist match results
9. Return ranked matches with confidence
"""
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import asyncio

from app.services import storage, image_processing, embedding, vector_search
from app.models.match import ImageUpload, MatchResult, UploadStatus
from app.models.product import Product

logger = logging.getLogger(__name__)

TOP_K = 10
MIN_CONFIDENCE = 0.0


async def run_matching_pipeline(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    user_id: Optional[int],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Full end-to-end matching pipeline.
    Returns dict with upload_id and list of match dicts.
    """

    # 1. Save original to MinIO
    object_key = f"uploads/{uuid.uuid4().hex}/{filename}"
    storage.upload_file(file_bytes, object_key, mime_type)

    # 2. Create upload record
    upload = ImageUpload(
        original_filename=filename,
        storage_key=object_key,
        file_size_bytes=len(file_bytes),
        mime_type=mime_type,
        status=UploadStatus.processing,
        uploaded_by=user_id,
    )
    db.add(upload)
    await db.flush()

    try:
        # 3. Preprocess
        processed_bytes, orig_size = image_processing.preprocess_for_embedding(file_bytes)
        upload.width_px = orig_size["width"]
        upload.height_px = orig_size["height"]

        processed_key = f"processed/{uuid.uuid4().hex}.jpg"
        storage.upload_file(processed_bytes, processed_key, "image/jpeg")
        upload.processed_key = processed_key

        # 4. Extract dominant color
        color_info = image_processing.extract_dominant_color(file_bytes)

        # 5. Generate embedding (runs in thread to not block event loop)
        loop = asyncio.get_event_loop()
        query_vector = await loop.run_in_executor(
            None, embedding.get_image_embedding, processed_bytes
        )

        # 6. Search Qdrant
        hits = vector_search.search_similar(query_vector, top_k=TOP_K)

        if not hits:
            upload.status = UploadStatus.completed
            upload.processed_at = datetime.utcnow()
            await db.flush()
            return {"upload_id": upload.id, "matches": [], "color": color_info}

        # 7. Fetch products from DB using qdrant_point_ids
        point_ids = [str(h.id) for h in hits]
        score_map = {str(h.id): h.score for h in hits}

        result = await db.execute(
            select(Product).where(
                and_(Product.qdrant_point_id.in_(point_ids), Product.is_active == True)
            )
        )
        products = result.scalars().all()
        product_by_pid = {p.qdrant_point_id: p for p in products}

        # 8. Rank with combined score
        ranked = _rank_results(hits, product_by_pid, color_info)

        # 9. Persist match results
        match_records = []
        for rank_idx, m in enumerate(ranked, start=1):
            mr = MatchResult(
                upload_id=upload.id,
                product_id=m["product"].id,
                rank=rank_idx,
                confidence_score=m["confidence"],
                vector_distance=m["vector_score"],
                color_delta_e=m.get("delta_e"),
                score_breakdown=m["breakdown"],
            )
            db.add(mr)
            match_records.append((mr, m["product"]))

        upload.status = UploadStatus.completed
        upload.processed_at = datetime.utcnow()
        await db.flush()

        # Build response
        matches_out = []
        for mr, prod in match_records:
            try:
                image_url = storage.get_presigned_url(prod.reference_image_key) if prod.reference_image_key else None
            except Exception:
                image_url = None

            matches_out.append({
                "match_result_id": mr.id,
                "rank": mr.rank,
                "confidence_score": mr.confidence_score,
                "vector_score": mr.vector_distance,
                "color_delta_e": mr.color_delta_e,
                "score_breakdown": mr.score_breakdown,
                "product": _serialize_product(prod, image_url),
            })

        return {
            "upload_id": upload.id,
            "query_color": color_info,
            "matches": matches_out,
        }

    except Exception as e:
        logger.exception(f"Matching pipeline failed: {e}")
        upload.status = UploadStatus.failed
        upload.error_message = str(e)
        await db.flush()
        raise


def _rank_results(hits, product_by_pid, color_info) -> List[Dict]:
    """Combine vector score and color ΔE into a single confidence score."""
    ranked = []
    for hit in hits:
        pid = str(hit.id)
        product = product_by_pid.get(pid)
        if product is None:
            continue

        vec_score = hit.score  # 0..1 cosine similarity

        # Color Delta-E score
        delta_e = None
        color_score = vec_score  # fallback
        if (
            product.color_lab_l is not None
            and color_info.get("lab_l") is not None
        ):
            delta_e = image_processing.delta_e_cie76(
                (color_info["lab_l"], color_info["lab_a"], color_info["lab_b"]),
                (product.color_lab_l, product.color_lab_a, product.color_lab_b),
            )
            # Map ΔE 0..100 → score 1..0 (lower ΔE = better match)
            color_score = max(0.0, 1.0 - delta_e / 100.0)

        # Combined 70% vector + 30% color
        confidence = round(0.7 * vec_score + 0.3 * color_score, 4)

        ranked.append({
            "product": product,
            "confidence": confidence,
            "vector_score": round(vec_score, 4),
            "delta_e": round(delta_e, 2) if delta_e is not None else None,
            "breakdown": {
                "vector_similarity": round(vec_score, 4),
                "color_score": round(color_score, 4),
                "color_delta_e": round(delta_e, 2) if delta_e is not None else None,
            },
        })

    ranked.sort(key=lambda x: x["confidence"], reverse=True)
    return ranked


def _serialize_product(p: Product, image_url: Optional[str]) -> Dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "name_ar": p.name_ar,
        "finish": p.finish.value if p.finish else None,
        "color_hex": p.color_hex,
        "thickness_mm": p.thickness_mm,
        "width_mm": p.width_mm,
        "length_mm": p.length_mm,
        "tags": p.tags or [],
        "reference_image_url": image_url,
    }
