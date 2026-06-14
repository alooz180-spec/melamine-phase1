import io
import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

TARGET_SIZE = (224, 224)


def load_image_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def preprocess_for_embedding(data: bytes) -> Tuple[bytes, Dict[str, int]]:
    """
    Resize and normalize the image for embedding.
    Returns (processed_jpeg_bytes, {width, height}).
    """
    img = load_image_from_bytes(data)
    orig_size = {"width": img.width, "height": img.height}

    # Center-crop to square then resize
    img = _center_crop_square(img)
    img = img.resize(TARGET_SIZE, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue(), orig_size


def _center_crop_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    return img.crop((left, top, left + min_dim, top + min_dim))


def extract_dominant_color(data: bytes, n_clusters: int = 3) -> Dict[str, Any]:
    """
    Extract dominant color in RGB and CIE Lab.
    Uses simple average (fast) — for production, swap with K-means.
    """
    img = load_image_from_bytes(data)
    img_resized = img.resize((50, 50))  # fast average
    arr = np.array(img_resized, dtype=np.float32)
    mean_rgb = arr.mean(axis=(0, 1))
    r, g, b = int(mean_rgb[0]), int(mean_rgb[1]), int(mean_rgb[2])
    hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
    lab = _rgb_to_lab(r, g, b)

    return {
        "rgb_r": r,
        "rgb_g": g,
        "rgb_b": b,
        "hex": hex_color,
        "lab_l": lab[0],
        "lab_a": lab[1],
        "lab_b": lab[2],
    }


def _rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """sRGB → CIE Lab (D65 illuminant)."""
    # Linearize
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = linearize(r), linearize(g), linearize(b)

    # sRGB → XYZ (D65)
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041

    # XYZ → Lab
    x, y, z = x / 0.95047, y / 1.00000, z / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)
    return round(L, 2), round(a, 2), round(b_val, 2)


def delta_e_cie76(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """CIE76 Delta-E color difference."""
    return float(np.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2))))


def image_to_tensor(data: bytes) -> np.ndarray:
    """Convert image bytes to normalized numpy array (C, H, W) for embedding model."""
    img = load_image_from_bytes(data)
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    arr = (arr - mean) / std
    return arr.transpose(2, 0, 1)  # H,W,C → C,H,W
