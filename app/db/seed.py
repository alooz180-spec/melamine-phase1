"""
Seed the database with:
- 2 users: admin + staff
- 3 companies
- 3 catalogs
- 30 demo melamine products with color data + Qdrant indexing
"""
import asyncio
import uuid
import sys
import os
import logging

# Ensure PYTHONPATH
sys.path.insert(0, "/app")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.product import Company, Catalog, Product, FinishType
from app.services import vector_search, embedding
from app.db.session import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ─── Demo data ────────────────────────────────────────────────────────────────

USERS = [
    {"email": "admin@melamine.com", "full_name": "System Admin", "password": "admin1234", "role": UserRole.admin},
    {"email": "staff@melamine.com", "full_name": "Sales Staff", "password": "staff1234", "role": UserRole.staff},
]

COMPANIES = [
    {"name": "Egger", "country": "Austria", "website": "https://www.egger.com"},
    {"name": "Pfleiderer", "country": "Germany", "website": "https://www.pfleiderer.com"},
    {"name": "Kronospan", "country": "Austria", "website": "https://www.kronospan.com"},
]

CATALOGS = [
    {"name": "Egger Melamine 2024", "year": 2024, "description": "Full range melamine boards", "company_idx": 0},
    {"name": "Pfleiderer DecoBoard 2024", "year": 2024, "description": "Premium decor boards", "company_idx": 1},
    {"name": "Kronospan Colours 2024", "year": 2024, "description": "Standard colour collection", "company_idx": 2},
]

# (code, name, name_ar, hex, r, g, b, finish, thickness, tags)
PRODUCTS = [
    # Whites & Creams
    ("W980", "Alpine White", "أبيض جبلي", "#F5F5F0", 245, 245, 240, FinishType.matte, 18.0, ["white", "neutral"]),
    ("W1000", "Pure White", "أبيض نقي", "#FFFFFF", 255, 255, 255, FinishType.gloss, 18.0, ["white", "gloss"]),
    ("W928", "Cream White", "كريم أبيض", "#FFF8DC", 255, 248, 220, FinishType.satin, 18.0, ["cream", "warm"]),
    ("U702", "Soft Beige", "بيج ناعم", "#F5DEB3", 245, 222, 179, FinishType.matte, 18.0, ["beige", "warm"]),

    # Greys
    ("U763", "Light Grey", "رمادي فاتح", "#D3D3D3", 211, 211, 211, FinishType.matte, 18.0, ["grey", "neutral"]),
    ("U732", "Pebble Grey", "رمادي حصى", "#C0C0C0", 192, 192, 192, FinishType.satin, 18.0, ["grey"]),
    ("U741", "Stone Grey", "رمادي حجري", "#808080", 128, 128, 128, FinishType.matte, 18.0, ["grey", "stone"]),
    ("U960", "Anthracite", "أنثراسايت", "#36454F", 54, 69, 79, FinishType.matte, 18.0, ["dark", "grey"]),
    ("U899", "Graphite", "غرافيت", "#474747", 71, 71, 71, FinishType.gloss, 18.0, ["dark", "modern"]),

    # Browns & Woodgrains
    ("H1145", "Light Elm", "دردار فاتح", "#C4A882", 196, 168, 130, FinishType.woodgrain, 18.0, ["wood", "elm", "warm"]),
    ("H3408", "Gladstone Oak", "بلوط غلادستون", "#8B7355", 139, 115, 85, FinishType.woodgrain, 18.0, ["wood", "oak"]),
    ("H1334", "Davos Oak Beige", "بلوط ديفوس بيج", "#A0896A", 160, 137, 106, FinishType.woodgrain, 18.0, ["wood", "oak"]),
    ("H3152", "Brandy Oak", "بلوط براندي", "#7B5B3A", 123, 91, 58, FinishType.woodgrain, 18.0, ["wood", "dark"]),
    ("H3700", "Wenge", "وينجي", "#3D2B1F", 61, 43, 31, FinishType.woodgrain, 18.0, ["wood", "dark", "exotic"]),

    # Blues
    ("U504", "Ocean Blue", "أزرق المحيط", "#1E90FF", 30, 144, 255, FinishType.matte, 18.0, ["blue", "bold"]),
    ("U522", "Steel Blue", "أزرق فولاذي", "#4682B4", 70, 130, 180, FinishType.satin, 18.0, ["blue", "neutral"]),
    ("U560", "Navy Blue", "أزرق كحلي", "#000080", 0, 0, 128, FinishType.matte, 18.0, ["blue", "dark"]),

    # Greens
    ("U630", "Sage Green", "أخضر حكيم", "#BCB88A", 188, 184, 138, FinishType.matte, 18.0, ["green", "soft"]),
    ("U656", "Forest Green", "أخضر الغابة", "#228B22", 34, 139, 34, FinishType.matte, 18.0, ["green", "dark"]),
    ("U726", "Mint", "نعناع", "#98FF98", 152, 255, 152, FinishType.gloss, 18.0, ["green", "fresh"]),

    # Reds & Pinks
    ("U311", "Tomato Red", "أحمر طماطم", "#FF6347", 255, 99, 71, FinishType.gloss, 18.0, ["red", "bold"]),
    ("U363", "Burgundy", "خمري", "#800020", 128, 0, 32, FinishType.matte, 18.0, ["red", "dark"]),
    ("U363S", "Dusty Rose", "وردي غبار", "#DCAE96", 220, 174, 150, FinishType.satin, 18.0, ["pink", "soft"]),

    # Yellows & Oranges
    ("U108", "Sunflower Yellow", "أصفر عباد الشمس", "#FFD700", 255, 215, 0, FinishType.gloss, 18.0, ["yellow", "bright"]),
    ("U330", "Terracotta", "تراكوتا", "#E2725B", 226, 114, 91, FinishType.matte, 18.0, ["orange", "earthy"]),

    # Blacks
    ("U999", "Jet Black", "أسود غامق", "#0A0A0A", 10, 10, 10, FinishType.gloss, 18.0, ["black", "gloss"]),
    ("U900", "Matt Black", "أسود مات", "#1C1C1C", 28, 28, 28, FinishType.matte, 18.0, ["black", "matte"]),

    # Special / Metallic
    ("U110", "Silver Metallic", "فضي معدني", "#C0C0C0", 192, 192, 192, FinishType.metallic, 18.0, ["metallic", "silver"]),
    ("U960G", "Gold Metallic", "ذهبي معدني", "#FFD700", 255, 215, 0, FinishType.metallic, 18.0, ["metallic", "gold"]),
    ("U990T", "Concrete Look", "مظهر خرساني", "#A9A9A9", 169, 169, 169, FinishType.textured, 18.0, ["textured", "concrete"]),
]


