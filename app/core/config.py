from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Melamine Color Deduction System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Neon PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_BTHpr53OLwEa@ep-lingering-glade-ah61vgq6-pooler.c-3.us-east-1.aws.neon.tech/neondb?ssl=require"
    DATABASE_URL_SYNC: str = "postgresql://neondb_owner:npg_BTHpr53OLwEa@ep-lingering-glade-ah61vgq6-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

    # Redis (not needed for MVP)
    REDIS_URL: Optional[str] = None

    # Cloudflare R2 Storage
    USE_LOCAL_STORAGE: bool = False
    LOCAL_STORAGE_PATH: str = "/tmp/melamine_images"
    R2_ACCOUNT_ID: str = "00b34611ec22cab71dcaaa2bedec5d0c"
    R2_ACCESS_KEY_ID: str = "d7647f96dd59a2d83d59cd03d673b84f"
    R2_SECRET_ACCESS_KEY: str = "061bb5de23cda029f30beda918a4252fc8234833f953fe93212c36ddffb46952"
    R2_BUCKET: str = "melamine-images"
    R2_ENDPOINT: str = "https://00b34611ec22cab71dcaaa2bedec5d0c.r2.cloudflarestorage.com"

    # Qdrant Cloud
    QDRANT_HOST: str = "f88fc3d0-2845-4636-91ef-638b66d24911.us-west-1-0.aws.cloud.qdrant.io"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MTk3MTNjZDktYmE1ZS00YWRlLWEwN2ItZmYwZWEzM2Y2Y2VhIn0.4GAfFnxeCcKBdJanCe2YVhWfPmqQFHjABi2jcpBuREc"
    QDRANT_COLLECTION: str = "melamine_colors"
    QDRANT_VECTOR_SIZE: int = 512
    QDRANT_USE_HTTPS: bool = True

    # Auth
    SECRET_KEY: str = "mel4m1ne-pr0d-2024-railway-secret-key-x9z"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # CORS — allow Lovable + all origins for now
    FRONTEND_URL: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
