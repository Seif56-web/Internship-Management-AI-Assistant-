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

    # LLM (assistant conversationnel) - OpenAI-compatible API
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_TOKENS: int = 700
    LLM_TEMPERATURE: float = 0.3

    # Rate limiting du chat
    CHAT_RATE_LIMIT_MAX: int = 20
    CHAT_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # RAG (Retrieval-Augmented Generation)
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.3
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 150
    RAG_VECTOR_DB_PATH: str = "./backend/rag_chroma_db"
    RAG_EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    RAG_DOCUMENT_PATHS: str = (
        "./backend/uploads/rapports,"
        "./backend/uploads/attestations,"
        "./backend/uploads/feuilles_validation,"
        "./Proposition_Assistant_Conversationnel_Gestion_Stagiaires.pdf,"
        "./Attestation de Stage Haider BOUZAIDA PFE (1).pdf"
    )

    class Config:
        env_file = ".env"


settings = Settings()
