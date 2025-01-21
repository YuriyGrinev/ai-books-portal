from typing import List

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Application
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    ENVIRONMENT: str

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """Get database URL"""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # MinIO
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_HOST: str
    MINIO_PORT: int
    MINIO_SECURE: bool
    MINIO_BUCKET_NAME: str

    @property
    def MINIO_URL(self) -> HttpUrl:
        """Get MinIO URL"""
        scheme = "https" if self.MINIO_SECURE else "http"
        return HttpUrl(f"{scheme}://{self.MINIO_HOST}:{self.MINIO_PORT}")

    # API
    API_V1_PREFIX: str
    PROJECT_NAME: str
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


settings = Settings() 