from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.product import Catalog
from app.models.user import User
from app.core.security import get_current_user, get_current_admin
from app.schemas import CatalogCreate, CatalogUpdate, CatalogOut

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.get("/", response_model=List[CatalogOut])
async def list_catalogs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Catalog).order_by(Catalog.id))
    return result.scalars().all()


@router.post("/", response_model=CatalogOut)
async def create_catalog(
    payload: CatalogCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    catalog = Catalog(**payload.model_dump())
    db.add(catalog)
    await db.flush()
    return catalog


@router.get("/{catalog_id}", response_model=CatalogOut)
async def get_catalog(
    catalog_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Catalog).where(Catalog.id == catalog_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return c


@router.patch("/{catalog_id}", response_model=CatalogOut)
async def update_catalog(
    catalog_id: int,
    payload: CatalogUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Catalog).where(Catalog.id == catalog_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Catalog not found")
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(c, field, val)
    await db.flush()
    return c
