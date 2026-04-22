"""Application settings and constants for Deal Intelligence Agent."""

from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database Configuration
    database_url: str | None = None

    # Databricks Configuration
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_sql_warehouse_id: str = ""
    databricks_catalog: str = ""
    databricks_schema: str = ""

    # Vector Search Configuration
    vector_search_endpoint: str
    vector_search_index: str

    # LLM Endpoints
    llm_endpoint_sonnet: str
    llm_endpoint_haiku: str
    embedding_endpoint: str

    # Application Configuration
    presigned_url_expiry_seconds: int = 3600
    log_level: str = "INFO"
    app_name: str = "deal-intelligence-agent"
    app_version: str = "1.0.0"

    APP_NAME: str = "Deal Intelligence Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: str = "*"

    # Databricks Model Serving
    DATABRICKS_HOST: str = ""
    DATABRICKS_TOKEN: str = ""
    DATABRICKS_SERVING_ENDPOINT: str = "unified-intelligence-agent"
    DATABRICKS_SQL_HTTP_PATH: str = ""
    DATABRICKS_CATALOG: str = "main"
    DATABRICKS_SCHEMA: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Delta Table Names
CHATS_TABLE = "deal_chats"
DOCUMENTS_TABLE = "deal_documents"
DOCUMENT_CHUNKS_TABLE = "deal_document_chunks"
SESSIONS_TABLE = "deal_sessions"
SESSION_MESSAGES_TABLE = "deal_session_messages"
CITATIONS_TABLE = "deal_citations"
CONVERSATIONS_TABLE = "conversations"

# Processing Constants
MAX_CHUNK_TOKENS = 1024
CHUNK_OVERLAP_TOKENS = 100
EMBEDDING_DIMENSIONS = 1024
VECTOR_SEARCH_TOP_K = 5

# File Upload Constants
ALLOWED_FILE_EXTENSIONS: set[str] = {"pdf", "pptx", "docx"}
VOLUME_BASE_PATH = "/Volumes/{catalog}/{schema}/docs"

# Classification Constants
CLASSIFICATION_MAX_CHARS = 500

# Demo Company Mapping
DEMO_COMPANY_SECTORS: dict[str, str] = {
    "Apple Inc.": "Technology",
    "JPMorgan Chase & Co.": "Financial Services",
    "Pfizer Inc.": "Healthcare",
    "ExxonMobil Corporation": "Energy",
    "Amazon Inc.": "Consumer / E-Commerce",
}
