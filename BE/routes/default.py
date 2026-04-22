"""Default health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from BE.models.db import get_db
from BE.settings import get_settings

from BE.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["default"])


@router.get("/")
def root():
    """Root endpoint returning app name and version."""
    settings = get_settings()
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/health")
def health():
    """Liveness probe — always returns OK if the process is running."""
    return {"status": "healthy"}


@router.get("/ready")
def ready():
    """Readiness probe — checks database and Vector Search connectivity."""
    settings = get_settings()
    checks: dict[str, str] = {}

    # Check database connection using the shared engine
    try:
        from sqlalchemy import text
        from BE.models.db import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", str(exc))
        checks["database"] = "unavailable"

    # Check Vector Search availability (skip for local dev without Databricks)
    if settings.databricks_host and settings.databricks_token:
        try:
            from databricks.sdk import WorkspaceClient

            ws = WorkspaceClient(host=settings.databricks_host, token=settings.databricks_token)
            ws.vector_search_indexes.get_index(index_name=settings.vector_search_index)
            checks["vector_search"] = "connected"
        except Exception as exc:
            logger.warning("Vector Search readiness check failed: %s", str(exc))
            checks["vector_search"] = "unavailable"
    else:
        checks["vector_search"] = "skipped (local dev)"

    all_healthy = all(v in ("connected", "skipped (local dev)") for v in checks.values())
    if all_healthy:
        return {"status": "ready", "checks": checks}

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "not_ready", "checks": checks},
    )
