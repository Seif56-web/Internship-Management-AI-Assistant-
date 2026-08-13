from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./gestion_stagiaires.db"
    DATABASE_URL_SYNC: str = "sqlite:///./gestion_stagiaires.db"
    SECRET_KEY: str = "changer-cette-cle-en-production-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    UPLOAD_DIR: str = "uploads/rapports"
    ATTESTATION_DIR: str = "uploads/attestations"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "stages@hutchinson.tn"

    class Config:
        env_file = ".env"


settings = Settings()
