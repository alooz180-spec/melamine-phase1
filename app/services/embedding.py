"""
Embedding service — Railway free tier version.
Uses color histogram (512-dim) — fast, no GPU, no large model download.
For production upgrade: swap _histogram_fallback with CLIP.
"""
import numpy as np
import logging
from typing import List

logger = logging.getLogger(__name__)

VECTOR_SIZE = 512


def get_image_embedding(image_bytes: bytes) -> List[float]:
    """Generate a 512-dim color histogram embedding."""
    return _histogram_embedding(image_bytes)


def _histogram_embedding(image_bytes: bytes) -> List[float]:
    """
    RGB color histogram: 8 bins × 8 bins × 8 bins = 512 dims.
    L2-normalized so cosine similarity works correctly.
    """
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((64, 64))
    arr = np.array(img)
    hist, _ = np.histogramdd(
        arr.reshape(-1, 3).astype(np.float32),
        bins=[8, 8, 8],
        range=[(0, 256), (0, 256), (0, 256)],
    )
    hist = hist.flatten().astype(np.float32)
    norm = np.linalg.norm(hist)
    if norm > 0:
        hist = hist / norm
    return hist.tolist()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a, b = np.array(v1), np.array(v2)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0
