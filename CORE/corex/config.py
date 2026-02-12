import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    CORE_X_AGENT Configuration (LDP v2.0)
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # API Info
    PROJECT_NAME: str = "LUMEN CORE-X (LDP ENABLED)"
    API_V1_STR: str = "/api/v1"

    # --- DEV MODE & LDP ---
    DEV_MODE: bool = False
    LOG_LEVEL: str = "INFO"
    STRICT_VALIDATION: bool = False
    FEATURE_FLAGS: str = "default"  # 'all' or comma-separated list

    # Security - Must be set via environment variable
    SECRET_KEY: str = ""  # Will raise error if not set in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///E:/SHAD/GROTA_LUMENA/DATABASE/lumen_core.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @property
    def is_feature_enabled(self, feature: str) -> bool:
        if self.FEATURE_FLAGS == "all":
            return True
        return feature in self.FEATURE_FLAGS.split(",")


settings = Settings()
