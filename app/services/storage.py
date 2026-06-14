"""
Storage: Cloudflare R2 (S3-compatible) with local disk fallback.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _client():
    import boto3
    from app.core.config import settings
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _use_r2() -> bool:
    from app.core.config import settings
    return not settings.USE_LOCAL_STORAGE and bool(settings.R2_ACCESS_KEY_ID)


def _local_path(object_name: str) -> str:
    from app.core.config import settings
    safe = object_name.replace("/", "_")
    os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
    return os.path.join(settings.LOCAL_STORAGE_PATH, safe)


def upload_file(data: bytes, object_name: str,
                content_type: str = "application/octet-stream",
                bucket: Optional[str] = None) -> str:
    from app.core.config import settings
    if _use_r2():
        _client().put_object(
            Bucket=bucket or settings.R2_BUCKET,
            Key=object_name,
            Body=data,
            ContentType=content_type,
        )
        logger.info(f"R2 upload OK: {object_name}")
    else:
        with open(_local_path(object_name), "wb") as f:
            f.write(data)
        logger.info(f"Local upload OK: {object_name}")
    return object_name


def download_file(object_name: str, bucket: Optional[str] = None) -> bytes:
    from app.core.config import settings
    if _use_r2():
        resp = _client().get_object(Bucket=bucket or settings.R2_BUCKET, Key=object_name)
        return resp["Body"].read()
    with open(_local_path(object_name), "rb") as f:
        return f.read()


def get_presigned_url(object_name: str, bucket: Optional[str] = None,
                      expires_hours: int = 1) -> Optional[str]:
    from app.core.config import settings
    if _use_r2():
        try:
            return _client().generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket or settings.R2_BUCKET, "Key": object_name},
                ExpiresIn=expires_hours * 3600,
            )
        except Exception as e:
            logger.warning(f"Presign failed: {e}")
            return None
    return None


def delete_file(object_name: str, bucket: Optional[str] = None) -> None:
    from app.core.config import settings
    if _use_r2():
        _client().delete_object(Bucket=bucket or settings.R2_BUCKET, Key=object_name)
    else:
        path = _local_path(object_name)
        if os.path.exists(path):
            os.remove(path)
