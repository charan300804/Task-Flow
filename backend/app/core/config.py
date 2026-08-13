import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TaskFlow"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-taskflow-jwt-key-change-in-production-32bytes")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database (PostgreSQL)
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "taskflow")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "taskflow_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "taskflow_db")

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # MinIO / Object Storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() in ("true", "1", "t")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "taskflow-artifacts")

    # Worker Settings
    WORKER_HEARTBEAT_INTERVAL_SECONDS: int = 5
    WORKER_UNHEALTHY_THRESHOLD_SECONDS: int = 15
    DEFAULT_JOB_TIMEOUT_SECONDS: int = 300
    DEFAULT_MAX_RETRIES: int = 3
    RETRY_BASE_DELAY_SECONDS: int = 2

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "*"]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
