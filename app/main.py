from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.api.v1 import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize local storage dir
    os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)

    # Initialize Qdrant collection
    try:
        from app.services.vector_search import ensure_collection_exists
        ensure_collection_exists()
        logger.info(f"Qdrant collection '{settings.QDRANT_COLLECTION}' ready")
    except Exception as e:
        logger.warning(f"Qdrant init warning: {e}")

    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Melamine Color Deduction System

Upload a melamine board photo → get ranked color matches from the catalog.

### Quick Start
1. **Login** → `POST /api/v1/auth/login`
2. **Match image** → `POST /api/v1/match/` with Bearer token
3. **Feedback** → `POST /api/v1/feedback/`
""",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# CORS — allow Lovable + any frontend
allowed_origins = [
    settings.FRONTEND_URL,
    "https://*.lovable.app",
    "https://*.lovableproject.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten after Lovable URL is known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "env": settings.ENVIRONMENT}


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/health",
    })
