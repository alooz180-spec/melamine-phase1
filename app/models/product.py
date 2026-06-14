import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class FinishType(str, enum.Enum):
    matte = "matte"
    gloss = "gloss"
    satin = "satin"
    textured = "textured"
    woodgrain = "woodgrain"
    metallic = "metallic"
    other = "other"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    country = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    catalogs = relationship("Catalog", back_populates="company", lazy="select")


class Catalog(Base):
    __tablename__ = "catalogs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="catalogs")
    products = relationship("Product", back_populates="catalog", lazy="select")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    catalog_id = Column(Integer, ForeignKey("catalogs.id"), nullable=False)

    # Color properties
    color_hex = Column(String(7), nullable=True)   # e.g. #A3B4C5
    color_lab_l = Column(Float, nullable=True)     # CIE Lab L*
    color_lab_a = Column(Float, nullable=True)     # CIE Lab a*
    color_lab_b = Column(Float, nullable=True)     # CIE Lab b*
    color_rgb_r = Column(Integer, nullable=True)
    color_rgb_g = Column(Integer, nullable=True)
    color_rgb_b = Column(Integer, nullable=True)

    # Physical
    finish = Column(SAEnum(FinishType, name="finishtype", create_type=True), nullable=True)
    thickness_mm = Column(Float, nullable=True)
    width_mm = Column(Float, nullable=True)
    length_mm = Column(Float, nullable=True)

    # Reference image stored in MinIO
    reference_image_key = Column(String(500), nullable=True)

    # Embedding vector stored in Qdrant (we store the point id here)
    qdrant_point_id = Column(String(100), nullable=True, index=True)

    # Extra metadata
    tags = Column(JSON, nullable=True, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    catalog = relationship("Catalog", back_populates="products")
    match_results = relationship("MatchResult", back_populates="product", lazy="select")
    feedbacks = relationship("Feedback", back_populates="product", lazy="select")
