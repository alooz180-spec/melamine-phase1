from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.user import User
from app.models.product import Product
from app.models.match import ImageUpload, MatchResult, Feedback
from app.core.security import get_current_admin
from app.schemas import SystemStats
from app.services import vector_search

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=SystemStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """System-wide statistics for admin dashboard."""
    total_products = (await db.execute(select(func.count(Product.id)).where(Product.is_active == True))).scalar()
    total_uploads = (await db.execute(select(func.count(ImageUpload.id)))).scalar()
    total_matches = (await db.execute(select(func.count(MatchResult.id)))).scalar()
    total_feedbacks = (await db.execute(select(func.count(Feedback.id)))).scalar()

    qdrant_stats = vector_search.get_collection_stats()

    return SystemStats(
        total_products=total_products or 0,
        total_uploads=total_uploads or 0,
        total_matches=total_matches or 0,
        total_feedbacks=total_feedbacks or 0,
        qdrant_vectors=qdrant_stats.get("vectors_count") or 0,
        qdrant_status=qdrant_stats.get("status", "unknown"),
    )
