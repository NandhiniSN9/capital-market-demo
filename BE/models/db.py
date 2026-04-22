"""Sync database engine and session factory for Databricks SQL."""

import logging
import os
import time
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from BE.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_engine = None
_SessionLocal = None

# Token cache with expiry tracking
_token_cache = {"token": "", "expires_at": 0.0}
_TOKEN_REFRESH_BUFFER = 300  # refresh 5 min before expiry


def _get_token() -> str:
    """Get a valid token — PAT for local dev, OAuth with auto-refresh for Databricks Apps."""
    now = time.time()

    if settings.DATABRICKS_TOKEN:
        return settings.DATABRICKS_TOKEN

    if _token_cache["token"] and now < _token_cache["expires_at"] - _TOKEN_REFRESH_BUFFER:
        return _token_cache["token"]

    try:
        logger.info("[DB] Fetching OAuth token via SDK...")
        from databricks.sdk import WorkspaceClient
        wc = WorkspaceClient(
            host=settings.DATABRICKS_HOST,
            client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
            client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
        )
        token_obj = wc.config.oauth_token()
        token = token_obj.access_token if hasattr(token_obj, "access_token") else str(token_obj)

        expiry = getattr(token_obj, "expiry", None)
        if expiry and hasattr(expiry, "timestamp"):
            _token_cache["expires_at"] = expiry.timestamp()
        else:
            _token_cache["expires_at"] = now + 3600

        _token_cache["token"] = token
        logger.info("[DB] OAuth token refreshed, length=%d, expires_in=%.0fs",
                    len(token), _token_cache["expires_at"] - now)
        return token
    except Exception as e:
        logger.error("[DB] OAuth token fetch failed: %s", str(e))
        return _token_cache["token"] or ""


def _build_engine_url() -> str:
    if settings.database_url:
        return settings.database_url
    token = _get_token()
    host = settings.DATABRICKS_HOST.rstrip("/").replace("https://", "")
    return (
        f"databricks://token:{token}@{host}"
        f"?http_path={settings.DATABRICKS_SQL_HTTP_PATH}"
        f"&catalog={settings.DATABRICKS_CATALOG}"
        f"&schema={settings.DATABRICKS_SCHEMA}"
    )


def _token_needs_refresh() -> bool:
    if settings.DATABRICKS_TOKEN:
        return False
    return time.time() >= _token_cache["expires_at"] - _TOKEN_REFRESH_BUFFER


def get_engine():
    global _engine, _SessionLocal
    if _engine is not None and _token_needs_refresh():
        logger.info("[DB] Token expired, recreating engine...")
        old_engine = _engine
        _engine = None
        _SessionLocal = None
        # Dispose old engine in background to avoid blocking in-flight requests
        try:
            old_engine.dispose()
        except Exception:
            pass

    if _engine is None:
        logger.info("[DB] Creating SQLAlchemy engine...")
        _engine = create_engine(
            _build_engine_url(),
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=10,
            max_overflow=20,
            echo=settings.DEBUG,
        )
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
        logger.info("[DB] Engine created")
    return _engine


def get_db() -> Generator[Session, None, None]:
    get_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
