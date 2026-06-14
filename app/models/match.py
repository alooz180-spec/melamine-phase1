import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class UploadStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class FeedbackType(str, enum.Enum):
    confirmed = "confirmed"
    rejected = "rejected"
    corrected = "corrected"


class ImageUpload(Base):
    __tablename__ = "image_uploads"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(500), nullable=False)
    storage_key = Column(String(500), nullable=False)           # MinIO object key
    processed_key = Column(String(500), nullable=True)          # preprocessed version
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    width_px = Column(Integer, nullable=True)
    height_px = Column(Integer, nullable=True)
    status = Column(
        SAEnum(UploadStatus, name="uploadstatus", create_type=True),
        nullable=False, default=UploadStatus.pending
    )
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    uploaded_by_user = relationship("User", back_populates="uploads")
    match_results = relationship("MatchResult", back_populates="upload", lazy="select")


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("image_uploads.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    rank = Column(Integer, nullable=False)                      # 1 = best match
    confidence_score = Column(Float, nullable=False)            # 0.0 - 1.0
    vector_distance = Column(Float, nullable=True)              # raw Qdrant score
    color_delta_e = Column(Float, nullable=True)                # CIE Delta-E color diff
    score_breakdown = Column(JSON, nullable=True)               # {"color": 0.8, "texture": 0.7}

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    upload = relationship("ImageUpload", back_populates="match_results")
    product = relationship("Product", back_populates="match_results")
    feedbacks = relationship("Feedback", back_populates="match_result", lazy="select")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    match_result_id = Column(Integer, ForeignKey("match_results.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)    # correct product if corrected
    feedback_type = Column(
        SAEnum(FeedbackType, name="feedbacktype", create_type=True),
        nullable=False
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    match_result = relationship("MatchResult", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
    product = relationship("Product", back_populates="feedbacks")
