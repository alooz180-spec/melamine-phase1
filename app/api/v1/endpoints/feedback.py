from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.match import Feedback, MatchResult
from app.models.user import User
from app.core.security import get_current_user, get_current_admin
from app.schemas import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackOut)
async def submit_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit feedback on a match result."""
    mr_result = await db.execute(
        select(MatchResult).where(MatchResult.id == payload.match_result_id)
    )
    mr = mr_result.scalar_one_or_none()
    if not mr:
        raise HTTPException(status_code=404, detail="Match result not found")

    feedback = Feedback(
        match_result_id=payload.match_result_id,
        user_id=current_user.id,
        product_id=payload.correct_product_id,
        feedback_type=payload.feedback_type,
        notes=payload.notes,
    )
    db.add(feedback)
    await db.flush()
    return feedback


@router.get("/", response_model=List[FeedbackOut])
async def list_feedbacks(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all feedback (admin only)."""
    result = await db.execute(
        select(Feedback).order_by(Feedback.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()
