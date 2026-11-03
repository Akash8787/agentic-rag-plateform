"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Configuration shared by the API and application services."""

    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 5000
    secret_key: Optional[str] = None
    database_url: str = "sqlite:///storage/app.db"
    upload_dir: Path = Path("storage/uploads")
    index_dir: Path = Path("storage/indexes")
    max_upload_size_mb: int = 25
    groq_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    groq_model: str = "openai/gpt-oss-120b"
    embedding_model: str = "all-MiniLM-L12-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables."""
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=False)
        max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
        if max_upload_size_mb <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be greater than zero")

        return cls(
            debug=_as_bool(os.getenv("FLASK_DEBUG", "false")),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "5000")),
            secret_key=os.getenv("SECRET_KEY") or None,
            database_url=os.getenv("DATABASE_URL", "sqlite:///storage/app.db"),
            upload_dir=Path(os.getenv("UPLOAD_DIR", "storage/uploads")),
            index_dir=Path(os.getenv("INDEX_DIR", "storage/indexes")),
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
            groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            embedding_model=os.getenv(
                "EMBEDDING_MODEL", "all-MiniLM-L12-v2"
            ),
            reranker_model=os.getenv(
                "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-12-v2"
            ),
            max_upload_size_mb=max_upload_size_mb,
        )

    def to_flask_config(self) -> dict[str, object]:
        """Convert settings to Flask's configuration mapping."""
        return {
            "DEBUG": self.debug,
            "HOST": self.host,
            "PORT": self.port,
            "SECRET_KEY": self.secret_key,
            "DATABASE_URL": self.database_url,
            "UPLOAD_DIR": self.upload_dir,
            "INDEX_DIR": self.index_dir,
            "MAX_CONTENT_LENGTH": self.max_upload_size_mb * 1024 * 1024,
            "GROQ_API_KEY": self.groq_api_key,
            "TAVILY_API_KEY": self.tavily_api_key,
            "GROQ_MODEL": self.groq_model,
            "EMBEDDING_MODEL": self.embedding_model,
            "RERANKER_MODEL": self.reranker_model,
        }
