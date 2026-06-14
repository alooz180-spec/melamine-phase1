from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole
from app.models.product import FinishType
from app.models.match import FeedbackType


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str  # email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    full_name: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.staff


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Company ──────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    country: Optional[str] = None
    website: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyOut(BaseModel):
    id: int
    name: str
    country: Optional[str]
    website: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Catalog ──────────────────────────────────────────────────────────────────

class CatalogCreate(BaseModel):
    name: str
    year: Optional[int] = None
    description: Optional[str] = None
    company_id: int


class CatalogUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CatalogOut(BaseModel):
    id: int
    name: str
    year: Optional[int]
    description: Optional[str]
    company_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Product ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    code: str
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    catalog_id: int
    color_hex: Optional[str] = None
    color_lab_l: Optional[float] = None
    color_lab_a: Optional[float] = None
    color_lab_b: Optional[float] = None
    color_rgb_r: Optional[int] = None
    color_rgb_g: Optional[int] = None
    color_rgb_b: Optional[int] = None
    finish: Optional[FinishType] = None
    thickness_mm: Optional[float] = None
    width_mm: Optional[float] = None
    length_mm: Optional[float] = None
    tags: Optional[List[str]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    description: Optional[str] = None
    color_hex: Optional[str] = None
    color_lab_l: Optional[float] = None
    color_lab_a: Optional[float] = None
    color_lab_b: Optional[float] = None
    finish: Optional[FinishType] = None
    thickness_mm: Optional[float] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    code: str
    name: str
    name_ar: Optional[str]
    description: Optional[str]
    catalog_id: int
    color_hex: Optional[str]
    color_lab_l: Optional[float]
    color_lab_a: Optional[float]
    color_lab_b: Optional[float]
    color_rgb_r: Optional[int]
    color_rgb_g: Optional[int]
    color_rgb_b: Optional[int]
    finish: Optional[FinishType]
    thickness_mm: Optional[float]
    width_mm: Optional[float]
    length_mm: Optional[float]
    tags: Optional[List[str]]
    qdrant_point_id: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Image Upload ─────────────────────────────────────────────────────────────

class UploadOut(BaseModel):
    id: int
    original_filename: str
    storage_key: str
    file_size_bytes: Optional[int]
    status: str
    width_px: Optional[int]
    height_px: Optional[int]
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Match ────────────────────────────────────────────────────────────────────

class ProductBrief(BaseModel):
    id: int
    code: str
    name: str
    name_ar: Optional[str]
    finish: Optional[str]
    color_hex: Optional[str]
    thickness_mm: Optional[float]
    width_mm: Optional[float]
    length_mm: Optional[float]
    tags: Optional[List[str]]
    reference_image_url: Optional[str]


class MatchOut(BaseModel):
    match_result_id: int
    rank: int
    confidence_score: float
    vector_score: Optional[float]
    color_delta_e: Optional[float]
    score_breakdown: Optional[Dict[str, Any]]
    product: ProductBrief


class MatchResponse(BaseModel):
    upload_id: int
    query_color: Optional[Dict[str, Any]]
    matches: List[MatchOut]


# ─── Feedback ─────────────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    match_result_id: int
    feedback_type: FeedbackType
    correct_product_id: Optional[int] = None
    notes: Optional[str] = None


class FeedbackOut(BaseModel):
    id: int
    match_result_id: int
    user_id: Optional[int]
    product_id: Optional[int]
    feedback_type: FeedbackType
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Admin Stats ──────────────────────────────────────────────────────────────

class SystemStats(BaseModel):
    total_products: int
    total_uploads: int
    total_matches: int
    total_feedbacks: int
    qdrant_vectors: int
    qdrant_status: str
