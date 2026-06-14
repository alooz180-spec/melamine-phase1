import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.core.security import get_current_user, get_current_admin
from app.schemas import ProductCreate, ProductUpdate, ProductOut
from app.services import storage, vector_search, embedding, image_processing

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductOut])
async def list_products(
    catalog_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Product).where(Product.is_active == True)
    if catalog_id:
        q = q.where(Product.catalog_id == catalog_id)
    q = q.offset(skip).limit(limit).order_by(Product.code)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=ProductOut)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    product = Product(**payload.model_dump())
    db.add(product)
    await db.flush()
    return product


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(p, field, val)
    await db.flush()
    return p


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    p.is_active = False
    if p.qdrant_point_id:
        try:
            vector_search.delete_product_vector(p.qdrant_point_id)
        except Exception:
            pass
    await db.flush()
    return {"detail": "Product deactivated"}


@router.post("/{product_id}/upload-reference-image")
async def upload_reference_image(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Upload a reference image for a product, generate its embedding,
    and index it in Qdrant.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    file_bytes = await file.read()

    # Save original to MinIO
    obj_key = f"products/{product_id}/reference_{uuid.uuid4().hex}.jpg"
    storage.upload_file(file_bytes, obj_key, file.content_type or "image/jpeg")
    p.reference_image_key = obj_key

    # Extract color
    color = image_processing.extract_dominant_color(file_bytes)
    p.color_rgb_r = color["rgb_r"]
    p.color_rgb_g = color["rgb_g"]
    p.color_rgb_b = color["rgb_b"]
    p.color_hex = color["hex"]
    p.color_lab_l = color["lab_l"]
    p.color_lab_a = color["lab_a"]
    p.color_lab_b = color["lab_b"]

    # Preprocess + embed
    processed_bytes, _ = image_processing.preprocess_for_embedding(file_bytes)
    vec = embedding.get_image_embedding(processed_bytes)

    # Upsert in Qdrant
    point_id = p.qdrant_point_id or str(uuid.uuid4())
    p.qdrant_point_id = point_id

    vector_search.upsert_product_vector(
        point_id=point_id,
        vector=vec,
        payload={
            "product_id": p.id,
            "product_code": p.code,
            "product_name": p.name,
            "catalog_id": p.catalog_id,
            "color_hex": p.color_hex,
            "finish": p.finish.value if p.finish else None,
        },
    )

    await db.flush()
    return {
        "detail": "Reference image uploaded and indexed",
        "product_id": p.id,
        "qdrant_point_id": point_id,
        "color": color,
    }
