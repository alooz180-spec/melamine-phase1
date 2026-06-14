from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db.session import get_db
from app.models.match import ImageUpload, MatchResult
from app.models.user import User
from app.core.security import get_current_user
from app.schemas import MatchResponse, UploadOut
from app.services.matching import run_matching_pipeline

router = APIRouter(prefix="/match", tags=["matching"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
MAX_SIZE_MB = 20


@router.post("/", response_model=MatchResponse)
async def match_image(
    file: UploadFile = File(..., description="Melamine board image to match"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image and receive ranked product matches.
    """
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {ALLOWED_MIME}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_SIZE_MB}MB)")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = await run_matching_pipeline(
            file_bytes=file_bytes,
            filename=file.filename or "upload.jpg",
            mime_type=file.content_type,
            user_id=current_user.id,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching pipeline error: {str(e)}")

    return MatchResponse(**result)


@router.get("/history", response_model=List[UploadOut])
async def match_history(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List past uploads for the current user."""
    q = (
        select(ImageUpload)
        .where(ImageUpload.uploaded_by == current_user.id)
        .order_by(ImageUpload.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{upload_id}/results")
async def get_upload_results(
    upload_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get match results for a specific upload."""
    upload_result = await db.execute(
        select(ImageUpload).where(ImageUpload.id == upload_id)
    )
    upload = upload_result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.uploaded_by != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    matches_result = await db.execute(
        select(MatchResult)
        .where(MatchResult.upload_id == upload_id)
        .order_by(MatchResult.rank)
    )
    matches = matches_result.scalars().all()
    return {
        "upload_id": upload_id,
        "status": upload.status.value,
        "matches": [
            {
                "match_result_id": m.id,
                "rank": m.rank,
                "product_id": m.product_id,
                "confidence_score": m.confidence_score,
                "vector_distance": m.vector_distance,
                "color_delta_e": m.color_delta_e,
                "score_breakdown": m.score_breakdown,
            }
            for m in matches
        ],
    }
