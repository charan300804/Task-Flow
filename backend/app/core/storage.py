import io
import json
import logging
import os
from typing import Optional, Union, Dict, Any

logger = logging.getLogger(__name__)

try:
    from minio import Minio
    from minio.error import S3Error
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False
    Minio = None
    logger.warning("minio package not installed locally. Using local filesystem storage fallback for artifacts.")

from app.core.config import settings

class StorageClient:
    def __init__(self):
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.use_minio = HAS_MINIO
        if self.use_minio:
            try:
                self.client = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                )
            except Exception as e:
                logger.warning(f"Could not connect to MinIO endpoint: {e}")
                self.use_minio = False
        self.fallback_dir = os.path.join(os.getcwd(), "artifact_storage")
        os.makedirs(self.fallback_dir, exist_ok=True)

    def ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        if not self.use_minio:
            return
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"MinIO bucket '{self.bucket_name}' created successfully.")
        except Exception as e:
            logger.warning(f"MinIO bucket connection warning: {e}")
            self.use_minio = False

    def upload_json(self, object_name: str, data: Dict[str, Any]) -> str:
        """Upload a dictionary/JSON payload to object storage."""
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return self.upload_bytes(object_name, json_bytes, content_type="application/json")

    def upload_bytes(self, object_name: str, data_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes to object storage."""
        if self.use_minio:
            try:
                self.ensure_bucket_exists()
                data_stream = io.BytesIO(data_bytes)
                self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    data=data_stream,
                    length=len(data_bytes),
                    content_type=content_type,
                )
                return f"s3://{self.bucket_name}/{object_name}"
            except Exception as e:
                logger.warning(f"MinIO upload failed, falling back to local file storage: {e}")

        # Fallback local file storage
        local_path = os.path.join(self.fallback_dir, object_name.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(data_bytes)
        return f"s3://{self.bucket_name}/{object_name}"

    def get_object_content(self, object_name: str) -> Optional[bytes]:
        """Download object content as bytes."""
        if self.use_minio:
            try:
                response = self.client.get_object(self.bucket_name, object_name)
                data = response.read()
                response.close()
                response.release_conn()
                return data
            except Exception as e:
                logger.warning(f"Failed to fetch object {object_name} from MinIO: {e}")

        # Fallback local file storage
        local_path = os.path.join(self.fallback_dir, object_name.replace("/", "_"))
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()
        return None

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Generate a presigned GET URL for an artifact."""
        if self.use_minio:
            try:
                return self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    expires=expires_seconds,
                )
            except Exception as e:
                logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
        return f"/api/jobs/artifacts/{object_name}"

storage_client = StorageClient()