def _rgb_to_lab(r, g, b):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    rl, gl, bl = lin(r), lin(g), lin(b)
    x = rl*0.4124564 + gl*0.3575761 + bl*0.1804375
    y = rl*0.2126729 + gl*0.7151522 + bl*0.0721750
    z = rl*0.0193339 + gl*0.1191920 + bl*0.9503041
    x, y, z = x/0.95047, y/1.0, z/1.08883
    def f(t): return t**(1/3) if t > 0.008856 else 7.787*t + 16/116
    L = 116*f(y) - 16
    a = 500*(f(x) - f(y))
    b_val = 200*(f(y) - f(z))
    return round(L, 2), round(a, 2), round(b_val, 2)


async def seed():
    async with SessionLocal() as db:
        # ── Users ─────────────────────────────────────────────────────────────
        logger.info("Seeding users...")
        for u in USERS:
            existing = await db.execute(select(User).where(User.email == u["email"]))
            if existing.scalar_one_or_none():
                logger.info(f"  User {u['email']} already exists, skipping")
                continue
            db.add(User(
                email=u["email"],
                full_name=u["full_name"],
                hashed_password=get_password_hash(u["password"][:72]),
                role=u["role"],
            ))
        await db.commit()

        # ── Companies ─────────────────────────────────────────────────────────
        logger.info("Seeding companies...")
        company_ids = []
        for c in COMPANIES:
            existing = await db.execute(select(Company).where(Company.name == c["name"]))
            obj = existing.scalar_one_or_none()
            if not obj:
                obj = Company(**c)
                db.add(obj)
                await db.flush()
            company_ids.append(obj.id)
        await db.commit()

        # ── Catalogs ──────────────────────────────────────────────────────────
        logger.info("Seeding catalogs...")
        catalog_ids = []
        for i, c in enumerate(CATALOGS):
            existing = await db.execute(select(Catalog).where(Catalog.name == c["name"]))
            obj = existing.scalar_one_or_none()
            if not obj:
                obj = Catalog(
                    name=c["name"],
                    year=c["year"],
                    description=c["description"],
                    company_id=company_ids[c["company_idx"]],
                )
                db.add(obj)
                await db.flush()
            catalog_ids.append(obj.id)
        await db.commit()

        # ── Ensure Qdrant collection exists ───────────────────────────────────
        try:
            vector_search.ensure_collection_exists()
            logger.info("Qdrant collection ready")
        except Exception as e:
            logger.warning(f"Qdrant not available yet: {e}")

        # ── Products ──────────────────────────────────────────────────────────
        logger.info("Seeding products...")
        for idx, (code, name, name_ar, hex_color, r, g, b, finish, thickness, tags) in enumerate(PRODUCTS):
            existing = await db.execute(select(Product).where(Product.code == code))
            p = existing.scalar_one_or_none()
            lab_l, lab_a, lab_b = _rgb_to_lab(r, g, b)

            if not p:
                catalog_id = catalog_ids[idx % len(catalog_ids)]
                p = Product(
                    code=code,
                    name=name,
                    name_ar=name_ar,
                    catalog_id=catalog_id,
                    color_hex=hex_color,
                    color_rgb_r=r,
                    color_rgb_g=g,
                    color_rgb_b=b,
                    color_lab_l=lab_l,
                    color_lab_a=lab_a,
                    color_lab_b=lab_b,
                    finish=finish,
                    thickness_mm=thickness,
                    width_mm=2800.0,
                    length_mm=2070.0,
                    tags=tags,
                )
                db.add(p)
                await db.flush()

            # Generate synthetic embedding from color (histogram of solid color)
            if not p.qdrant_point_id:
                import numpy as np
                from PIL import Image
                import io

                # Create a solid-color swatch to embed
                swatch = Image.new("RGB", (224, 224), (r, g, b))
                buf = io.BytesIO()
                swatch.save(buf, format="JPEG")
                swatch_bytes = buf.getvalue()

                try:
                    vec = embedding.get_image_embedding(swatch_bytes)
                    point_id = str(uuid.uuid4())
                    p.qdrant_point_id = point_id
                    vector_search.upsert_product_vector(
                        point_id=point_id,
                        vector=vec,
                        payload={
                            "product_id": p.id,
                            "product_code": p.code,
                            "product_name": p.name,
                            "color_hex": p.color_hex,
                            "catalog_id": p.catalog_id,
                        },
                    )
                    logger.info(f"  Indexed product {p.code} → {point_id}")
                except Exception as e:
                    logger.warning(f"  Could not index {p.code} in Qdrant: {e}")

        await db.commit()
        logger.info("✅ Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
